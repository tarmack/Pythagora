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
from PyQt4.QtCore import SIGNAL, Qt, QModelIndex, QMimeData
from PyQt4.QtGui import QMessageBox, QKeySequence, QListView, QTableView, QFontMetrics, QFont
from PyQt4 import uic

import mpd
import auxilia
import PluginBase

DATA_DIR = ''

def getWidget(modelManager, view, mpdclient, config, library):
    return PlaylistForm(modelManager, view, mpdclient, config, library)

class PlaylistForm(PluginBase.PluginBase, auxilia.Actions):
    '''Display and manage the currently known playlists.'''
    moduleName = '&PlayLists'
    moduleIcon = 'document-multiple'

    def load(self):
        self.playlistModel = self.modelManager.playlists
        # Load and place the stored playlists form.
        if self.view.KDE:
            uic.loadUi(DATA_DIR+'ui/PlaylistsForm.ui', self)
        else:
            uic.loadUi(DATA_DIR+'ui/PlaylistsForm.ui.Qt', self)
        self.playlistSplitter.setSizes(self.config.playlistSplit)

        # Playlist list
        self.playlistList.setModel(self.playlistModel)
        self.playlistList.keyPressEvent = self._listKeyPressEvent
        self.connect(self.playlistList.selectionModel(),
                SIGNAL('currentChanged(const QModelIndex &, const QModelIndex &)'),
                self.songList.setRootIndex)
        self.connect(self.playlistList, SIGNAL('itemDoubleClicked(QListWidgetItem*)'), self._addList)
        # Create actions.
        self.playlistListPlayAdd = self.actionPlayAdd(self.playlistList, self._addPlayList)
        self.playlistListPlayReplace = self.actionPlayReplace(self.playlistList, self._loadPlayList)
        self.playlistListAdd = self.actionAddSongs(self.playlistList, self._addList)
        self.playlistListReplace = self.actionLoad(self.playlistList, self._loadList)
        self.playlistListRemove = self.actionRemove(self.playlistList, self._deleteList)

        # Song list
        self.songList.setModel(self.playlistModel)
        self.songList.setColumnHidden(0, True)
        self.songList.horizontalHeader().setResizeMode(3) # QHeaderView::ResizeToContents
        self.songList.verticalHeader().setDefaultSectionSize(QFontMetrics(QFont()).height())
        self.songList.keyPressEvent = self._songKeyPressEvent
        # Create actions.
        self.songListPlayAdd = self.actionPlayAdd(self.songList, self._addPlaySongs)
        self.songListPlayReplace = self.actionPlayReplace(self.songList, self._clearPlaySong)
        self.songListAdd = self.actionAddSongs(self.songList, self._addSongs)
        self.songListRemove = self.actionRemove(self.songList, self._removeSongs)

        # overload new button dropEvent()
        self.newButton.dragEnterEvent = self._newListDragEnterEvent
        self.newButton.dropEvent = self._newListDropEvent

        # Connect to the buttons.
        self.connect(self.newButton, SIGNAL('clicked()'), self._newList)
        self.connect(self.loadButton, SIGNAL('clicked()'), self._loadList)
        self.connect(self.deleteButton, SIGNAL('clicked()'), self._deleteList)
        self.connect(self.playlistSplitter, SIGNAL('splitterMoved(int, int)'), self._storeSplitter)


    def _listKeyPressEvent(self, event):
        if event.matches(QKeySequence.Delete):
            self._deleteList()
        elif event.key() == Qt.Key_Escape:
            self.playlistList.setCurrentIndex(QModelIndex())
        else:
            QListView.keyPressEvent(self.playlistList, event)

    def _songKeyPressEvent(self, event):
        if event.matches(QKeySequence.Delete):
            self._removeSongs()
        elif event.key() == Qt.Key_Escape:
            self.songList.setCurrentIndex(QModelIndex())
        else:
            QTableView.keyPressEvent(self.songList, event)

    def _newListDragEnterEvent(self, event):
        if event.provides('mpd/uri'):
            event.accept()

    def _newListDropEvent(self, event):
        if event.provides('mpd/uri'):
            event.accept()
            parent = self._newList()
            data = QMimeData()
            data.setData('mpd/uri', event.mimeData().data('mpd/uri'))

            def disconnect(item, row=-1, column=-1):
                if parent.row() == row:
                    self.disconnect(self.playlistList.itemDelegate(parent),
                            SIGNAL('commitData(QWidget *)'),
                            addSongs)
                    self.disconnect(self.playlistModel,
                            SIGNAL('rowsAboutToBeRemoved(const QModelIndex &, int , int)'),
                            disconnect)

            def addSongs(editor, data=data):
                # Make sure to disconnect from the signals.
                if parent.data(Qt.DisplayRole):
                    disconnect(None, parent.row())
                    self.playlistModel.dropMimeData(data, Qt.CopyAction, 0, 0, parent)

            self.connect(self.playlistList.itemDelegate(parent),
                    SIGNAL('commitData(QWidget *)'),
                    addSongs)
            self.connect(self.playlistModel,
                    SIGNAL('rowsAboutToBeRemoved(const QModelIndex &, int , int)'),
                    disconnect)

    def _getSelectedPlaylists(self):
        return (self.playlistModel.data(index, Qt.DisplayRole) for index in self.playlistList.selectedIndexes())

    def _getSelectedSongs(self):
        return (index.internalPointer() for index in self.songList.selectedIndexes() if index.column() == 1)

    def _newList(self):
        ''' Insert a new row in the list of playlists and open the editor on it. '''
        self.playlistModel.insertRow(0, QModelIndex())
        index = self.playlistModel.index(0, 0, QModelIndex())
        self.playlistList.setCurrentIndex(index)
        self.playlistList.edit(index)
        return index

    def _deleteList(self):
        '''Delete the currently selected playlist.'''
        for name in self._getSelectedPlaylists():
            resp = QMessageBox.question(self,
                    'Delete Playlist',
                    'Are you sure you want to delete '+name,
                    QMessageBox.Yes|QMessageBox.No,
                    QMessageBox.No)
            if resp == QMessageBox.Yes:
                try:
                    self.mpdclient.send('rm', (name,))
                except mpd.CommandError:
                    pass
        self.playlistList.setCurrentIndex(QModelIndex())

    def _removeSongs(self):
        self.mpdclient.send('command_list_ok_begin')
        try:
            for index in sorted(self.songList.selectionModel().selectedIndexes(), key=lambda i:i.row(), reverse=True):
                if index.column() == 1:
                    song = index.internalPointer()
                    self.mpdclient.send('playlistdelete', (song.playlist, index.row()))
        finally:
            self.mpdclient.send('command_list_end')

    def _loadPlayList(self):
        self._loadList()
        self.mpdclient.send('play')

    def _addPlayList(self):
        last = int(self.mpdclient.status()['playlistlength'])
        self._addList()
        self.mpdclient.send('play', (last,))

    def _loadList(self):
        '''Load the currently selected playlist onto the server.
           Note: this operation clears the current playlist.
        '''
        self.mpdclient.send('clear')
        self._addList()

    def _addList(self, state=None):
        '''Load the currently selected playlist onto the server.
        '''
        if not state:
            state = self.mpdclient.status()['state']
        try:
            for name in self._getSelectedPlaylists():
                self.mpdclient.send('load', (name,))
        except:
            return
        if state == 'play':
            self.mpdclient.send('play')

    def _addSongs(self):
        self.mpdclient.send('command_list_ok_begin')
        try:
            for song in self._getSelectedSongs():
                self.mpdclient.send('add', (song.file.absolute,))
        finally:
            self.mpdclient.send('command_list_end')

    def _addPlaySongs(self):
        last = len(self.modelManager.playQueue)
        self._addSongs()
        self.mpdclient.send('play', (last,))

    def _clearPlaySong(self):
        self.mpdclient.send('clear')
        self._addPlaySongs()

    def _storeSplitter(self):
        self.config.playlistSplit = self.playlistSplitter.sizes()

