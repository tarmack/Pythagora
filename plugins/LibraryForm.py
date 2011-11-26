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
from PyQt4.QtCore import SIGNAL, Qt
from PyQt4.QtGui import QHeaderView, QTreeWidgetItem, QListWidgetItem
from PyQt4 import uic
from time import time

import auxilia
import PluginBase
import mpdlibrary

DATA_DIR = ''

class LibraryForm(PluginBase.PluginBase, auxilia.Actions):
    '''List and controls for the full "library" of music known to the server.
       Note that this does not actually manage the filesystem or tags or covers.
       There are many other programs that do that exceedingly well already.
    '''
    moduleName = '&Library'
    moduleIcon = 'server-database'

    def load(self):
        # Load and place the Library form.
        if self.view.KDE:
            uic.loadUi(DATA_DIR+'ui/LibraryForm.ui', self)
        else:
            uic.loadUi(DATA_DIR+'ui/LibraryForm.ui.Qt', self)
        self.trackView.header().setResizeMode(1, QHeaderView.Stretch)

        self.libSplitter_1.setSizes(self.config.libSplit1)
        self.libSplitter_2.setSizes(self.config.libSplit2)
        self.connect(self.libSplitter_1, SIGNAL('splitterMoved(int, int)'), self.__storeSplitter)
        self.connect(self.libSplitter_2, SIGNAL('splitterMoved(int, int)'), self.__storeSplitter)
        self.view.connect(self.view,SIGNAL('reloadLibrary'),self.reload)
        self.view.connect(self.view,SIGNAL('clearForms'),self.clear)

        # search and filter functions
        self.connect(self.artistView,SIGNAL('itemSelectionChanged()'),self.artistFilter)
        self.connect(self.albumView,SIGNAL('itemSelectionChanged()'),self.albumFilter)

        self.connect(self.artistSearchField,SIGNAL('textEdited(QString)'),self.artistSearch)
        self.connect(self.albumSearchField,SIGNAL('textEdited(QString)'),self.albumSearch)
        self.connect(self.trackSearchField,SIGNAL('textEdited(QString)'),self.trackSearch)

        # Double click actions.
        self.connect(self.artistView,SIGNAL('itemDoubleClicked(QListWidgetItem*)'),self.addArtist)
        self.connect(self.albumView,SIGNAL('itemDoubleClicked(QListWidgetItem*)'),self.addAlbum)
        self.connect(self.trackView,SIGNAL('itemDoubleClicked(QTreeWidgetItem*,int)'),self.addTrack)


        # Create context menu's.
        #=======================================================================

        # Create the actions for each window.
        self.artistPlayAdd = self.actionPlayAdd(self.artistView, self.__addPlayArtist)
        self.artistPlayReplace = self.actionPlayReplace(self.artistView, self.__clearPlayArtist)
        self.artistAdd = self.actionAddSongs(self.artistView, self.addArtist)

        self.albumPlayAdd = self.actionPlayAdd(self.albumView, self.__addPlayAlbum)
        self.albumPlayReplace = self.actionPlayReplace(self.albumView, self.__clearPlayAlbum)
        self.albumAdd = self.actionAddSongs(self.albumView, self.addAlbum)

        self.trackPlayAdd = self.actionPlayAdd(self.trackView, self.__addPlayTrack)
        self.trackPlayReplace = self.actionPlayReplace(self.trackView, self.__clearPlayTrack)
        self.trackAdd = self.actionAddSongs(self.trackView, self.addTrack)

        #=======================================================================

    def reload(self):
        if not self.config.server:
            return
        try:
            # Emit signal to also reload playlists from server.
            self.view.setCursor(Qt.WaitCursor)
            p = time()
            t = time()

            self.__loadArtistView(self.library.artists())
            print 'load Artist took %.3f seconds' % (time() - t); t = time()
            self.__loadAlbumView(self.library.albums())
            print 'load Album took %.3f seconds' % (time() - t); t = time()
            self.__loadTracksView(self.library.songs())
            print 'load Tracks took %.3f seconds' % (time() - t); t = time()
            print 'library load took %.3f seconds' % (time() - p)
        finally:
            self.view.setCursor(Qt.ArrowCursor)

    def clear(self):
        self.artistView.clear()
        self.albumView.clear()
        self.trackView.clear()

    def __loadArtistView(self, artists):
        self.artistView.clear()
        self.artistView.setUpdatesEnabled(False)
        #artists.sort(auxilia.cmpUnicode)
        for artist in artists:
            self.artistView.addItem(ArtistWidget(artist))
        self.artistView.insertItem(0, ArtistWidget('--all--'))
        self.artistSearch(self.artistSearchField.text())
        self.artistView.setUpdatesEnabled(True)

    def __loadAlbumView(self, albumlist):
        '''Reloads the list with the list presented'''
        self.albumView.clear()
        self.albumView.setUpdatesEnabled(False)
        #albumlist.sort(cmp=auxilia.cmpUnicode)
        for album in albumlist:
            albumWidget = AlbumWidget(album)
            self.albumView.addItem(albumWidget)
        self.albumView.insertItem(0, AlbumWidget('--all--'))
        self.albumSearch(self.albumSearchField.text())
        self.albumView.setUpdatesEnabled(True)

    def __loadTracksView(self, tracks):
        self.trackView.clear()
        self.trackView.setUpdatesEnabled(False)
        for track in tracks:
            trackWidget = TrackWidget(track)
            self.trackView.addTopLevelItem(trackWidget)
        if self.trackSearchField.text() != '':
            self.trackSearch(self.trackSearchField.text())
        self.trackView.setUpdatesEnabled(True)


    def artistFilter(self):
        songlist = []
        albumlist = []
        artists = [item.artist for item in self.artistView.selectedItems()]
        if len(artists) < 1:
            self.__loadAlbumView(self.library.albums())
            self.__loadTracksView(self.library.songs())
            return
        for artist in artists:
            if artist == '--all--':
                if '--all--' in (x.text() for x in self.albumView.selectedItems()):
                    self.__loadTracksView(self.library.songs())
                self.__loadAlbumView(self.library.albums())
                return
            songlist.extend(artist.songs)
            albumlist.extend(artist.albums)
        self.__loadAlbumView(albumlist)
        self.__loadTracksView(songlist)

    def albumFilter(self):
        songlist = []
        albums = [item.album for item in self.albumView.selectedItems()]
        artists = [item.artist for item in self.artistView.selectedItems()]
        if len(albums) < 1:
            if artists:
                self.artistFilter()
            else:
                self.__loadTracksView(self.library.songs())
            return
        for album in albums:
            if album == '--all--':
                self.artistFilter()
                return
            if album.lower() == 'greatest hits' and artists: # If album is a greatest hits assume only one artist is on there.
                songlist.extend(self.library.albumSongs(album, artists))
            else:
                songlist.extend(self.library.albumSongs(album))
        self.__loadTracksView(songlist)

    def artistSearch(self, key):
        self.__search(key, self.artistView)

    def albumSearch(self, key):
        self.__search(key, self.albumView)

    def trackSearch(self, key):
        hits = self.trackView.findItems(str(key), (Qt.MatchContains|Qt.MatchWrap), 1)[:]
        for x in xrange(self.trackView.topLevelItemCount()):
            self.trackView.topLevelItem(x).setHidden(True)
        for hit in hits:
            hit.setHidden(False)

    def __search(self, key, widget):
        hits = widget.findItems(str(key), (Qt.MatchContains|Qt.MatchWrap))[:]
        for x in xrange(widget.count()):
            widget.item(x).setHidden(True)
        for hit in hits:
            hit.setHidden(False)

    def addArtist(self):
        '''Add all songs from the currently selected artist into the current playlist'''
        return self.__addSongSet('artist', self.artistView.selectedItems())

    def addAlbum(self):
        '''Add all songs from the currently selected album into the current playlist'''
        return self.__addSongSet('album', self.albumView.selectedItems())

    def __addSongSet(self, key, selection):
        first = None
        for item in selection:
            for song in self.mpdclient.find(key,unicode(item.text())):
                self.mpdclient.send('add', (song['file'],))
                if not first:
                    first = self.mpdclient.playlistid()[-1]['id']
        self.view.emit(SIGNAL('playlistChanged()'))
        return first

    def addTrack(self):
        '''Add all selected songs into the current playlist'''
        first = None
        for item in self.trackView.selectedItems():
            self.mpdclient.send('add', (item.song['file'],))
            if not first:
                first = self.mpdclient.playlistid()[-1]['id']
        self.view.emit(SIGNAL('playlistChanged()'))
        return first


    def __addPlayArtist(self):
        try:
            self.mpdclient.send('playid', (self.addArtist(),))
        except:
            pass

    def __clearPlayArtist(self):
        self.mpdclient.send('clear')
        self.__addPlayArtist()

    def __addPlayAlbum(self):
        try:
            self.mpdclient.send('playid', (self.addAlbum(),))
        except:
            pass

    def __clearPlayAlbum(self):
        self.mpdclient.send('clear')
        self.__addPlayAlbum()


    def __addPlayTrack(self):
        try:
            self.mpdclient.send('playid', (self.addTrack(),))
        except:
            pass

    def __clearPlayTrack(self):
        self.mpdclient.send('clear')
        self.__addPlayTrack()

    def __storeSplitter(self):
        self.config.libSplit1 = self.libSplitter_1.sizes()
        self.config.libSplit2 = self.libSplitter_2.sizes()


