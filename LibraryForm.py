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
from PyQt4.QtGui import QHeaderView, QWidget
from PyQt4 import uic
from time import time
import os

import songwidgets
import auxilia
import mpdlibrary

class LibraryForm(auxilia.Actions, QWidget):
    '''List and controls for the full "library" of music known to the server.
       Note that this does not actually manage the filesystem or tags or covers.
       There are many other programs that do that exceedingly well already.
    '''
    def __init__(self, view, app, mpdclient, config):
        QWidget.__init__(self)
        self.app = app
        self.view = view
        self.mpdclient = mpdclient
        self.config = config
        # Load and place the Library form.
        if self.view.KDE:
            uic.loadUi('ui/LibraryForm.ui', self)
        else:
            uic.loadUi('ui/LibraryForm.ui.Qt', self)
        self.trackView.header().setResizeMode(1, QHeaderView.Stretch)
        self.view.tabs.addTab(self, auxilia.PIcon('server-database'), '&Library')
        # Load and place the FileSystem form.
        if self.view.KDE:
            uic.loadUi('ui/FileSystemForm.ui', self)
        else:
            uic.loadUi('ui/FileSystemForm.ui.Qt', self)
        self.view.tabs.addTab(self.filesystemTree, auxilia.PIcon('folder-sound'), 'F&ileSystem')

        self.libSplitter_1.setSizes(config.libSplit1)
        self.libSplitter_2.setSizes(config.libSplit2)
        self.connect(self.libSplitter_1, SIGNAL('splitterMoved(int, int)'), self.__storeSplitter)
        self.connect(self.libSplitter_2, SIGNAL('splitterMoved(int, int)'), self.__storeSplitter)
        self.view.connect(self.view,SIGNAL('reloadLibrary'),self.reload)

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

        self.connect(self.filesystemTree, SIGNAL('itemExpanded(QTreeWidgetItem*)'), lambda item: item.setExpanded())

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

    def reload(self, mainlist):
        if not self.config.server:
            return
        try:
            # Emit signal to also reload playlists from server.
            self.view.setCursor(Qt.WaitCursor)
            p = time()
            t = time()
            self.library = mpdlibrary.Library(mainlist)

            print 'library parsing took %.3f seconds' % (time() - t); t = time()
            self.__loadArtistView(self.library.artists())
            print 'load Artist took %.3f seconds' % (time() - t); t = time()
            self.__loadAlbumView(self.library.albums())
            print 'load Album took %.3f seconds' % (time() - t); t = time()
            self.__loadTracksView(self.library.songs())
            print 'load Tracks took %.3f seconds' % (time() - t); t = time()
            self.__loadFileSystemView('/')
            print 'load FS took %.3f seconds' % (time() - t)
            print 'library load took %.3f seconds' % (time() - p)
        finally:
            self.view.setCursor(Qt.ArrowCursor)

    def __loadArtistView(self, artists):
        self.artistView.clear()
        self.artistView.setUpdatesEnabled(False)
        artists.sort(auxilia.cmpUnicode)
        for artist in artists:
            self.artistView.addItem(songwidgets.ArtistWidget(artist, self.library))
        self.artistView.insertItem(0, '--all--')
        self.artistSearch(self.artistSearchField.text())
        self.artistView.setUpdatesEnabled(True)

    def __loadAlbumView(self, albumlist):
        '''Reloads the list with the list presented'''
        self.albumView.clear()
        self.albumView.setUpdatesEnabled(False)
        albumlist.sort(cmp=auxilia.cmpUnicode)
        for album in albumlist:
            artists = self.library.albumArtists(album)
            albumWidget = songwidgets.AlbumWidget(album, artists, self.library)
            self.albumView.addItem(albumWidget)
        self.albumView.insertItem(0, '--all--')
        self.albumSearch(self.albumSearchField.text())
        self.albumView.setUpdatesEnabled(True)

    def __loadTracksView(self, tracks):
        self.trackView.clear()
        self.trackView.setUpdatesEnabled(False)
        for track in tracks:
            trackWidget = songwidgets.TrackWidget(track)
            self.trackView.addTopLevelItem(trackWidget)
        if self.trackSearchField.text() != '':
            self.trackSearch(self.trackSearchField.text())
        self.trackView.setUpdatesEnabled(True)

    def __loadFileSystemView(self, path):
        parent = self.filesystemTree.invisibleRootItem()
        self.filesystemTree.setUpdatesEnabled(False)
        self.filesystemTree.clear()
        filelist = self.library.ls(path)
        for name in filelist:
            nextPath = os.path.join(path, name)
            attr = self.library.attributes(nextPath)
            item = songwidgets.FilesystemWidget(name, attr, self.library)
            parent.addChild(item)
        parent.sortChildren(0, 0)
        self.filesystemTree.setUpdatesEnabled(True)


    def artistFilter(self):
        songlist = []
        albumlist = []
        artists = self.artistView.selectedItems()
        if len(artists) < 1:
            self.__loadAlbumView(self.library.albums())
            self.__loadTracksView(self.songs())
            return
        for artist in artists:
            artist = unicode(artist.text())
            if artist == '--all--':
                if '--all--' in (unicode(x.text()) for x in self.albumView.selectedItems()):
                    self.__loadTracksView(self.library.songs())
                self.__loadAlbumView(self.library.albums())
                return
            songlist.extend(self.library.artistSongs(artist))
            albumlist.extend(self.library.artistAlbums(artist))
        self.__loadAlbumView(albumlist)
        self.__loadTracksView(songlist)

    def albumFilter(self):
        songlist = []
        albums = self.albumView.selectedItems()
        artists = [unicode(artist.text()) for artist in self.artistView.selectedItems()]
        if len(albums) < 1:
            if artists:
                self.artistFilter()
            else:
                self.__loadTracksView(self.library.songs())
            return
        for album in albums:
            album = unicode(album.text())
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

    def rescan(self):
        '''rescan the library'''
        self.mpdclient.send('rescan')

    def update(self):
        '''update the library'''
        self.mpdclient.send('update')

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



