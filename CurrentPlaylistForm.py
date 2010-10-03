# -*- coding: utf-8 -*
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
from PyQt4.QtCore import SIGNAL, Qt, QSize#, QTimer
from PyQt4.QtGui import QWidget, QInputDialog, QKeySequence, QListWidget, QIcon
from PyQt4 import uic
from time import time
from sys import getrefcount

import songwidgets
import auxilia
import iconretriever

# TODO: See if drag pixmap can be alpha blended. (probably impossible)
# TODO: Make cover art download optional.

#===============================================================================
# List and controls for the currently loaded playlist
#===============================================================================
class CurrentPlaylistForm(QWidget, auxilia.Actions):
    '''List and controls for the currently loaded playlist'''
    updating = False
    editing = 0
    playing = -1
    currentPlayTime = 0
    def __init__(self, view, app, mpdclient, config):
        QWidget.__init__(self)
        self.app = app
        self.view = view
        self.mpdclient = mpdclient
        self.config = config
        if self.view.KDE:
            uic.loadUi('ui/CurrentListForm.ui', self)
        else:
            uic.loadUi('ui/CurrentListForm.ui.Qt', self)
        self.view.currentListLayout.addWidget(self)

        self.retriever = iconretriever.ThreadedRetriever(config.musicPath)
        if config.oneLinePlaylist:
            self.oneLinePlaylist.setChecked(True)
            self.currentList.setIconSize(QSize(16, 16))
        else:
            self.currentList.setIconSize(QSize(32, 32))
        self.keepPlayingVisible.setChecked(self.config.keepPlayingVisible)
        self.__togglePlaylistTools(self.config.playlistControls)
        self.version = 0
        self.idlist = []
        self.trackKey = ''
        self.view.connect(self.view, SIGNAL('playlistChanged'), self.reload)
        self.view.connect(self.view, SIGNAL('resetCurrentList()'), self.__resetCurrentList)
        self.view.connect(self.view, SIGNAL('currentSong'), self.setPlaying)

        # Connect to the list for double click action.
        self.connect(self.currentList,SIGNAL('itemDoubleClicked(QListWidgetItem*)'),self.__playSong)

        self.connect(self.currentFilter,SIGNAL('textEdited(QString)'),self.trackSearch)

        self.connect(self.currentRemove,SIGNAL('clicked()'),self.__removeSelected)
        self.connect(self.currentClear,SIGNAL('clicked()'),self.__clearCurrent)
        self.connect(self.currentSave,SIGNAL('clicked()'),self.__saveCurrent)

        self.currentList.dropEvent = self.dropEvent
        self.currentList.dragEnterEvent = self.dragEnterEvent

        # Overload keyPressEvent.
        self.currentList.keyPressEvent = self.keyPressEvent

        self.connect(self.currentBottom, SIGNAL('clicked()'), self.__togglePlaylistTools)
        self.connect(self.currentList,SIGNAL('itemSelectionChanged()'),self._setEditing)
        self.connect(self.currentList.verticalScrollBar(), SIGNAL('valueChanged(int)'), self._setEditing)
        self.connect(self.keepPlayingVisible,SIGNAL('toggled(bool)'),self.__toggleKeepPlayingVisible)
        self.connect(self.oneLinePlaylist,SIGNAL('toggled(bool)'),self.__setOneLinePlaylist)

        # Menu for current playlist.
        # Create actions.
        self.currentMenuPlay = self.action(self.currentList, self.__playFromMenu,
                icon="media-playback-start", text='play', tooltip='Start playing the selected song.')
        self.currentMenuRemove = self.action(self.currentList, self.__removeSelected,
                icon="list-remove", text='Remove', tooltip="Remove the selected songs from the playlist.")
        self.currentMenuClear = self.action(self.currentList, self.__clearCurrent,
                icon="document-new", text='Clear', tooltip="Remove all songs from the playlist.")
        self.currentMenuSave = self.action(self.currentList, self.__saveCurrent,
                icon="document-save-as", text='Save', tooltip="Save the current playlist.")
        self.currentMenuCrop = self.action(self.currentList, self.__cropCurrent,
                icon="project-development-close", text='Crop', tooltip="Remove all but the selected songs.")
        # Add the actions to widget.
        self.currentList.addAction(self.currentMenuPlay)
        self.currentList.addAction(self.currentMenuRemove)
        self.currentList.addAction(self.currentMenuClear)
        self.currentList.addAction(self.currentMenuSave)
        self.currentList.addAction(self.currentMenuCrop)


    def setPlaying(self, currentsong):
        playing = int(currentsong['pos'])
        print 'debug: setPlaying to ', playing
        beforeScroll = self.currentList.verticalScrollBar().value()
        item = self.currentList.item(self.playing)
        if item:
            item.playing(False)
        if playing >= 0:
            item = self.currentList.item(playing)
            if item:
                item.playing(True)
                self.playing = playing
            else: self.playing = -1
        else: self.playing = -1
        self.__scrollList(beforeScroll)

    def reload(self, plist, status):
        '''Causes the current play list to be reloaded from the server'''
        if not self.config.server:
            return
        oneLine = self.config.oneLinePlaylist
        beforeScroll = self.currentList.verticalScrollBar().value()
        self.selection = [item.song['id'] for item in self.currentList.selectedItems()]
        itemlist = {}
        version = int(status['playlist'])
        if version <= self.version:
            return
        # Get the song id's of the selected songs.
        self.currentList.setUpdatesEnabled(False)
        if plist:
            oldPos = int(plist[0]['pos'])
            for song in plist:
                song['pos'] = int(song['pos'])
                # if the song is in our parralel id list.
                if song['id'] in self.idlist:
                    # get the id position.
                    index = self.idlist.index(song['id'])
                    # take the item.
                    item = self._takeItem(index)
                    item.song = song
                    # If the old position is after the new position (moving up).
                    if index > song['pos']:
                        # take all songs that were between old and new position and put them in a dict.
                        for x in range(song['pos'], index):
                            holditem = self._takeItem(song['pos'])
                            itemlist[holditem.song['id']] = holditem
                    # put the item back in the list at the right position.
                    self._insertItem(song['pos'], item)
                # if ist in our 'hold on to' list.
                elif song['id'] in itemlist:
                    if oldPos+1 < song['pos']:
                        items = []
                        for item in itemlist.values():
                            if int(item.song['pos']) > oldPos and int(item.song['pos']) < song['pos']:
                                items.append(item)
                        items.sort(key=lambda x: x.song['pos'], reverse=True)
                        for item in items:
                            self._insertItem(oldPos+1, item)
                    # pick the item from the dict.
                    item = itemlist[song['id']]
                    # update the song atribute.
                    item.song = song
                    # put it in place in the view.
                    self._insertItem(song['pos'], item)
                else:
                    # If the song is not in the parallel or the 'hold on to' list. Just insert a new item at the correct position.
                    item = songwidgets.CurrentListWidget(song, oneLine)
                    self._insertItem(song['pos'], item)
                oldPos = song['pos']
                # select the song again if needed.
                if song['id'] in self.selection: item.setSelected(True)

        # If the playlist has shrunk, delete the songs from the end.
        last = int(status['playlistlength'])
        for x in range(last, self.currentList.count()):
            self._takeItem(last)

        self.view.numSongsLabel.setText(status['playlistlength']+' Songs')
        self.__setPlayTime()

        self.__scrollList(beforeScroll)
        self.version = version
        self.setPlaying({'pos': status.get('song', -1)})
        key = unicode(self.currentFilter.text())
        if key != '':
            self.trackSearch(key)
        self.currentList.setUpdatesEnabled(True)

    def loadIcons(self):
        while self.retriever.icons:
            item, icon = self.retriever.icons.pop(0)
            if getrefcount(item) > 2:
                item.setIcon(QIcon(icon))

    def trackSearch(self, key):
        print 'debug: trackSearch starting.'
        self.currentList.setUpdatesEnabled(False)
        t = time()
        hits = self.currentList.findItems(key, (Qt.MatchContains|Qt.MatchWrap))
        print 'debug: trackSearch found %i items.' % len(hits)
        whole = self.currentList.findItems('', (Qt.MatchContains|Qt.MatchWrap))
        print 'debug: trackSearch made total list.'
        for i, item in enumerate(set(whole) - set(hits)):
            item.setHidden(True)
        print 'debug: trackSearch hidden all not in hits.'
        for i, item in enumerate(hits):
            item.setHidden(False)
        self.currentList.setUpdatesEnabled(True)
        print 'debug: trackSearch took %.3f seconds.' % (time()-t)

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.Delete):
            self.__removeSelected()
        elif event.key() == Qt.Key_Escape:
            self.currentList.currentList.setCurrentRow(-1)
        else:
            QListWidget.keyPressEvent(self.currentList, event)

    def dragEnterEvent(self, event):
        if hasattr(event.source().selectedItems()[0], 'getDrag'):
            event.accept()

    def dropEvent(self, event, clear=False):
        event.setDropAction(Qt.CopyAction)
        if not clear:
            toPos = self.currentList.row(self.currentList.itemAt(event.pos()))
            if toPos > 0:
                toPos += self.currentList.dropIndicatorPosition()-1
        else:
            self.mpdclient.send('clear')
            toPos = -1
        print 'debug: drop on position ', toPos
        if event.source() == self.currentList:
            event.accept()
            self.__internalMove(toPos)
        else:
            self.__drop(event, toPos)

    def __internalMove(self, toPos):
        # Move the songs to the new position.
        if toPos < 0:
            toPos = self.currentList.count()
        itemList = self.currentList.selectedItems()
        itemList.sort(key=self.currentList.row)
        print 'debug: ', [unicode(x.text()) for x in itemList]
        itemList.reverse()
        for item in itemList:
            if self.currentList.row(item) < toPos:
                toPos -= 1
            print "debug: move ", unicode(item.text()), "to", toPos
            self.mpdclient.send('moveid', (item.song['id'], toPos))

    def __drop(self, event, toPos):
        event.accept()
        itemList = event.source().selectedItems()
        itemList = [item.getDrag(self.mpdclient) for item in itemList]
        try:
            print 'debug: adding', itemList
            self.view.setCursor(Qt.WaitCursor)
            self.mpdclient.send('command_list_ok_begin')
            for item in itemList:
                for song in item:
                    if toPos < 0:
                        self.mpdclient.send('add', (song['file'],))
                    else:
                        self.mpdclient.send('addid', (song['file'], toPos))
                        toPos += 1
        finally:
            self.mpdclient.send('command_list_end')
            self.editing = time()
            self.view.setCursor(Qt.ArrowCursor)


    def _takeItem(self, row):
        item = self.currentList.takeItem(row)
        del self.idlist[row]
        self.currentPlayTime -= int(item.song.get('time','0'))
        return item

    def _insertItem(self, row, item):
        self.currentList.insertItem(row, item)
        self.idlist.insert(row, item.song['id'])
        if not item.icon:
            self.retriever.fetchIcon(item, self.config.musicPath)
        self.currentPlayTime += int(item.song.get('time','0'))

    def __resetCurrentList(self):
        self.currentList.clear()
        self.idlist = []
        self.version = 0
        self.playing = -1
        self.currentPlayTime = 0

    def __scrollList(self, beforeScroll=None):
        editing = time() - self.editing
        count = self.currentList.count()
        maxScroll = self.currentList.verticalScrollBar().maximum()
        if editing <= 5:
            keepCurrent = False
        else:
            keepCurrent = self.config.keepPlayingVisible
        if keepCurrent:
            self.currentList.scrollToItem(self.currentList.item(self.playing - ((count - maxScroll)/8)), 1)
        elif beforeScroll:
            self.currentList.scrollToItem(self.currentList.item(beforeScroll), 1)

    def __saveCurrent(self):
        '''Save the current playlist'''
        lsinfo = self.mpdclient.lsinfo()
        playlists = []
        for somedict in lsinfo:
            if somedict.get('playlist',None) != None:
                playlists.append(somedict['playlist'])

        (name,ok) = QInputDialog.getItem(self,'Save Playlist','Enter or select the playlist name',playlists,0,True)
        if ok == True:
            if name in playlists:
                self.mpdclient.send('rm', (name,))
            self.mpdclient.send('save', (name,))

    def __clearCurrent(self):
        '''Clear the current playlist'''
        self.mpdclient.send('stop')
        self.mpdclient.send('clear')
        self.reload()

    def __removeSelected(self):
        '''Remove the selected item(s) from the current playlist'''
        self.__removeSongs(self.currentList.selectedItems())

    def __cropCurrent(self):
        idlist = []
        for x in xrange(self.currentList.count()):
            item = self.currentList.item(x)
            if not item.isSelected():
                idlist.append(item)
        self.__removeSongs(idlist)

    def __removeSongs(self, itemList):
        self.mpdclient.send('command_list_ok_begin')
        for item in itemList:
            try:
                self.mpdclient.send('deleteid', (item.song['id'],))
            except Exception, e:
                print e
        self.mpdclient.send('command_list_end')
        self.currentList.setCurrentRow(-1)

    def __playFromMenu(self):
        self.__playSong(self.currentList.selectedItems())

    def __playSong(self, item):
        self.mpdclient.send('playid', (self.currentList.currentItem().song['id'],))

    def __setPlayTime(self):
        songTime = self.currentPlayTime
        songMin = int(songTime / 60)
        songSecs = songTime - (songMin * 60)
        songHour = int(songMin / 60)
        songMin -= songHour * 60
        songDay = songHour / 24
        songHour -= songDay * 24
        if songDay == 1:
            self.view.playTimeLabel.setText('Total play time: %d day %02d:%02d:%02d ' % (songDay, songHour, songMin, songSecs))
        elif songDay > 0:
            self.view.playTimeLabel.setText('Total play time: %d days %02d:%02d:%02d ' % (songDay, songHour, songMin, songSecs))
        else:
            self.view.playTimeLabel.setText('Total play time: %02d:%02d:%02d ' % (songHour, songMin, songSecs))

    def __toggleKeepPlayingVisible(self, value):
        self.config.keepPlayingVisible = value
        self.__scrollList()

    def __setOneLinePlaylist(self, value):
        self.config.oneLinePlaylist = value
        self.view.emit(SIGNAL('resetCurrentList()'))
        if value:
            self.currentList.setIconSize(QSize(16, 16))
        else:
            self.currentList.setIconSize(QSize(32, 32))
        self.mpdclient.send('status', callback=
                lambda status: self.view.emit(SIGNAL('update'), ['playlist'], status))

    def __togglePlaylistTools(self, value=None):
        text = ('Show Playlist Tools', 'Hide Playlist Tools')
        if value == None:
            if self.playlistTools.isVisible():
                self.playlistTools.setVisible(False)
            else:
                self.playlistTools.setVisible(True)
            value = self.playlistTools.isVisible()
        else:
            self.playlistTools.setVisible(value)
        self.currentBottom.setArrowType(int(value)+1)
        self.currentBottom.setText(text[value])
        self.config.playlistControls = bool(self.playlistTools.isVisible())

    def _setEditing(self, i=0):
        self.editing = time()

