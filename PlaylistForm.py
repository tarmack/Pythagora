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
from PyQt4.QtGui import QMessageBox, QInputDialog, QKeySequence, QListWidget, QTreeWidget

import mpd
import songwidgets
import auxilia

# TODO: Ask user if he wants to save the new/temp list if he selects another list.
# TODO: PlaylistList context menu. add actions:
#        * append to displayed playlist
# TODO: Double click actions. playlistlist add to current.

#==============================================================================
# Display and manage the currently known playlists.
#==============================================================================
class PlaylistForm(auxilia.DragNDrop, auxilia.Actions):
    '''Display and manage the currently known playlists.'''
    def __init__(self, view, app, mpdclient):
        self.app = app
        self.view = view
        self.mpdclient = mpdclient
        self.currentPlaylist = None
        self.view.connect(self.view,SIGNAL('reloadPlaylists()'),self.reload)

        # top bit
        view.connect(view.playlistList,SIGNAL('itemClicked(QListWidgetItem*)'),self.selectPlaylist)
        view.connect(view.newButton,SIGNAL('clicked()'),self.__newList)
        view.connect(view.loadButton,SIGNAL('clicked()'),self.__loadList)
        view.connect(view.deleteButton,SIGNAL('clicked()'),self.__deleteList)

        # overload dropEvent()
        self.view.newButton.dropEvent = self.newListDropEvent
        self.view.newButton.dragEnterEvent = self.newListDragEnterEvent
        self.view.songList.dropEvent = self.songListDropEvent
        self.view.playlistList.dropEvent = self.playlistListDropEvent
        # overload keyPressEvent() and keep original
        self.view.playlistList.keyPressEvent = self.listKeyPressEvent
        self.view.songList.keyPressEvent = self.songKeyPressEvent

        # Create actions.
        self.playlistListPlayAdd = self.actionPlayAdd(self.view.playlistList, self.__addPlayList)
        self.playlistListPlayReplace = self.actionPlayReplace(self.view.playlistList, self.__loadPlayList)
        self.playlistListAdd = self.actionAddSongs(self.view.playlistList, self.__addList)
        self.playlistListReplace = self.actionLoad(self.view.playlistList, self.__loadList)
        self.playlistListRemove = self.actionRemove(self.view.playlistList, self.__deleteList)

        self.songListPlayAdd = self.actionPlayAdd(self.view.songList, self.__addPlaySong)
        self.songListPlayReplace = self.actionPlayReplace(self.view.songList, self.__clearPlaySong)
        self.songListAdd = self.actionAddSongs(self.view.songList, self.__addSong)
        self.songListRemove = self.actionRemove(self.view.songList, self.__removeSong)


    def listKeyPressEvent(self, event):
        if event.matches(QKeySequence.Delete):
            self.__deleteList()
        elif event.key() == Qt.Key_Escape:
            self.view.playlistList.setCurrentRow(-1)
        else:
            QListWidget.keyPressEvent(self.view.playlistList, event)

    def songKeyPressEvent(self, event):
        if event.matches(QKeySequence.Delete):
            self.__removeSong()
        elif event.key() == Qt.Key_Escape:
            self.view.songList.setCurrentRow(-1)
        else:
            QTreeWidget.keyPressEvent(self.view.songList, event)

    def newListDragEnterEvent(self, event):
        event.accept()

    def newListDropEvent(self, event):
        print 'dropped new playlist'
        self.__newList()
        self.songListDropEvent(event, -1)

    def playlistListDropEvent(self, event):
        self.currentPlaylist = unicode(self.view.playlistList.itemAt(event.pos()).text())
        self.songListDropEvent(event, -1)

    def songListDropEvent(self, event, toPos=None):
        event.setDropAction(Qt.CopyAction)
        source = event.source()
        if not toPos:
            toPos = self.view.songList.itemAt(event.pos())
            toPos = self.view.songList.indexFromItem(toPos).row()
        if source == self.view.songList:
            event.accept()
            itemList = [x.song for x in source.selectedItems()]
            print 'debug: ', itemList
            for song in itemList:
                songList = self.mpdclient.listplaylistinfo(self.currentPlaylist)
                self.mpdclient.playlistmove(self.currentPlaylist, songList.index(song), toPos)
                if songList.index(song) < toPos:
                    toPos += 1
        elif source == self.view.currentList:
            self.dropSong(event, toPos)
        elif source == self.view.artistView:
            self.dropArtist(event, toPos)
        elif source == self.view.albumView:
            self.dropAlbum(event, toPos)
        elif source == self.view.trackView:
            self.dropSong(event, toPos)
        elif source == self.view.playlistList:
            self.dropPlaylist(event, toPos)
        elif source == self.view.filesystemTree:
            self.dropFile(event, toPos)
        elif source == self.view.genreList:
            self.dropURL(event, toPos)
        elif source == self.view.bookmarkList:
            self.dropURL(event, toPos)


    def addDrop(self, itemList, toPos):
        try:
            self.view.setCursor(Qt.WaitCursor)
            count = self.view.songList.topLevelItemCount()
            if not self.currentPlaylist:
                self.currentPlaylist = self.__newList()
            self.mpdclient.command_list_ok_begin()
            for i, song in enumerate(itemList):
                self.mpdclient.playlistadd(self.currentPlaylist, song)
                if toPos >= 0:
                    self.mpdclient.playlistmove(self.currentPlaylist, count, toPos)
                    toPos += 1
                    count += 1
            self.mpdclient.command_list_end()
        finally:
            self.view.setCursor(Qt.ArrowCursor)


    def reload(self):
        '''Reload the lists from the server'''
        try:
            plname = unicode(self.view.playlistList.selectedItems()[0].text())
        except:
            plname = None
        self.view.playlistList.clear()
        playlists = [x['playlist'] for x in self.mpdclient.lsinfo() if 'playlist' in x]
        playlists.sort(auxilia.cmpUnicode)
        for l in playlists:
            self.view.playlistList.addItem(l)

        self.currentPlaylist = plname
        self.__getPlaylist(plname)

    def selectPlaylist(self, item):
        self.__getPlaylist(unicode(item.text()))

    def __getPlaylist(self, plname=None):
        '''Load up and display the selected playlist or the one given.'''
        self.view.songList.clear()
        if not plname:
            try:
                plname = unicode(self.view.playlistList.selectedItems()[0].text())
            except:
                return
        else: self.view.playlistList.setCurrentItem(self.view.playlistList.findItems(plname, Qt.MatchExactly)[0])
        self.currentPlaylist = plname

        try:
            songList = self.mpdclient.listplaylistinfo(plname)
            for i, song in enumerate(songList):
                self.view.songList.addTopLevelItem(songwidgets.LongSongWidget(song, i))
        except mpd.CommandError:
            pass

        for i in range(3):
            self.view.songList.resizeColumnToContents(i)

    def __loadPlayList(self):
        self.__loadList()
        self.mpdclient.play()

    def __addPlayList(self):
        last = int(self.mpdclient.status['playlistlength'])
        self.__addList()
        self.mpdclient.play(last)

    def __loadList(self):
        '''Load the currently selected playlist onto the server.
           Note: this operation clears the current playlist by default.
        '''
        state = self.mpdclient.status()['state']
        self.view.currentList.clear()
        self.mpdclient.clear()
        self.__addList(state)

    def __addList(self, state=None):
        '''Load the currently selected playlist onto the server.
        '''
        if not state:
            state = self.mpdclient.status()['state']
        try:
            self.mpdclient.load(unicode(self.view.playlistList.selectedItems()[0].text()))
        except:
            return
        if state == 'play':
            self.mpdclient.play()

    def __newList(self):
        '''Ask the user for a name for the new playlist'''
        playlists = [x['playlist'] for x in self.mpdclient.lsinfo() if 'playlist' in x]

        (name,ok) = QInputDialog.getText(self.view
                , 'new Playlist'
                , 'Please enter a name for the new playlist.'
                , 0
                , 'New Playlist')
        if ok == True:
            while name in playlists:
                (name,ok) = QInputDialog.getText(self.view
                        , 'new Playlist'
                        , 'The playlist %s already exists.\nPlease enter a different name' % name
                        , 0
                        , 'New Playlist')
                if ok != True:
                    return self.currentPlaylist
            self.view.playlistList.addItem(name)
            try:
                self.view.playlistList.setCurrentItem(self.view.playlistList.findItems(name, Qt.MatchExactly)[0])
            except:
                pass
            self.view.songList.clear()
            self.currentPlaylist = name
            return name

    def __deleteList(self):
        '''Delete the currently selected playlist.'''
        try:
            item = self.view.playlistList.selectedItems()[0]
        except:
            return
        plname = unicode(item.text())
        resp = QMessageBox.question(self.view,'Delete Playlist','Are you sure you want to delete '+plname,QMessageBox.Yes|QMessageBox.No,QMessageBox.No)
        if resp == QMessageBox.Yes:
            try:
                self.mpdclient.rm(plname)
            except mpd.CommandError:
                pass
            self.view.playlistList.takeItem(self.view.playlistList.row(item))


    def __addPlaySong(self):
        last = int(self.mpdclient.status['playlistlength'])
        self.__addSong()
        self.mpdclient.play(last)

    def __clearPlaySong(self):
        self.mpdclient.clear()
        self.__addPlaySong()

    def __addSong(self):
        self.mpdclient.command_list_ok_begin()
        try:
            for item in self.view.songList.selectedItems():
                self.mpdclient.add(item.song['file'])
        finally:
            self.mpdclient.command_list_end()

    def __removeSong(self):
        itemlist = self.view.songList.selectedItems()
        itemlist.reverse()
        self.mpdclient.command_list_ok_begin()
        try:
            for item in itemlist:
                self.mpdclient.playlistdelete(self.currentPlaylist, item.pos)
        finally:
            self.mpdclient.command_list_end()

