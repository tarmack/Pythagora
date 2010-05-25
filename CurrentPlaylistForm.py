# -*- coding: utf-8 -*
#-------------------------------------------------------------------------------{{{
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
#-------------------------------------------------------------------------------}}}
from PyQt4.QtCore import SIGNAL, Qt, QSize#, QTimer
from PyQt4.QtGui import QInputDialog, QKeySequence, QListWidget, QIcon
from time import time
from sys import getrefcount

import songwidgets
import auxilia
import iconretriever
import WriteOut
WriteOut.Quiet()

# TODO: Consistent drop placing with indicator.
# TODO: See if drag pixmap can be alpha blended. (probably imposible)
# TODO: Make cover art download optional.

#===============================================================================
# List and controls for the currently loaded playlist
#===============================================================================
class CurrentPlaylistForm(auxilia.DragNDrop):#{{{1
    '''List and controls for the currently loaded playlist'''
    updating = False
    editing = 0
    playing = -1
    currentPlayTime = 0
    def __init__(self, view, app, mpdclient, config):#{{{2
        self.app = app
        self.view = view
        self.mpdclient = mpdclient
        self.config = config

        self.retriever = iconretriever.ThreadedRetriever(config.musicPath)
        #self.version = int(self.mpdclient.status()['playlist'])
        if config.oneLinePlaylist:
            self.view.oneLinePlaylist.setChecked(True)
            self.view.currentList.setIconSize(QSize(16, 16))
        else:
            self.view.currentList.setIconSize(QSize(32, 32))
        self.version = 0
        self.idlist = []
        self.trackKey = ''
        #self.timer = QTimer()
        #self.timer.setSingleShot(True)
        #view.connect(self.timer,SIGNAL('timeout()'),self.__search)
        self.view.connect(self.view, SIGNAL('playlistChanged()'), self.reload)
        self.view.connect(self.view, SIGNAL('resetCurrentList()'), self.__resetCurrentList)
        self.view.connect(self.view, SIGNAL('currentSong'), self.setPlaying)

        # Connect to the list for double click action.
        view.connect(self.view.currentList,SIGNAL('itemDoubleClicked(QListWidgetItem*)'),self.__playSong)

        view.connect(self.view.currentFilter,SIGNAL('textEdited(QString)'),self.trackSearch)

        self.view.connect(self.view.currentRemove,SIGNAL('clicked()'),self.__removeSelected)
        self.view.connect(self.view.currentClear,SIGNAL('clicked()'),self.__clearCurrent)
        self.view.connect(self.view.currentSave,SIGNAL('clicked()'),self.__saveCurrent)

        # Connect to the contextmenu signals.
        self.view.connect(self.view.currentMenuPlay,SIGNAL('triggered()'),self.__playFromMenu)
        self.view.connect(self.view.currentMenuRemove,SIGNAL('triggered()'),self.__removeSelected)
        self.view.connect(self.view.currentMenuClear,SIGNAL('triggered()'),self.__clearCurrent)
        self.view.connect(self.view.currentMenuSave,SIGNAL('triggered()'),self.__saveCurrent)
        self.view.connect(self.view.currentMenuCrop,SIGNAL('triggered()'),self.__cropCurrent)

        self.view.currentList.dropEvent = self.dropEvent

        # Overload keyPressEvent, remap the base implementation to call if we have a key wo don't handle.
        self.view.currentList.keyPressEvent = self.keyPressEvent

        view.connect(self.view.currentList,SIGNAL('indexesMoved(constQModelIndexList&)'),doprint)
        view.connect(self.view.currentList,SIGNAL('itemSelectionChanged()'),self._setEditing)
        view.connect(self.view.currentList.verticalScrollBar(), SIGNAL('valueChanged(int)'), self._setEditing)
        view.connect(self.view.keepPlayingVisible,SIGNAL('clicked()'),self.__scrollList)
        view.connect(self.view.oneLinePlaylist,SIGNAL('toggled(bool)'),self.__setOneLinePlaylist)
        self.view.emit(SIGNAL('playlistChanged()'))

        # Menu for current playlist.{{{3
        # Add the actions to widget.
        self.view.currentList.addAction(self.view.currentMenuPlay)
        self.view.currentList.addAction(self.view.currentMenuRemove)
        self.view.currentList.addAction(self.view.currentMenuClear)
        self.view.currentList.addAction(self.view.currentMenuSave)
        self.view.currentList.addAction(self.view.currentMenuCrop)
        #}}}


    def setPlaying(self, playing): #{{{2
        if playing != self.playing:
            print 'debug: setPlaying to ', playing
            beforeScroll = self.view.currentList.verticalScrollBar().value()
            item = self.view.currentList.item(self.playing)
            if item:
                item.playing(False)
            if playing >= 0:
                item = self.view.currentList.item(playing)
                if item:
                    item.playing(True)
                    self.playing = playing
                else: self.playing = -1
            else: self.playing = -1
            self.__scrollList(beforeScroll)

    def reload(self):#{{{2
        '''Causes the current play list to be reloaded from the server'''
        if not self.config.server or not self.mpdclient.connected():
            return
        oneLine = self.config.oneLinePlaylist
        beforeScroll = self.view.currentList.verticalScrollBar().value()
        self.selection = [item.song['id'] for item in self.view.currentList.selectedItems()]
        itemlist = {}
        try:
            status = self.mpdclient.status()
            version = int(status['playlist'])
            if version > self.version:
                try:
                    plist = self.mpdclient.plchanges(self.version)
                except:
                    return
            else: return
            # Get the song id's of the selected songs.
            self.view.currentList.setUpdatesEnabled(False)
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
                    # put the item back in the list at the right possition.
                    self._insertItem(song['pos'], item)
                # if ist in our 'hold on to' list.
                elif song['id'] in itemlist:
                    # pick the item from the dict.
                    item = itemlist[song['id']]
                    # update the song atribute.
                    item.song = song
                    # put it in place in the view.
                    self._insertItem(song['pos'], item)
                else:
                    # If the song is not in the paralel or the 'hold on to' list. Just insert a new item at the correct possition.
                    item = songwidgets.FullTreeWidget(song, oneLine)
                    self._insertItem(song['pos'], item)
                # select the song again if needed.
                if song['id'] in self.selection: item.setSelected(True)

            # If the playlist has shrunk, delete the songs from the end.
            last = int(status['playlistlength'])
            for x in range(last, self.view.currentList.count()):
                self.view.currentList.takeItem(last)

            self.view.numSongsLabel.setText(status['playlistlength']+' Songs')
            self.__setPlayTime(self.currentPlayTime)

            self.view.currentList.setUpdatesEnabled(True)
            self.__scrollList(beforeScroll)
            self.version = version
            self.setPlaying(int(status.get('song', -1)))
            key = unicode(self.view.currentFilter.text())
            if key != '':
                self.trackSearch(key)
        except Exception, e:
            print 'error: currentlist update exception', e
        finally:
            self.view.currentList.setUpdatesEnabled(True)

    def loadIcons(self):#{{{2
        while self.retriever.icons:
            item, icon = self.retriever.icons.pop(0)
            if getrefcount(item) > 2:
                item.setIcon(QIcon(icon))

    def trackSearch(self, key):#{{{2
        print 'debug: trackSearch starting.'
        self.view.currentList.setUpdatesEnabled(False)
        t = time()
        hits = self.view.currentList.findItems(key, (Qt.MatchContains|Qt.MatchWrap))
        print 'debug: trackSearch found %i items.' % len(hits)
        whole = self.view.currentList.findItems('', (Qt.MatchContains|Qt.MatchWrap))
        print 'debug: trackSearch made total list.'
        for i, item in enumerate(set(whole) - set(hits)):
            item.setHidden(True)
        print 'debug: trackSearch hidden all not in hits.'
        for i, item in enumerate(hits):
            item.setHidden(False)
        self.view.currentList.setUpdatesEnabled(True)
        print 'debug: trackSearch took %.3f seconds.' % (time()-t)

    def keyPressEvent(self, event):#{{{2
        if event.matches(QKeySequence.Delete):
            self.__removeSelected()
        elif event.key() == Qt.Key_Escape:
            self.view.currentList.setCurrentRow(-1)
        else:
            QListWidget.keyPressEvent(self.view.currentList, event)

    def dropEvent(self, event):#{{{2
        event.setDropAction(Qt.CopyAction)
        source = event.source()
        toPos = self.view.currentList.row(self.view.currentList.itemAt(event.pos()))
        if source == self.view.currentList:
            # FIXME: moving non contiguous selection to a position in the
            #        middle of the selection messes up order.
            event.accept()
            # Move the songs to the new position.
            itemList = self.view.currentList.selectedItems()
            if toPos < itemList[-1].song['pos']:
                # We moved up, reverse the list.
                itemList.reverse()
            for item in itemList:
                if toPos < 0:
                    toPos = self.view.currentList.count()-1
                self.mpdclient.moveid(item.song['id'], toPos)
            self.view.emit(SIGNAL('playlistChanged()'))
        elif source == self.view.songList:
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

    def addDrop(self, itemList, toPos):#{{{2
        try:
            self.view.setCursor(Qt.WaitCursor)
            self.mpdclient.command_list_ok_begin()
            for song in itemList:
                if toPos < 0:
                    self.mpdclient.add(song)
                else:
                    self.mpdclient.addid(song, toPos)
                    toPos += 1
        finally:
            self.mpdclient.command_list_end()
            self.editing = time()
            self.view.setCursor(Qt.ArrowCursor)

    def _takeItem(self, row):#{{{2
        item = self.view.currentList.takeItem(row)
        del self.idlist[row]
        self.currentPlayTime -= int(item.song.get('time','0'))
        return item

    def _insertItem(self, row, item):#{{{2
        self.view.currentList.insertItem(row, item)
        self.idlist.insert(row, item.song['id'])
        if not item.icon:
            self.retriever.fetchIcon(item, self.config.musicPath)
        self.currentPlayTime += int(item.song.get('time','0'))

    def __resetCurrentList(self):#{{{2
        self.view.currentList.clear()
        self.idlist = []
        self.version = 0
        self.playing = -1
        self.reload()

    def __scrollList(self, beforeScroll=None):#{{{2
        editing = time() - self.editing
        count = self.view.currentList.count()
        maxScroll = self.view.currentList.verticalScrollBar().maximum()
        if editing <= 5:
            keepCurrent = False
        else:
            keepCurrent = self.view.keepPlayingVisible.isChecked()
        if keepCurrent:
            self.view.currentList.scrollToItem(self.view.currentList.item(self.playing - ((count - maxScroll)/8)), 1)
        elif beforeScroll:
            self.view.currentList.scrollToItem(self.view.currentList.item(beforeScroll), 1)

    def __saveCurrent(self):#{{{2
        '''Save the current playlist'''
        lsinfo = self.mpdclient.lsinfo()
        playlists = []
        for somedict in lsinfo:
            if somedict.get('playlist',None) != None:
                playlists.append(somedict['playlist'])

        (name,ok) = QInputDialog.getItem(self.view,'Save Playlist','Enter or select the playlist name',playlists,0,True)
        if ok == True:
            if name in playlists:
                self.mpdclient.rm(name)
            self.mpdclient.save(name)
            self.view.emit(SIGNAL('reloadPlaylists()'))

    def __clearCurrent(self):#{{{2
        '''Clear the current playlist'''
        self.mpdclient.stop()
        self.mpdclient.clear()
        self.reload()

    def __removeSelected(self):#{{{2
        '''Remove the selected item(s) from the current playlist'''
        self.__removeSongs(self.view.currentList.selectedItems())

    def __cropCurrent(self):#{{{2
        idlist = []
        for x in xrange(self.view.currentList.count()):
            item = self.view.currentList.item(x)
            if not item.isSelected():
                idlist.append(item)
        self.__removeSongs(idlist)

    def __removeSongs(self, itemList):#{{{2
        self.mpdclient.command_list_ok_begin()
        for item in itemList:
            try:
                self.mpdclient.deleteid(item.song['id'])
            except:
                pass
        self.mpdclient.command_list_end()
        self.view.currentList.setCurrentRow(-1)
        self.view.emit(SIGNAL('playlistChanged()'))
        self.setPlaying(int(self.mpdclient.status().get('song', -1)))

    def __playFromMenu(self):   # {{{2
        self.__playSong(self.view.currentList.selectedItems())

    def __playSong(self, item):#{{{2
        self.mpdclient.playid(self.view.currentList.currentItem().song['id'])
        self.setPlaying(self.view.currentList.row(item))

    def __setPlayTime(self,songTime):#{{{2
        songMin = int(songTime / 60)
        songSecs = songTime - (songMin * 60)
        songHour = int(songMin / 60)
        songMin -= songHour * 60
        songDay = songHour / 24
        songHour -= songDay * 24
        if songHour == 1:
            self.view.playTimeLabel.setText('Total play time: %d day %02d:%02d:%02d ' % (songDay, songHour, songMin, songSecs))
        elif songHour:
            self.view.playTimeLabel.setText('Total play time: %d days %02d:%02d:%02d ' % (songDay, songHour, songMin, songSecs))
        else:
            self.view.playTimeLabel.setText('Total play time: %02d:%02d:%02d ' % (songHour, songMin, songSecs))
        self.currentPlayTime = songTime

    def __setOneLinePlaylist(self, value):#{{{2
        self.config.oneLinePlaylist = value
        self.view.emit(SIGNAL('resetCurrentList()'))
        if value:
            self.view.currentList.setIconSize(QSize(16, 16))
        else:
            self.view.currentList.setIconSize(QSize(32, 32))

    def _setEditing(self, i=0):#{{{2
        self.editing = time()

def doprint(foo='foo'):
    print 'debug: doprint', repr(foo)


# vim: set expandtab shiftwidth=4 softtabstop=4:
