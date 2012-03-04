# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Copyright 2009 E. A. Graham Jr. <txcrackers@gmail.com>.
# Copyright 2010 B. Kroon <bart@tarmack.eu>.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#-------------------------------------------------------------------------------
from PyQt4.QtCore import SIGNAL, Qt, QModelIndex
from PyQt4.QtGui import QHeaderView, QSortFilterProxyModel, QAbstractProxyModel, QFontMetrics, QFont
from PyQt4 import uic
from time import time
import bisect

import auxilia
import PluginBase

DATA_DIR = ''

def getWidget(modelManager, view, mpdclient, config, library):
    return LibraryForm(modelManager, view, mpdclient, config, library)

class LibraryForm(PluginBase.PluginBase, auxilia.Actions):
    '''List and controls for the full "library" of music known to the server.
       Note that this does not actually manage the filesystem or tags or covers.
       There are many other programs that do that exceedingly well already.
    '''
    moduleName = '&Library'
    moduleIcon = 'server-database'

    def load(self):
        self.artistModel = self.modelManager.artists
        self.albumModel = self.modelManager.albums
        self.trackModel = self.modelManager.tracks
        # Load and place the Library form.
        if self.view.KDE:
            uic.loadUi(DATA_DIR+'ui/LibraryForm.ui', self)
        else:
            uic.loadUi(DATA_DIR+'ui/LibraryForm.ui.Qt', self)
        self.artistProxy = QSortFilterProxyModel()
        self.artistProxy.setSourceModel(self.artistModel)
        self.artistProxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.artistProxy.setDynamicSortFilter(True)
        self.artistView.setModel(self.artistProxy)

        self.albumHideProxy = HidingProxyModel(self.albumModel)
        self.albumProxy = QSortFilterProxyModel()
        self.albumProxy.setSourceModel(self.albumHideProxy)
        self.albumProxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.albumProxy.setDynamicSortFilter(True)
        self.albumView.setModel(self.albumProxy)

        self.trackHideProxy = HidingProxyModel(self.trackModel)
        self.trackProxy = QSortFilterProxyModel()
        self.trackProxy.setSourceModel(self.trackHideProxy)
        self.trackProxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.trackProxy.setDynamicSortFilter(True)
        self.trackProxy.setFilterKeyColumn(1)
        self.trackView.setModel(self.trackProxy)
        self.trackView.horizontalHeader().setResizeMode(1, QHeaderView.Stretch)
        self.trackView.verticalHeader().setDefaultSectionSize(QFontMetrics(QFont()).height())

        self.libSplitter_1.setSizes(self.config.libSplit1)
        self.libSplitter_2.setSizes(self.config.libSplit2)
        self.connect(self.libSplitter_1, SIGNAL('splitterMoved(int, int)'), self._storeSplitter)
        self.connect(self.libSplitter_2, SIGNAL('splitterMoved(int, int)'), self._storeSplitter)
        self.view.connect(self.view, SIGNAL('reloadLibrary'), self.reload)
        self.view.connect(self.view, SIGNAL('clearForms'), self.clear)

        # search and filter functions
        self.connect(self.artistView.selectionModel(),
                SIGNAL('selectionChanged(const QItemSelection &, const QItemSelection &)'),
                self.artistFilter)
        self.connect(self.albumView.selectionModel(),
                SIGNAL('selectionChanged(const QItemSelection &, const QItemSelection &)'),
                self.albumFilter)

        self.connect(self.artistSearchField, SIGNAL('textEdited(QString)'), self.artistProxy.setFilterFixedString)
        self.connect(self.albumSearchField, SIGNAL('textEdited(QString)'), self.albumProxy.setFilterFixedString)
        self.connect(self.trackSearchField, SIGNAL('textEdited(QString)'), self.trackProxy.setFilterFixedString)
        self.connect(self.showAllAlbums, SIGNAL('clicked()'), self.albumHideProxy.reset)
        self.connect(self.showAllTracks, SIGNAL('clicked()'), self.trackHideProxy.reset)

        # Double click actions.
        self.connect(self.artistView, SIGNAL('itemDoubleClicked(QListWidgetItem*)'), self.addArtist)
        self.connect(self.albumView, SIGNAL('itemDoubleClicked(QListWidgetItem*)'), self.addAlbum)
        self.connect(self.trackView, SIGNAL('itemDoubleClicked(QTreeWidgetItem*,int)'), self.addTrack)


        # Create context menu's.
        #=======================================================================

        # Create the actions for each window.
        self.artistPlayAdd = self.actionPlayAdd(self.artistView, self._addPlayArtist)
        self.artistPlayReplace = self.actionPlayReplace(self.artistView, self._clearPlayArtist)
        self.artistAdd = self.actionAddSongs(self.artistView, self.addArtist)

        self.albumPlayAdd = self.actionPlayAdd(self.albumView, self._addPlayAlbum)
        self.albumPlayReplace = self.actionPlayReplace(self.albumView, self._clearPlayAlbum)
        self.albumAdd = self.actionAddSongs(self.albumView, self.addAlbum)

        self.trackPlayAdd = self.actionPlayAdd(self.trackView, self._addPlayTrack)
        self.trackPlayReplace = self.actionPlayReplace(self.trackView, self._clearPlayTrack)
        self.trackAdd = self.actionAddSongs(self.trackView, self.addTrack)

        #=======================================================================

    def reload(self):
        if not self.config.server:
            return
        try:
            self.view.setCursor(Qt.WaitCursor)
            p = time()
            t = time()

            self.artistModel.reload(self.library.artists())
            print 'load Artist took %.3f seconds' % (time() - t); t = time()
            self.albumModel.reload(self.library.albums())
            print 'load Album took %.3f seconds' % (time() - t); t = time()
            self.trackModel.reload(self.library.songs())
            print 'load Tracks took %.3f seconds' % (time() - t); t = time()
            print 'library load took %.3f seconds' % (time() - p)
        finally:
            self.view.setCursor(Qt.ArrowCursor)

    def clear(self):
        self.artistModel.clear()
        self.albumModel.clear()
        self.trackModel.clear()
        self.albumHideProxy.reset()
        self.trackHideProxy.reset()

    def _selectedArtists(self):
        selection = self.artistView.selectedIndexes()
        return [self.artistProxy.mapToSource(index).internalPointer() for index in selection]

    def _selectedAlbums(self):
        selection = self.albumView.selectedIndexes()
        return [self.albumHideProxy.mapToSource(self.albumProxy.mapToSource(index)).internalPointer() for index in selection]

    def _selectedTracks(self):
        selection = (index for index in self.trackView.selectedIndexes() if index.column() == 0)
        return [self.trackHideProxy.mapToSource(self.trackProxy.mapToSource(index)).internalPointer() for index in selection]

    def artistFilter(self, selected, deselected):
        artists = self._selectedArtists()
        self.albumHideProxy.hideAll()
        self.trackHideProxy.hideAll()
        if len(artists) < 1:
            return
        for artist in artists:
            try:
                for album in artist.albums:
                    row = self.albumModel.findRow(album)
                    self.albumHideProxy.showRow(row)
                for song in artist.songs:
                    row = self.trackModel.findRow(song)
                    self.trackHideProxy.showRow(row)
            except Exception, e:
                print e

    def albumFilter(self, selected, deselected):
        albums = self._selectedAlbums()
        if len(albums) < 1:
            return
        self.trackHideProxy.hideAll()
        for album in albums:
            for song in album.songs:
                row = self.trackModel.findRow(song)
                self.trackHideProxy.showRow(row)

    def addArtist(self, play=False):
        '''Add all songs from the currently selected artist into the current playlist'''
        songs = (song for artist in self._selectedArtists() for song in artist.songs)
        return self._addSongSet(songs, play)

    def addAlbum(self, play=False):
        '''Add all songs from the currently selected album into the current playlist'''
        songs = (song for album in self._selectedAlbums() for song in album.songs)
        return self._addSongSet(songs, play)

    def addTrack(self, play=False):
        '''Add all selected songs into the current playlist'''
        songs = (song for song in self._selectedTracks())
        return self._addSongSet(songs, play)

    def _addSongSet(self, songs, play=False):
        if play:
            self.mpdclient.send('addid', (songs.next().file.absolute,), callback=
                    lambda song_id: self.mpdclient.send('playid', (song_id,)))
        try:
            self.mpdclient.send('command_list_ok_begin')
            for song in songs:
                self.mpdclient.send('addid', (song.file.absolute,))
        finally:
            return self.mpdclient.send('command_list_end')


    def _addPlayArtist(self):
        self.addArtist(play=True)

    def _clearPlayArtist(self):
        self.mpdclient.send('clear')
        self._addPlayArtist()

    def _addPlayAlbum(self):
        self.addAlbum(play=True)

    def _clearPlayAlbum(self):
        self.mpdclient.send('clear')
        self._addPlayAlbum()

    def _addPlayTrack(self):
        self.addTrack(play=True)

    def _clearPlayTrack(self):
        self.mpdclient.send('clear')
        self._addPlayTrack()

    def _storeSplitter(self):
        self.config.libSplit1 = self.libSplitter_1.sizes()
        self.config.libSplit2 = self.libSplitter_2.sizes()


