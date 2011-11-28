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
from PyQt4.QtCore import SIGNAL, Qt, QSize, QAbstractListModel, QModelIndex
from PyQt4.QtGui import QWidget, QInputDialog, QKeySequence, QListView, QIcon, QFont, QSortFilterProxyModel
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
    editing = 0
    def __init__(self, view, app, mpdclient, library, config):
        QWidget.__init__(self)
        self.app = app
        self.view = view
        self.mpdclient = mpdclient
        self.config = config
        self.library = library
        self.playQueue = PlayQueueModel(config)
        if self.view.KDE:
            uic.loadUi(DATA_DIR+'ui/CurrentListForm.ui', self)
        else:
            uic.loadUi(DATA_DIR+'ui/CurrentListForm.ui.Qt', self)
        self.view.currentListLayout.addWidget(self)
        self.playQueueProxy = QSortFilterProxyModel()
        self.playQueueProxy.setSourceModel(self.playQueue)
        self.playQueueProxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.playQueueProxy.setDynamicSortFilter(True)
        self.currentList.setModel(self.playQueueProxy)

        if config.oneLinePlaylist:
            self.oneLinePlaylist.setChecked(True)
            self.currentList.setIconSize(QSize(16, 16))
        else:
            self.currentList.setIconSize(QSize(32, 32))
        self.keepPlayingVisible.setChecked(self.config.keepPlayingVisible)
        self.__togglePlaylistTools(self.config.playlistControls)
        self.trackKey = ''
        self.view.connect(self.view, SIGNAL('playlistChanged'), self.reload)
        self.view.connect(self.view, SIGNAL('clearForms'), self.playQueue.clear)
        self.view.connect(self.view, SIGNAL('currentSong'), self.setPlaying)

        # Connect to the list for double click action.
        self.connect(self.currentList, SIGNAL('doubleClicked(const QModelIndex &)'), self.__playSong)

        self.connect(self.currentFilter,SIGNAL('textEdited(QString)'),self.playQueueProxy.setFilterRegExp)

        self.connect(self.currentRemove,SIGNAL('clicked()'),self.__removeSelected)
        self.connect(self.currentClear,SIGNAL('clicked()'),self.__clearCurrent)
        self.connect(self.currentSave,SIGNAL('clicked()'),self.__saveCurrent)
        self.connect(self.addStream,SIGNAL('clicked()'),self.__addStream)

        self.currentList.dropEvent = self.dropEvent
        self.currentList.dragEnterEvent = self.dragEnterEvent

        # Overload keyPressEvent.
        self.currentList.keyPressEvent = self.keyPressEvent

        self.connect(self.currentBottom, SIGNAL('clicked()'), self.__togglePlaylistTools)
        self.connect(self.currentList,SIGNAL('selectionChanged()'),self._setEditing)
        self.connect(self.currentList.verticalScrollBar(), SIGNAL('valueChanged(int)'), self._setEditing)
        self.connect(self.keepPlayingVisible,SIGNAL('toggled(bool)'),self.__toggleKeepPlayingVisible)
        self.connect(self.oneLinePlaylist,SIGNAL('toggled(bool)'),self.__setOneLinePlaylist)

        # Menu for current playlist.
        # Create actions.
        self.currentMenuPlay = self.action(self.currentList, self.__playSong,
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
        self.playQueue.update((PlayQueueItem(song, self.library) for song in plist), status)
        # TODO: Keep selection correct over updates.

        self.view.numSongsLabel.setText(status['playlistlength']+' Songs')
        self.__setPlayTime(self.playQueue.totalTime())

        self.setPlaying({'pos': status.get('song', -1)})

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.Delete):
            self.__removeSelected()
        elif event.key() == Qt.Key_Escape:
            self.currentList.reset()
        else:
            QListView.keyPressEvent(self.currentList, event)

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

    def _getSelectedRows(self):
        return (self.playQueueProxy.mapToSource(index).row() for index in self.currentList.selectedIndexes())

    def _getSelectedIDs(self):
        return (self.playQueue[row].id for row in self._getSelectedRows())

    def __resetCurrentList(self):
        self.playQueue.clear()
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
        self.__removeSongs(self._getSelectedIDs())

    def __cropCurrent(self):
        selection = set(self._getSelectedRows())
        rows = set(xrange(len(self.playQueue)))
        self.__removeSongs(self.playQueue[row].id for row in (rows - selection))

    def __removeSongs(self, idList):
        self.mpdclient.send('command_list_ok_begin')
        try:
            for id in idList:
                try:
                    self.mpdclient.send('deleteid', (id,))
                except Exception, e:
                    print e
        finally:
            self.mpdclient.send('command_list_end')

    def __playSong(self, index=None):
        if index is not None:
            if hasattr(index, 'row'):
                row = index.row()
            else:
                row = index
            id = self.playQueue[row].id
        else:
            try:
                id = self._getSelectedIDs().next()
            except StopIteration:
                return
        self.mpdclient.send('playid', (id,))

    def __setPlayTime(self, songTime):
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
        self.playQueue.setOneLine(value)
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