# Widget subclasses.
class ArtistWidget(QListWidgetItem):
    '''Simple widget for artists in library view.'''
    def __init__(self, artist):
        self.artist = artist
        QListWidgetItem.__init__(self)
        self.setText(artist)

    def data(self, role):
        if role == Qt.DisplayRole:
            return unicode(self.artist)
        return QListWidgetItem.data(self, role)

    def getDrag(self):
        return self.artist.songs

class AlbumWidget(QListWidgetItem):
    '''Simple for album in library view.'''
    def __init__(self, album):
        self.album = album
        QListWidgetItem.__init__(self)

    def data(self, role):
        if role == Qt.ToolTipRole:
            print "debug: Type of data in AlbumWidget is", type(self.album)
            if isinstance(self.album, mpdlibrary.Album):
                s = '\n'.join(self.album.artists)
            else:
                s = ''
            print "debug: ToolTip:", s
            return s
        if role == Qt.DisplayRole:
            return unicode(self.album)
        return QListWidgetItem.data(self, role)

    def getDrag(self):
        return self.album.songs

class TrackWidget(QTreeWidgetItem):
    '''Track widget used in library track view.'''
    def __init__(self, song):
        QTreeWidgetItem.__init__(self, [])
        #QTreeWidgetItem.__init__(self, [song.track, song.title, song.time.human])
        self.song = song

    def data(self, column, role):
        if role == Qt.ToolTipRole:
            text = "Artist:\t %s\nAlbum:\t %s\nFile:\t %s"\
                    % (self.song.artist, self.song.album, self.song.file)
            return text
        if role == Qt.DisplayRole:
            if column == 0:
                return unicode(self.song.track)
            if column == 1:
                return unicode(self.song.title)
            if column == 2:
                return self.song.time.human
        return QTreeWidgetItem.data(self, column, role)

    def getDrag(self):
        return [self.song]


def getWidget(view, mpdclient, config, library):
    return LibraryForm(view, mpdclient, config, library)