class HidingProxyModel(QAbstractProxyModel):
    def __init__(self, sourceModel):
        QAbstractProxyModel.__init__(self)
        self.setSourceModel(sourceModel)
        self.connect(sourceModel, SIGNAL('modelReset()'), self.reset)
        self.shown = []

    def setSourceModel(self, sourceModel):
        self._sourceModel = sourceModel
        QAbstractProxyModel.setSourceModel(self, sourceModel)

    def sourceModel(self):
        return self._sourceModel

    def rowCount(self, parent):
        return len(self.shown)

    def columnCount(self, parent):
        return self._sourceModel.columnCount(parent)

    def index(self, row, column, parent):
        #parent = self.mapToSource(parent)
        row = self.mapRowToSource(row)
        index = self._sourceModel.index(row, column, parent)
        return self.mapFromSource(index)

    def reset(self):
        self.shown = range(self._sourceModel.rowCount(QModelIndex()))
        self.emit(SIGNAL('modelReset()'))

    def hideRow(self, row):
        index = self.mapFromSource(row)
        if index >= 0:
            self.beginRemoveRows(QModelIndex(), index, index)
            del self.shown[index]
            self.endRemoveRows()

    def showRow(self, row):
        index = bisect.bisect_left(self.shown, row)
        if len(self.shown) == index or self.shown[index] != row:
            self.beginInsertRows(QModelIndex(), index, index)
            self.shown.insert(index, row)
            self.endInsertRows()

    def hideAll(self):
        self.beginRemoveRows(QModelIndex(), 0, len(self.shown))
        self.shown = []
        self.endRemoveRows()

    def mapToSource(self, index):
        if index.isValid():
            row = self.mapRowToSource(index.row())
            index = self._sourceModel.createIndex(row, index.column(), index.internalPointer())
        return index

    def mapRowToSource(self, row):
        if not self.shown:
            row = -1
        else:
            row = self.shown[row]
        return row

    def mapFromSource(self, index):
        if index.isValid():
            row = self.mapRowFromSource(index.row())
            index = self.createIndex(row, index.column(), index.internalPointer())
        return index

    def mapRowFromSource(self, row):
        index = bisect.bisect_left(self.shown, row)
        if index < len(self.shown) and self.shown[index] == row:
            return index
        else:
            return -1

    def mimeData(self, indexes):
        indexes = [self.mapToSource(index) for index in indexes]
        return self._sourceModel.mimeData(indexes)