class PlayQueueModel(QAbstractListModel):
    def __init__(self, config):
        QAbstractListModel.__init__(self)
        self.version = 0
        self._playing = -1
        self._oneLine = config.oneLinePlaylist
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

    def totalTime(self):
        total = 0
        for song in self._songs:
            total += song.time
        return total

    def update(self, plist, status):
        version = int(status['playlist'])
        if version <= self.version:
            return
        self.version = version
        for song in plist:
            pos = int(song.pos)
            index = self.id_index(song.id)
            if index is not None:
                self.move(index, pos, song)
            else:
                self.insert(pos, song)
        length = int(status['playlistlength'])
        if length < len(self._songs):
            self.beginRemoveRows(QModelIndex(), length, len(self._songs)-1)
            del self._songs[length:]
            self.endRemoveRows()

    def clear(self):
        self.version = 0
        last = len(self._songs)
        self.beginRemoveRows(QModelIndex(), 0, last)
        self._songs = []
        self.endRemoveRows()
        self.reset()

    def rowCount(self, index):
        return len(self._songs)

    def data(self, index, role):
        row = index.row()
        if role == Qt.DisplayRole:
            return self._getText(row)
        if role == Qt.ToolTipRole:
            return self._getTooltip(row)
        if role == Qt.DecorationRole:
            return QIcon(self._songs[row].iconPath)
        if role == Qt.FontRole:
            font = QFont()
            if row == self._playing:
                font.setBold(True)
            return font

    def _getText(self, index):
        song = self._songs[index]
        if self._playing != int(song.pos) and song.isStream:
            return unicode(song.station)
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
        self.beginRemoveRows(QModelIndex(), row, row)
        song = self._songs.pop(row)
        self.endRemoveRows()
        return song

    def insert(self, row, song):
        song.iconChanged = lambda pos: self.emit(
                SIGNAL('dataChanged(const QModelIndex &, const QModelIndex &)'),
                self.createIndex(pos, 0), self.createIndex(pos, 0))
        self.beginInsertRows(QModelIndex(), row, row)
        self._songs.insert(row, song)
        self.endInsertRows()
        if not song.iconPath:
            self.retriever.fetchIcon(song)

    def move(self, old, new, song):
        if old != new:
            self.beginMoveRows(QModelIndex(), old, old, QModelIndex(), new)
        song.iconPath = self._songs.pop(old).iconPath
        song.iconChanged = lambda pos: self.emit(
                SIGNAL('dataChanged(const QModelIndex &, const QModelIndex &)'),
                self.createIndex(pos, 0), self.createIndex(pos, 0))
        self._songs.insert(new, song)
        if old != new:
            self.endMoveRows()
        else:
            self.emit(SIGNAL('dataChanged(const QModelIndex &, const QModelIndex &)'),
                self.createIndex(new, 0), self.createIndex(new, 0))

    def __len__(self):
        return self._songs.__len__()

    def __getslice__(self, start, end):
        return self._songs.__getslice__(start, end)

    def __setslice__(self, start, end, songs):
        length = len(self._songs)
        if end < length:
            self._songs.__setslice__(start, end, songs)
            self.emit(SIGNAL('dataChanged(const QModelIndex &, const QModelIndex &)'),
                self.createIndex(start, 0), self.createIndex(end, 0))
        elif start > length:
            self.beginInsertRows(QModelIndex(), start, end)
            self._songs.__setslice__(start, end, songs)
            self.endInsertRows()
        else:
            self.__setslice__(start, length-1, songs[:length-1 - start])
            self.__setslice__(length, end, songs[length - start:])

    def __delslice__(self, start, end):
        if end >= len(self._songs):
            end = len(self._songs)
        self.beginRemoveRows(QModelIndex(), start, end)
        self._songs.__delslice(start, end)
        self.endRemoveRows()

    def __getitem__(self, index):
        return self._songs.__getitem__(index)

    def __setitem__(self, index, song):
        self._songs.__setitem__(index, song)
        self.emit(SIGNAL('dataChanged(const QModelIndex &, const QModelIndex &)'),
            self.createIndex(index, 0), self.createIndex(index, 0))

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


