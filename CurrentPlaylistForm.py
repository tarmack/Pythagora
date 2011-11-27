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
from PyQt4.QtCore import SIGNAL, Qt, QSize, QAbstractListModel
from PyQt4.QtGui import QWidget, QInputDialog, QKeySequence, QListWidget, QIcon, QFont
from PyQt4 import uic
from time import time
import httplib

import auxilia
import iconretriever
import mpdlibrary
import streamTools

DATA_DIR = ''

# TODO: See if drag pixmap can be alpha blended. (probably impossible)
# TODO: Make cover art download optional.

#===============================================================================
# List and controls for the currently loaded playlist
#===============================================================================
class CurrentPlaylistForm(QWidget, auxilia.Actions):
    '''List and controls for the currently loaded playlist'''
    updating = False
    editing = 0
    currentPlayTime = 0
    def __init__(self, view, app, mpdclient, library, config):
        QWidget.__init__(self)
        self.app = app
        self.view = view
        self.mpdclient = mpdclient
        self.config = config
        self.library = library
        self.playQueue = PlayQueue(config)
        if self.view.KDE:
            uic.loadUi(DATA_DIR+'ui/CurrentListForm.ui', self)
        else:
            uic.loadUi(DATA_DIR+'ui/CurrentListForm.ui.Qt', self)
        self.view.currentListLayout.addWidget(self)
        self.currentList.setModel(self.playQueue)

        if config.oneLinePlaylist:
            self.oneLinePlaylist.setChecked(True)
            self.currentList.setIconSize(QSize(16, 16))
        else:
            self.currentList.setIconSize(QSize(32, 32))
        self.keepPlayingVisible.setChecked(self.config.keepPlayingVisible)
        self.__togglePlaylistTools(self.config.playlistControls)
        self.version = 0
        self.trackKey = ''
        self.view.connect(self.view, SIGNAL('playlistChanged'), self.reload)
        self.view.connect(self.view, SIGNAL('clearForms'), self.playQueue.clear)
        self.view.connect(self.view, SIGNAL('currentSong'), self.setPlaying)

        # Connect to the list for double click action.
        self.connect(self.currentList,SIGNAL('itemDoubleClicked(QListWidgetItem*)'),self.__playSong)

        self.connect(self.currentFilter,SIGNAL('textEdited(QString)'),self.trackSearch)

        self.connect(self.currentRemove,SIGNAL('clicked()'),self.__removeSelected)
        self.connect(self.currentClear,SIGNAL('clicked()'),self.__clearCurrent)
        self.connect(self.currentSave,SIGNAL('clicked()'),self.__saveCurrent)
        self.connect(self.addStream,SIGNAL('clicked()'),self.__addStream)

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

        # Set the Off icon for the repeat and random buttons.
        icon = self.randomButton.icon()
        icon.addPixmap(
                icon.pixmap(32,32,QIcon.Normal),
                QIcon.Normal,
                QIcon.On)
        icon.addPixmap(
                icon.pixmap(32,32,QIcon.Disabled),
                QIcon.Normal,
                QIcon.Off)
        self.randomButton.setIcon(icon)
        icon = self.repeatButton.icon()
        icon.addPixmap(
                icon.pixmap(32,32,QIcon.Normal),
                QIcon.Normal,
                QIcon.On)
        icon.addPixmap(
                icon.pixmap(32,32,QIcon.Disabled),
                QIcon.Normal,
                QIcon.Off)
        self.repeatButton.setIcon(icon)


    def setPlaying(self, currentsong):
        playing = int(currentsong['pos'])
        print 'debug: setPlaying to ', playing
        self.playQueue.setPlaying(playing)

    def playingItem(self):
        return #self.currentList.item(self.playing)

    def reload(self, plist, status):
        '''Causes the current play list to be reloaded from the server'''
        if not self.config.server:
            return
        version = int(status['playlist'])
        if version <= self.version:
            return
        self.playQueue.update((PlayQueueItem(song, self.library) for song in plist), status)

        # select the songs again if needed.
        #if song.id in self.selection: item.setSelected(True)

        self.view.numSongsLabel.setText(status['playlistlength']+' Songs')
        self.__setPlayTime()

        self.version = version
        self.setPlaying({'pos': status.get('song', -1)})
        key = unicode(self.currentFilter.text())
        if key != '':
            self.trackSearch(key)
        self.currentList.setUpdatesEnabled(True)

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
        itemList = [item.getDrag() for item in itemList]
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
        if not item.iconPath:
            self.retriever.fetchIcon(item, self.config.coverPath)
        self.currentPlayTime += int(item.song.get('time','0'))

    def __resetCurrentList(self):
        self.playQueue.clear()
        self.idlist = []
        self.version = 0
        self.playing = -1
        self.currentPlayTime = 0
        self.view.numSongsLabel.setText('- Songs')
        self.__setPlayTime()

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
        self.emit(SIGNAL('oneLinePlaylist'), value)
        if value:
            self.currentList.setIconSize(QSize(16, 16))
        else:
            self.currentList.setIconSize(QSize(32, 32))

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

    def __addStream(self):
        '''Ask the user for the url of the stream to add.'''
        (url,ok) = QInputDialog.getText(self
                , 'Add Stream'
                , 'Please enter the url of the stream you like to add to the playlist.'
                , 0
                , 'Add Stream')
        url = str(url)
        if ok == True and url:
            adrlist = self._getStream(url)
            self.mpdclient.send('command_list_ok_begin')
            try:
                for address in adrlist:
                    self.mpdclient.send('add', (address,))
            finally:
                self.mpdclient.send('command_list_end')

    def _getStream(self, url):
        data = self._retreiveURL(url)
        if data:
            try:
                if url.endswith('.pls'):
                    adrlist = streamTools._parsePLS(data)
                elif url.endswith('.m3u'):
                    adrlist = streamTools._parseM3U(data)
                elif url.endswith('.xspf'):
                    adrlist = streamTools._parseXSPF(data)
                else:
                    adrlist = [url]
            except streamTools.ParseError:
                return
            return adrlist

    def _retreiveURL(self, url):
        if url.startswith('http://'):
            url = url[7:]
        server, path = url.split('/', 1)
        conn = httplib.HTTPConnection(server)
        conn.request("GET", '/'+path)
        resp = conn.getresponse()
        if resp.status == 200:
            return resp.read()
        else:
            raise httplib.HTTPException('Got bad status code.')

    def _setEditing(self, i=0):
        self.editing = time()


