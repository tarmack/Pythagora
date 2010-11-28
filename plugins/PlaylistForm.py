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
from PyQt4.QtGui import QMessageBox, QInputDialog, QKeySequence, QListWidget, QTreeWidget, QTreeWidgetItem, QListWidgetItem
from PyQt4 import uic

import mpd
import auxilia
import mpdlibrary
import PluginBase

DATA_DIR = ''

# TODO: Double click actions. playlistlist add to current.

#==============================================================================
# Display and manage the currently known playlists.
#==============================================================================
class PlaylistForm(PluginBase.PluginBase, auxilia.Actions):
    '''Display and manage the currently known playlists.'''
    moduleName = '&PlayLists'
    moduleIcon = 'document-multiple'

    def load(self):
        self.currentPlaylist = None
        self.view.connect(self.view,SIGNAL('reloadPlaylists'),self.reload)
        self.view.connect(self.view,SIGNAL('clearForms'),self.clear)
        # Load and place the stored playlists form.
        if self.view.KDE:
            uic.loadUi(DATA_DIR+'ui/PlaylistsForm.ui', self)
        else:
            uic.loadUi(DATA_DIR+'ui/PlaylistsForm.ui.Qt', self)
        self.playlistSplitter.setSizes(self.config.playlistSplit)

        # top bit
        self.connect(self.playlistList,SIGNAL('itemSelectionChanged()'),self.selectPlaylist)
        self.connect(self.playlistList,SIGNAL('itemDoubleClicked(QListWidgetItem*)'),self.__addList)
        self.connect(self.newButton,SIGNAL('clicked()'),self.__newList)
        self.connect(self.loadButton,SIGNAL('clicked()'),self.__loadList)
        self.connect(self.deleteButton,SIGNAL('clicked()'),self.__deleteList)
        self.connect(self, SIGNAL('showPlaylist'), self.__showPlaylist)
        self.connect(self.playlistSplitter, SIGNAL('splitterMoved(int, int)'), self.__storeSplitter)

        # overload dropEvent()
        self.newButton.dragEnterEvent = self.dragEnterEvent
        self.newButton.dropEvent = self.newListDropEvent
        self.songList.dragEnterEvent = self.dragEnterEvent
        self.songList.dropEvent = self.songListDropEvent
        self.playlistList.dragEnterEvent = self.dragEnterEvent
        self.playlistList.dropEvent = self.playlistListDropEvent
        # overload keyPressEvent()
        self.playlistList.keyPressEvent = self.listKeyPressEvent
        self.songList.keyPressEvent = self.songKeyPressEvent

        # Create actions.
        self.playlistListPlayAdd = self.actionPlayAdd(self.playlistList, self.__addPlayList)
        self.playlistListPlayReplace = self.actionPlayReplace(self.playlistList, self.__loadPlayList)
        self.playlistListAdd = self.actionAddSongs(self.playlistList, self.__addList)
        self.playlistListReplace = self.actionLoad(self.playlistList, self.__loadList)
        self.playlistListRemove = self.actionRemove(self.playlistList, self.__deleteList)

        self.songListPlayAdd = self.actionPlayAdd(self.songList, self.__addPlaySong)
        self.songListPlayReplace = self.actionPlayReplace(self.songList, self.__clearPlaySong)
        self.songListAdd = self.actionAddSongs(self.songList, self.__addSong)
        self.songListRemove = self.actionRemove(self.songList, self.__removeSong)


    def listKeyPressEvent(self, event):
        if event.matches(QKeySequence.Delete):
            self.__deleteList()
        elif event.key() == Qt.Key_Escape:
            self.playlistList.setCurrentRow(-1)
        else:
            QListWidget.keyPressEvent(self.playlistList, event)

    def songKeyPressEvent(self, event):
        if event.matches(QKeySequence.Delete):
            self.__removeSong()
        elif event.key() == Qt.Key_Escape:
            self.songList.setCurrentRow(-1)
        else:
            QTreeWidget.keyPressEvent(self.songList, event)

    def dragEnterEvent(self, event):
        if hasattr(event.source().selectedItems()[0], 'getDrag'):
            event.accept()

    def newListDropEvent(self, event):
        print 'dropped new playlist'
        self.__newList()
        self.songListDropEvent(event, -1)

    def playlistListDropEvent(self, event):
        self.currentPlaylist = unicode(self.playlistList.itemAt(event.pos()).text())
        self.songListDropEvent(event, -1)

    def songListDropEvent(self, event, toPos=None):
        event.setDropAction(Qt.CopyAction)
        source = event.source()
        # FIXME: Internal move upwards reverses order.
        # FIXME: Internal move downwards interleves moved with existing songs.
        if not toPos:
            toPos = self.songList.itemAt(event.pos())
            toPos = self.songList.indexFromItem(toPos).row()
        if source == self.songList:
            event.accept()
            itemList = [x.song for x in source.selectedItems()]
            print 'debug: ', itemList
            for song in itemList:
                songList = self.mpdclient.listplaylistinfo(self.currentPlaylist)
                self.mpdclient.send('playlistmove', (self.currentPlaylist, songList.index(song), toPos))
                if songList.index(song) < toPos:
                    toPos += 1
        else:
            itemList = event.source().selectedItems()
            itemList = [item.getDrag() for item in itemList]
            try:
                self.view.setCursor(Qt.WaitCursor)
                count = self.songList.topLevelItemCount()
                if not self.currentPlaylist:
                    self.currentPlaylist = self.__newList()
                self.mpdclient.send('command_list_ok_begin')
                for item in itemList:
                    for i, song in enumerate(item):
                        self.mpdclient.send('playlistadd', (self.currentPlaylist, song['file']))
                        if toPos >= 0:
                            self.mpdclient.send('playlistmove', (self.currentPlaylist, count, toPos))
                            toPos += 1
                            count += 1
            except:
                raise
            finally:
                self.mpdclient.send('command_list_end')
                self.view.setCursor(Qt.ArrowCursor)

    def reload(self, playlists):
        '''Reload the lists from the server'''
        try:
            plname = unicode(self.playlistList.selectedItems()[0].text())
        except:
            plname = None
        self.playlistList.clear()
        playlists.sort(auxilia.cmpUnicode)
        for l in playlists:
            self.playlistList.addItem(PlaylistWidget(l, self.mpdclient))

        self.currentPlaylist = plname
        self.__getPlaylist(plname)

    def clear(self):
        self.playlistList.clear()
        self.songList.clear()
        self.currentPlaylist = None

    def selectPlaylist(self):
        if self.playlistList.selectedItems():
            item = self.playlistList.selectedItems()[0]
            self.__getPlaylist(unicode(item.text()))

    def __getPlaylist(self, plname=None):
        '''Load up and display the selected playlist or the one given.'''
        self.songList.clear()
        if not plname:
            try:
                plname = unicode(self.playlistList.selectedItems()[0].text())
            except:
                return
        else: self.playlistList.setCurrentItem(self.playlistList.findItems(plname, Qt.MatchExactly)[0])
        self.currentPlaylist = plname
        self.mpdclient.send('listplaylistinfo', (plname,), callback=
                lambda songlist: self.emit(SIGNAL('showPlaylist'), songlist))

    def __showPlaylist(self, songlist):
        if isinstance(songlist, Exception):
            return
        for i, song in enumerate(songlist):
            self.songList.addTopLevelItem(LongSongWidget(song, i))
        for i in range(3):
            self.songList.resizeColumnToContents(i)


    def __loadPlayList(self):
        self.__loadList()
        self.mpdclient.send('play')

    def __addPlayList(self):
        last = int(self.mpdclient.status()['playlistlength'])
        self.__addList()
        self.mpdclient.send('play', (last,))

    def __loadList(self):
        '''Load the currently selected playlist onto the server.
           Note: this operation clears the current playlist by default.
        '''
        state = self.mpdclient.status()['state']
        self.mpdclient.send('clear')
        self.__addList(state)

    def __addList(self, state=None):
        '''Load the currently selected playlist onto the server.
        '''
        if not state:
            state = self.mpdclient.status()['state']
        try:
            self.mpdclient.send('load', (unicode(self.playlistList.selectedItems()[0].text()),))
        except:
            return
        if state == 'play':
            self.mpdclient.send('play')

    def __newList(self):
        '''Ask the user for a name for the new playlist'''
        (name,ok) = QInputDialog.getText(self
                , 'new Playlist'
                , 'Please enter a name for the new playlist.'
                , 0
                , 'New Playlist')
        if ok == True:
            while self.playlistList.findItems(name, Qt.MatchExactly):
                (name,ok) = QInputDialog.getText(self
                        , 'new Playlist'
                        , 'The playlist %s already exists.\nPlease enter a different name' % name
                        , 0
                        , 'New Playlist')
                if ok != True:
                    return self.currentPlaylist
            self.playlistList.addItem(PlaylistWidget(name))
            try:
                self.playlistList.setCurrentItem(self.playlistList.findItems(name, Qt.MatchExactly)[0])
            except:
                pass
            self.songList.clear()
            self.currentPlaylist = name
            return name

    def __deleteList(self):
        '''Delete the currently selected playlist.'''
        try:
            item = self.playlistList.selectedItems()[0]
        except:
            return
        plname = unicode(item.text())
        resp = QMessageBox.question(self,'Delete Playlist','Are you sure you want to delete '+plname,QMessageBox.Yes|QMessageBox.No,QMessageBox.No)
        if resp == QMessageBox.Yes:
            try:
                self.mpdclient.send('rm', (plname,))
            except mpd.CommandError:
                pass
            self.playlistList.takeItem(self.playlistList.row(item))


    def __addPlaySong(self):
        last = int(self.mpdclient.status()['playlistlength'])
        self.__addSong()
        self.mpdclient.send('play', (last,))

    def __clearPlaySong(self):
        self.mpdclient.send('clear')
        self.__addPlaySong()

    def __addSong(self):
        self.mpdclient.send('command_list_ok_begin')
        try:
            for item in self.songList.selectedItems():
                self.mpdclient.send('add', (item.song['file'],))
        finally:
            self.mpdclient.send('command_list_end')

    def __removeSong(self):
        itemlist = self.songList.selectedItems()
        itemlist.reverse()
        self.mpdclient.send('command_list_ok_begin')
        try:
            for item in itemlist:
                self.mpdclient.send('playlistdelete', (self.currentPlaylist, item.pos))
        finally:
            self.mpdclient.send('command_list_end')

    def __storeSplitter(self):
        self.config.playlistSplit = self.playlistSplitter.sizes()

# Widget subclasses.
class PlaylistWidget(QListWidgetItem):
    '''Widget used in the stored playlist list.'''
    def __init__(self, text, mpdclient):
        self.mpdclient = mpdclient
        QListWidgetItem.__init__(self)
        self.setText(text)

    def getDrag(self):
        return self.mpdclient.listplaylistinfo(self.text())

class LongSongWidget(QTreeWidgetItem):
    '''Lays out a song in a three-column tree widget: artist, title, album.
    Used in PlaylistForm.'''
    def __init__(self, song, pos):
        QTreeWidgetItem.__init__(self)
        self.song = song
        self.pos = pos
        self.setText(0,mpdlibrary.songArtist(song))
        self.setText(1,mpdlibrary.songTitle(song))
        self.setText(2,mpdlibrary.songAlbum(song))

    def getDrag(self):
        return [self.song]


def getWidget(view, mpdclient, config):
    return PlaylistForm(view, mpdclient, config)
