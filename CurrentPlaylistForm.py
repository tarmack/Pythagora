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
from PyQt4.QtCore import SIGNAL, Qt, QSize, QAbstractListModel, QModelIndex, QMimeData
from PyQt4.QtGui import QWidget, QInputDialog, QKeySequence, QListView, QIcon, QFont, QSortFilterProxyModel
from PyQt4 import uic
from time import time
import httplib
import cPickle as pickle

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
        self.playQueue = PlayQueueModel(mpdclient, config)
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
        self.view.connect(self.view, SIGNAL('playlistChanged'), self.reload)
        self.view.connect(self.view, SIGNAL('clearForms'), self.playQueue.clear)
        self.view.connect(self.view, SIGNAL('currentSong'), self.setPlaying)

        # Connect to the view for double click action.
        self.connect(self.currentList, SIGNAL('doubleClicked(const QModelIndex &)'), self.__playSong)

        self.connect(self.currentFilter,SIGNAL('textEdited(QString)'),self.playQueueProxy.setFilterRegExp)

        self.connect(self.currentRemove,SIGNAL('clicked()'),self.__removeSelected)
        self.connect(self.currentClear,SIGNAL('clicked()'),self.__clearCurrent)
        self.connect(self.currentSave,SIGNAL('clicked()'),self._saveCurrent)
        self.connect(self.addStream,SIGNAL('clicked()'),self.__addStream)

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
        self.currentMenuSave = self.action(self.currentList, self._saveCurrent,
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
        if playing != self.playQueue.playing:
            self._ensurePlayingVisable()
        self.playQueue.setPlaying(playing)

    def playingItem(self):
        return self.playQueue.playingSong()

    def reload(self, plist, status):
        '''Causes the current play list to be reloaded from the server'''
        if not self.config.server:
            return
        self.playQueue.update((PlayQueueItem(song, self.library) for song in plist), status)
        # TODO: Keep selection correct over updates.

        self.view.numSongsLabel.setText(status['playlistlength']+' Songs')
        self._setPlayTime(self.playQueue.totalTime())

        self.setPlaying({'pos': status.get('song', -1)})

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.Delete):
            self.__removeSelected()
        elif event.key() == Qt.Key_Escape:
            self.currentList.reset()
        else:
            QListView.keyPressEvent(self.currentList, event)

    def _getSelectedRows(self):
        return (self.playQueueProxy.mapToSource(index).row() for index in self.currentList.selectedIndexes())

    def _getSelectedIDs(self):
        return (self.playQueue[row].id for row in self._getSelectedRows())

    def _resetCurrentList(self):
        self.playQueue.clear()
        self.view.numSongsLabel.setText('- Songs')
        self._setPlayTime()

    def _ensurePlayingVisable(self):
        if time() - self.playQueue.lastEdit <= 5:
            return
        playing = self.playQueueProxy.mapFromSource(self.playQueue.createIndex(self.playQueue.playing, 0))
        if self.currentList.isIndexHidden(playing):
            return
        bottom = self.currentList.rectForIndex(playing).bottom()
        height = self.currentList.viewport().height()
        new_pos = bottom - (height / 8)
        scrollBar = self.currentList.verticalScrollBar()
        scrollBar.setValue(new_pos)

    def _saveCurrent(self):
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

    def _setPlayTime(self, playTime=0):
        self.view.playTimeLabel.setText('Total play time: %s' % auxilia.formatTime(playTime))

    def __toggleKeepPlayingVisible(self, value):
        self.config.keepPlayingVisible = value
        if value:
            self._ensurePlayingVisable()

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

    def _setEditing(self):
        self.playQueue.lastEdit = time()


class PlayQueueModel(QAbstractListModel):
    def __init__(self, mpdclient, config):
        QAbstractListModel.__init__(self)
        self.lastEdit = time()
        self.version = 0
        self.playing = -1
        self._oneLine = config.oneLinePlaylist
        self._songs = []
        self.mpdclient = mpdclient
        self.config = config
        self.retriever = iconretriever.ThreadedRetriever(config.coverPath)

    def setOneLine(self, value):
        if self._oneLine != value:
            self._oneLine = value
            self.emit(SIGNAL('dataChanged(const QModelIndex &, const QModelIndex &)'),
                    self.createIndex(0, 0), self.createIndex(len(self._songs), 0))

    def setPlaying(self, row):
        if self.playing != row:
            self.emit(SIGNAL('dataChanged(const QModelIndex &, const QModelIndex &)'),
                    self.createIndex(self.playing, 0), self.createIndex(self.playing, 0))
            self.playing = row
            self.emit(SIGNAL('dataChanged(const QModelIndex &, const QModelIndex &)'),
                    self.createIndex(self.playing, 0), self.createIndex(self.playing, 0))

    def totalTime(self):
        total = 0
        for song in self._songs:
            total += song.time
        return total

    def playingSong(self):
        return self._songs[self.playing]

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

    def supportedDropActions(self):
        return Qt.MoveAction|Qt.CopyAction

    def supportedDragActions(self):
        return Qt.MoveAction

    def mimeTypes(self):
        return ['mpd/playqueue_id']

    def mimeData(self, indexes):
        id_list = [(index.row(), int(self._songs[index.row()].id)) for index in indexes]
        id_list.sort()
        if len(id_list) == 0:
            return 0
        data = QMimeData()
        data.setData('mpd/playqueue_id', pickle.dumps(id_list))
        return data

    def dropMimeData(self, data, action, row, column, parent):
        self.lastEdit = time()
        if row == -1:
            row = len(self._songs)-1
        if data.hasFormat('mpd/playqueue_id'):
            # Moving inside the play queue.
            id_list = pickle.loads(str(data.data('mpd/playqueue_id')))
            self.mpdclient.send('command_list_ok_begin')
            try:
                for old_pos, id in reversed(id_list):
                    if old_pos < row:
                        row -= 1
                    self.mpdclient.send('moveid', (id, row))
            finally:
                self.mpdclient.send('command_list_end')
            return True
        elif data.hasFormat('mpd/uri_list'):
            # List of uris to add, can be files from the DB or streams or
            # whatever, as long as mpd can add it to the play queue. 
            uri_list = pickle.loads(str(data.data('mpd/uri_list')))
            self.mpdclient.send('command_list_ok_begin')
            try:
                for uri in reversed(uri_list):
                    self.mpdclient.send('addid', (uri, row))
            finally:
                self.mpdclient.send('command_list_end')
            return True
        print 'debug: Drop on currentlist failed.'
        return False

    def flags(self, index):
        defaultFlags = QAbstractListModel.flags(self, index)
        if index.isValid() and index.column() == 0:
            return Qt.ItemIsDragEnabled | defaultFlags
        else:
            return Qt.ItemIsDropEnabled | defaultFlags

    def removeRow(self, row, parent):
        self.lastEdit = time()
        self.mpdclient.send('delete', (row))

    def removeRows(self, row, count, parent):
        self.lastEdit = time()
        self.mpdclient.send('command_list_ok_begin')
        try:
            for x in xrange(count):
                self.mpdclient.send('delete', (row))
        finally:
            self.mpdclient.send('command_list_end')

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
            if row == self.playing:
                font.setBold(True)
            return font

    def _getText(self, index):
        song = self._songs[index]
        if self.playing != int(song.pos) and song.isStream:
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

    def __delslice__(self, start, end):
        if end >= len(self._songs):
            end = len(self._songs)
        self.beginRemoveRows(QModelIndex(), start, end)
        self._songs.__delslice(start, end)
        self.endRemoveRows()

    def __getitem__(self, index):
        return self._songs.__getitem__(index)


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