class PlayQueue(QAbstractListModel):
    def __init__(self, config):
        QAbstractListModel.__init__(self)
        self._playing = -1
        self._oneLine = False
        self._songs = []
        self.config = config
        self.retriever = iconretriever.ThreadedRetriever(config.coverPath)

    def setOneLine(self, value):
        if self._oneLine != value:
            self._oneLine = value
            self.emit(SIGNAL('dataChanged(const QModelIndex &, const QModelIndex &)'),
                    self.createIndex(0, 0), self.createIndex(len(self._songs), 0))

    def setPlaying(self, row):
        if self._playing != row:
            self.emit(SIGNAL('dataChanged(const QModelIndex &, const QModelIndex &)'),
                    self.createIndex(self._playing, 0), self.createIndex(self._playing, 0))
            self._playing = row
            self.emit(SIGNAL('dataChanged(const QModelIndex &, const QModelIndex &)'),
                    self.createIndex(self._playing, 0), self.createIndex(self._playing, 0))

    def update(self, plist, status):
        first = len(self._songs)
        last = 0
        for song in plist:
            index = self.id_index(song.id)
            if index:
                first = min(first, index)
                last = max(last, index)
                old = self.pop(index)
                song.iconPath = old.iconPath
            pos = int(song.pos)
            self.insert(pos, song)
            first = min(first, pos)
            last = max(last, pos)
        length = int(status['playlistlength'])
        last = len(self._songs) if length < len(self._songs) else last
        first = min(first, length)
        del self._songs[length:]

        # emit dataChanged(first, last) here.
        self.emit(SIGNAL('dataChanged(const QModelIndex &, const QModelIndex &)'),
                self.createIndex(first, 0), self.createIndex(last, 0))

    def clear(self):
        last = len(self._songs)
        self._songs = []
        self.emit(SIGNAL('dataChanged(const QModelIndex &, const QModelIndex &)'), 
                self.createIndex(0, 0), self.createIndex(0, last))

    def rowCount(self, index):
        return len(self._songs)

    def data(self, index, role):
        row = index.row()
        if role == Qt.DisplayRole:
            return self._getText(row)
        if role == Qt.ToolTipRole:
            return self._getTooltip(row)
        if role == Qt.DecorationRole:
            #print "Data requested DecorationRole, iconPath is: '%s'" % self._songs[row].iconPath
            return QIcon(self._songs[row].iconPath)
        if role == Qt.FontRole:
            font = QFont()
            if row == self._playing:
                font.setBold(True)
            return font
        #return QAbstractListModel.data(self, index, role)

    def _getText(self, index):
        song = self._songs[index]
        if self._playing != int(song.pos) and song.isStream:
            title = song.station
            artist = ''
        else:
            artist = song.artist
            title = song.title
        if self._oneLine:
            return ' - '.join((artist, title))
        else:
            return '\n'.join((title, artist))

    def _getTooltip(self, index):
        song = self._songs[index]
        if song.isStream:
            return "Station:\t %s\nurl:\t %s" % (song.station, song.file)
        else:
            return "Album:\t %s\nTime:\t %s\nFile:\t %s" % (song.album, song.time.human , song.file)

    def id_index(self, id):
        for index, song in enumerate(self._songs):
            if song.id == id:
                return index

    def pop(self, row):
        return self._songs.pop(row)

    def insert(self, row, song):
        song.iconChanged = lambda pos: self.emit(
                SIGNAL('dataChanged(const QModelIndex &, const QModelIndex &)'),
                self.createIndex(pos, 0), self.createIndex(pos, 0))
        self._songs.insert(row, song)
        if not song.iconPath:
            self.retriever.fetchIcon(song)


class PlayQueueItem(mpdlibrary.Song):
    ''' Class that extends the mpdLibrary Song object to catch the setting of `iconPath`.'''
    iconChanged = None
    iconPath = ''
    def __setattr__(self, attr, value):
        if attr == 'iconPath' and value == self.iconPath:
            return
        mpdlibrary.Song.__setattr__(self, attr, value)
        if attr == 'iconPath':
            if self.iconChanged:
                self.iconChanged(int(self.pos))

