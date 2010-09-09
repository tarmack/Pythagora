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
import operator

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
        self.view.connect(self.view,SIGNAL('reloadLibrary()'),self.reload)

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
        if not self.config.server or not self.mpdclient.connected():
            return
        try:
            # Emit signal to also reload playlists from server.
            self.view.emit(SIGNAL('reloadPlaylists()'))
            self.view.setCursor(Qt.WaitCursor)
            p = time()
            t = time()
            self.mainSongList = []
            self.artistdict = {}
            self.albumdict = {}
            self.albumlist = {}
            filesystemlist = {}
            # parse the list and prepare it for loading in the library browser and the file system view.
            self.mpdclient.iterate = True
            mainlist = self.mpdclient.listallinfo()
            #print 'library download took %.3f seconds' % (time() - p); t = time()
            for song in (x for x in mainlist if 'file' in x):
                self.mainSongList.append(song)
                album = song.get('album','?')
                artist = auxilia.songArtist(song)
                appendToList(self.artistdict, artist, song)
                appendToList(self.albumdict, album, song)
                appendToList(self.albumlist, album, artist, True)

                # Build the file system tree.
                fslist = filesystemlist
                for part in song['file'].split('/'):
                    fslist[part] = fslist.get(part, {})
                    fslist = fslist[part]

            print 'library parsing took %.3f seconds' % (time() - t); t = time()
            self.__loadArtistView()
            print 'load Artist took %.3f seconds' % (time() - t); t = time()
            self.__loadAlbumView(self.albumlist)
            print 'load Album took %.3f seconds' % (time() - t); t = time()
            self.__loadTracksView(self.mainSongList)
            print 'load Tracks took %.3f seconds' % (time() - t); t = time()
            self.__loadFileSystemView(filesystemlist)
            print 'load FS took %.3f seconds' % (time() - t)
            print 'library load took %.3f seconds' % (time() - p)
        finally:
            self.mpdclient.iterate = False
            self.view.emit(SIGNAL('update'), ['player'])
            self.view.setCursor(Qt.ArrowCursor)

    def __loadArtistView(self):
        self.artistView.clear()
        self.artistView.setUpdatesEnabled(False)
        artists = self.artistdict.keys()
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
        for (album, artists) in sorted(albumlist.iteritems(), auxilia.cmpUnicode, operator.itemgetter(0)):
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

    def __loadFileSystemView(self, filelist, parent=None):
        update = True
        if not parent:
            self.filesystemTree.clear()
            parent = self.filesystemTree.invisibleRootItem()
            update = False
            self.filesystemTree.setUpdatesEnabled(False)
        for name in filelist.keys():
            item = songwidgets.FilesystemWidget(name)
            parent.addChild(item)
            self.__loadFileSystemView(filelist[name], item)
        parent.sortChildren(0, 0)
        if not update:
            self.filesystemTree.setUpdatesEnabled(True)


    def artistFilter(self):
        songlist = []
        albumlist = {}
        artists = self.artistView.selectedItems()
        if len(artists) < 1:
            self.__loadAlbumView(self.albumlist)
            self.__loadTracksView(self.mainSongList)
            return
        for artist in artists:
            artist = unicode(artist.text())
            if artist == '--all--':
                if '--all--' in (unicode(x.text()) for x in self.albumView.selectedItems()):
                    self.__loadTracksView(self.mainSongList)
                self.__loadAlbumView(self.albumlist)
                return
            artistsongs = self.artistdict[artist]
            songlist.extend(artistsongs)
            for song in artistsongs:
                #tup = (song.get('album', '?'), auxilia.songArtist(song))
                #if not tup in albumlist:
                #    albumlist.insert(0, tup)
                album = song.get('album', '?')
                if not artist in albumlist.get(album, []):
                    albumlist[album] = albumlist.get(album, [])+[artist]
        self.__loadAlbumView(albumlist)
        self.__loadTracksView(songlist)

    def albumFilter(self):
        songlist = []
        albums = self.albumView.selectedItems()
        artists = [unicode(artist.text()) for artist in self.artistView.selectedItems()]
        if len(albums) < 1:
            self.__loadTracksView(self.mainSongList)
            return
        for album in albums:
            album = unicode(album.text())
            if album == '--all--':
                self.artistFilter()
                return
            if album.lower() == 'greatest hits' and artists: # If album is a greatest hits assume only one artist is on there.
                songlist.extend([song for song in self.albumdict[album] if auxilia.songArtist(song) in artists])
            else:
                songlist.extend(self.albumdict[album])
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
        self.__scan(self.mpdclient.rescan())

    def update(self):
        '''update the library'''
        self.__scan(self.mpdclient.update())

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
                self.mpdclient.add(song['file'])
                if not first:
                    first = self.mpdclient.playlistid()[-1]['id']
        self.view.emit(SIGNAL('playlistChanged()'))
        return first

    def addTrack(self):
        '''Add all selected songs into the current playlist'''
        first = None
        for item in self.trackView.selectedItems():
            self.mpdclient.add(item.song['file'])
            if not first:
                first = self.mpdclient.playlistid()[-1]['id']
        self.view.emit(SIGNAL('playlistChanged()'))
        return first


    def __addPlayArtist(self):
        try:
            self.mpdclient.playid(self.addArtist())
        except:
            pass

    def __clearPlayArtist(self):
        self.mpdclient.clear()
        self.__addPlayArtist()

    def __addPlayAlbum(self):
        try:
            self.mpdclient.playid(self.addAlbum())
        except:
            pass

    def __clearPlayAlbum(self):
        self.mpdclient.clear()
        self.__addPlayAlbum()


    def __addPlayTrack(self):
        try:
            self.mpdclient.playid(self.addTrack())
        except:
            pass

    def __clearPlayTrack(self):
        self.mpdclient.clear()
        self.__addPlayTrack()


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


