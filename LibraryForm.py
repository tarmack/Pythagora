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
            self.library = Library(mainlist)

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
            self.artistView.addItem(songwidgets.ArtistWidget(artist))
        self.artistView.insertItem(0, '--all--')
        self.artistSearch(self.artistSearchField.text())
        self.artistView.setUpdatesEnabled(True)

    def __loadAlbumView(self, albumlist):
        '''Reloads the list with the list presented'''
        self.albumView.clear()
        self.albumView.setUpdatesEnabled(False)
        albumlist.sort(cmp=auxilia.cmpUnicode)
        for album in albumlist:
            artists = self.library.artistsOnAlbum(album)
            albumWidget = songwidgets.AlbumWidget(album, artists)
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

    def __loadFileSystemView(self, path, parent=None):
        update = True
        if not parent:
            parent = self.filesystemTree.invisibleRootItem()
            self.filesystemTree.setUpdatesEnabled(False)
            update = False
            self.filesystemTree.clear()
        filelist = self.library.ls(path)
        for name in filelist:
            nextPath = os.path.join(path, name)
            attr = self.library.attributes(nextPath)
            item = songwidgets.FilesystemWidget(name, attr)
            parent.addChild(item)
            if attr == 'directory':
                self.__loadFileSystemView(nextPath, item)
        parent.sortChildren(0, 0)
        if not update:
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


def appendToList(listDict, keys, value, deduplicate=False):
    '''In place add value to listDict at key.
    If any of them are lists the values in those lists are used as value and
    key. Everything gets added to everything. The optional deduplicate makes
    appendToList only add values that are not yet in the list.
    '''
    if type(value) != list:
        value = [value]
    if type(keys) != list:
        keys = [keys]
    for key in keys:
        part = listDict.get(key, [])
        if deduplicate:
            # filter all that are already in there.
            value = [x for x in value if x not in part]
        listDict[key] = part + value


class Library:
    '''Supplies a storage model for the mpd database.'''
    def __init__(self, mainlist):
        self._songList = []
        self._artists = {}
        self._albums = {}
        self._filesystem = {}
        # parse the list and prepare it for loading in the library browser and the file system view.
        for song in (x for x in mainlist if 'file' in x):
            self._songList.append(song)
            album = auxilia.songAlbum(song, 'None')
            artist = auxilia.songArtist(song, 'Unknown')
            appendToList(self._artists, artist, song)
            appendToList(self._albums, album, song)

            # Build the file system tree.
            fslist = self._filesystem
            path = song['file'].split('/')
            while path:
                part = path.pop(0)
                if path == []:
                    fslist[part] = song
                else:
                    fslist[part] = fslist.get(part, {})
                    fslist = fslist[part]

    def artists(self):
        '''Returns a list containing all artists in the library.'''
        return self._artists.keys()

    def albums(self):
        '''Returns a list containing all albums in the library.'''
        return self._albums.keys()

    def songs(self):
        '''Returns a list containing all songs in the library.'''
        return self._songList[:]

    def artistSongs(self, artist):
        '''Returns a list containing all songs from the supplied artist.'''
        return self._artists.get(artist, [])

    def artistAlbums(self, artist):
        '''Returns a list containing all albums the artist is listed on.'''
        albumlist = set()
        for song in self.artistSongs(artist):
            album = auxilia.songAlbum(song, '')
            albumlist.add(album)
        return list(albumlist)

    def albumSongs(self, album, artists=[]):
        '''Returns a list containing all songs on the supplied album title.
        The optional artist argument can be used to only get the songs of a particular artist or list of artists.'''
        if type(artists) is str:
            artists = [artists]
        songlist = self._albums.get(album, [])
        if artists:
            songlist = [song for song in songlist if auxilia.songArtist(song, '') in artists]
        return songlist

    def artistsOnAlbum(self, album):
        '''Returns a list containing all artists listed on the album.'''
        songlist = self.albumSongs(album)
        artistlist = set()
        for song in songlist:
            artistlist.add(auxilia.songArtist(song))
        return list(artistlist)

    def ls(self, path, fslist=None):
        '''Returns a list of songs and directories contained in the given path.'''
        if path.startswith('/'):
            path = path[1:]
        if fslist is None:
            fslist = self._filesystem
        if not path:
            return fslist.keys()
        part, sep, path = path.partition('/')
        if part == '':
            return fslist.keys()
        fslist = fslist.get(part, {})
        return self.ls(path, fslist)

    def attributes(self, path):
        '''Returns whether path is a directory or a song file.'''
        if path.startswith('/'):
            path = path[1:]
        fslist = self._filesystem
        for part in path.split('/'):
            if part:
                fslist = fslist[part]
        if fslist.get('file', None) == path:
            return 'file'
        else:
            return 'directory'
