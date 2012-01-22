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
from PyQt4.QtGui import QWidget, QInputDialog, QKeySequence, QListView, QIcon, QFont, QSortFilterProxyModel, QStyledItemDelegate
from PyQt4 import uic
from time import time
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
        self.playQueueDelegate = PlayQueueDelegate(self.config)
        if self.view.KDE:
            uic.loadUi(DATA_DIR+'ui/CurrentListForm.ui', self)
        else:
            uic.loadUi(DATA_DIR+'ui/CurrentListForm.ui.Qt', self)
        self.view.currentListLayout.addWidget(self)
        self.playQueueProxy = QSortFilterProxyModel()
        self.playQueueProxy.setSourceModel(self.playQueue)
        self.playQueueProxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.playQueueProxy.setDynamicSortFilter(True)
        self.playQueueProxy.setFilterRole(Qt.AccessibleTextRole)
        self.currentList.setModel(self.playQueueProxy)
        self.currentList.setItemDelegateForColumn(0, self.playQueueDelegate)

        if config.oneLinePlaylist:
            self.oneLinePlaylist.setChecked(True)
            self.currentList.setIconSize(QSize(16, 16))
        else:
            self.currentList.setIconSize(QSize(32, 32))
        self.keepPlayingVisible.setChecked(self.config.keepPlayingVisible)
        self._togglePlaylistTools(self.config.playlistControls)
        self.view.connect(self.view, SIGNAL('playlistChanged'), self.reload)
        self.view.connect(self.view, SIGNAL('clearForms'), self.playQueue.clear)
        self.view.connect(self.view, SIGNAL('currentSong'), self.setPlaying)

        # Connect to the view for double click action.
        self.connect(self.currentList, SIGNAL('doubleClicked(const QModelIndex &)'), self._playSong)

        self.connect(self.currentFilter,SIGNAL('textEdited(QString)'),self.playQueueProxy.setFilterFixedString)

        self.connect(self.currentRemove,SIGNAL('clicked()'),self._removeSelected)
        self.connect(self.currentClear,SIGNAL('clicked()'),self._clearCurrent)
        self.connect(self.currentSave,SIGNAL('clicked()'),self._saveCurrent)
        self.connect(self.addStream,SIGNAL('clicked()'),self._addStream)

        self.connect(self.currentBottom, SIGNAL('clicked()'), self._togglePlaylistTools)
        self.connect(self.currentList,SIGNAL('selectionChanged()'),self._setEditing)
        self.connect(self.currentList.verticalScrollBar(), SIGNAL('valueChanged(int)'), self._setEditing)
        self.connect(self.keepPlayingVisible,SIGNAL('toggled(bool)'),self._toggleKeepPlayingVisible)
        self.connect(self.oneLinePlaylist,SIGNAL('toggled(bool)'),self._setOneLinePlaylist)

        # Menu for current playlist.
        # Create actions.
        self.currentMenuPlay = self.action(self.currentList, self._playSong,
                icon="media-playback-start", text='play', tooltip='Start playing the selected song.')
        self.currentMenuRemove = self.action(self.currentList, self._removeSelected,
                icon="list-remove", text='Remove', tooltip="Remove the selected songs from the playlist.")
        self.currentMenuClear = self.action(self.currentList, self._clearCurrent,
                icon="document-new", text='Clear', tooltip="Remove all songs from the playlist.")
        self.currentMenuSave = self.action(self.currentList, self._saveCurrent,
                icon="document-save-as", text='Save', tooltip="Save the current playlist.")
        self.currentMenuCrop = self.action(self.currentList, self._cropCurrent,
                icon="project-development-close", text='Crop', tooltip="Remove all but the selected songs.")

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

    def reload(self, plist, status):
        '''Causes the current play list to be reloaded from the server'''
        if not self.config.server:
            return
        self.playQueue.update((mpdlibrary.Song(song, self.library) for song in plist), status)

        self.view.numSongsLabel.setText(status['playlistlength']+' Songs')
        self._setPlayTime(self.playQueue.totalTime())

        self.setPlaying({'pos': status.get('song', -1)})

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.Delete):
            self._removeSelected()
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
        top = self.currentList.rectForIndex(playing).top()
        height = self.currentList.viewport().height()
        new_pos = top - (height / 8)
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

    def _clearCurrent(self):
        '''Clear the current playlist'''
        self.mpdclient.send('stop')
        self.mpdclient.send('clear')

    def _removeSelected(self):
        '''Remove the selected item(s) from the current playlist'''
        self._removeSongs(self._getSelectedIDs())

    def _cropCurrent(self):
        selection = set(self._getSelectedRows())
        rows = set(xrange(len(self.playQueue)))
        self._removeSongs(self.playQueue[row].id for row in (rows - selection))

    def _removeSongs(self, idList):
        self.mpdclient.send('command_list_ok_begin')
        try:
            for id in idList:
                try:
                    self.mpdclient.send('deleteid', (id,))
                except Exception, e:
                    print e
        finally:
            self.mpdclient.send('command_list_end')

    def _playSong(self, index=None):
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

    def _toggleKeepPlayingVisible(self, value):
        self.config.keepPlayingVisible = value
        if value:
            self._ensurePlayingVisable()

    def _setOneLinePlaylist(self, value):
        self.config.oneLinePlaylist = value
        self.playQueueDelegate.oneLine = value
        if value:
            self.currentList.setIconSize(QSize(16, 16))
        else:
            self.currentList.setIconSize(QSize(32, 32))

    def _togglePlaylistTools(self, value=None):
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

    def _addStream(self):
        '''Ask the user for the url of the stream to add.'''
        (url,ok) = QInputDialog.getText(self
                , 'Add Stream'
                , 'Please enter the url of the stream you like to add to the playlist.'
                , 0
                , 'Add Stream')
        url = str(url)
        if ok == True and url:
            try:
                adrlist = streamTools.getStreamList(url)
            except streamTools.ParseError:
                print 'error: Could not parse stream address.'
                return
            self.mpdclient.send('command_list_ok_begin')
            try:
                for address in adrlist:
                    self.mpdclient.send('add', (address,))
            finally:
                self.mpdclient.send('command_list_end')

    def _setEditing(self):
        self.playQueue.lastEdit = time()


class PlayQueueModel(QAbstractListModel):
    '''
    A model of the mpd playqueue for use in the Qt model/view framework.
    '''
    def __init__(self, mpdclient, config):
        QAbstractListModel.__init__(self)
        self.lastEdit = time()
        self.version = 0
        self.playing = -1
        self._oneLine = config.oneLinePlaylist
        self._songs = []
        self._id_list = []
        self._changes = []
        self.mpdclient = mpdclient
        self.config = config
        self.retriever = iconretriever.ThreadedRetriever(config.coverPath)

    def setPlaying(self, row):
        '''
        Sets the currently playing song to `row` and makes sure the view
        reads this change.
        '''
        if self.playing != row:
            self.emit(SIGNAL('dataChanged(const QModelIndex &, const QModelIndex &)'),
                    self.createIndex(self.playing, 0), self.createIndex(self.playing, 0))
            self.playing = row
            self.emit(SIGNAL('dataChanged(const QModelIndex &, const QModelIndex &)'),
                    self.createIndex(self.playing, 0), self.createIndex(self.playing, 0))

    def totalTime(self):
        ''' Returns the total play time of all songs in the queue. '''
        total = 0
        for song in self._songs:
            total += song.time
        return total

    def update(self, plist, status):
        ''' Updates the playqueue model with the changes in `plist`. '''
        version = int(status['playlist'])
        if version <= self.version:
            return
        self.version = version
        clist = []
        change = None
        for song in plist:
            pos = int(song.pos)
            song_id = int(song.id)
            index = self.id_index(song_id)
            if index is not None:
                if change != 'move' or (clist and not (index-1 == clist[-1][0] and pos-1 == clist[-1][1])):
                    self._runCList(change, clist)
                    change = 'move'
                    clist = []
                    index = self.id_index(int(song.id))
                clist.append((index, pos, song))
            else:
                if change != 'insert' or (clist and not pos-1 == clist[-1][0]):
                    self._runCList(change, clist)
                    change = 'insert'
                    clist = []
                clist.append((pos, song))
        self._runCList(change, clist)
        length = int(status['playlistlength'])
        if length < len(self._songs):
            del self[length:]

    def _runCList(self, change, clist):
        ''' Applies the changes from `clist` according to `change`. '''
        if change is None or not clist:
            return
        if change == 'move':
            destination = clist[0][1]
            if not self.beginMoveRows(QModelIndex(), clist[0][0], clist[-1][0], QModelIndex(), destination):
                # destination is part of the move operation. Just update the song.
                for index, _, song in clist:
                    old_song = self._songs[index]
                    self._songs[index] = self._updateSong(old_song, song)
            else:
                correction = 0
                for index, _, song in clist:
                    old_song = self._popSong(index - correction)
                    self._insertSong(destination, self._updateSong(old_song, song))
                    if destination > index:
                        correction += 1
                    else:
                        destination += 1
                self.endMoveRows()
            if not old_song == song:
                self.emit(SIGNAL('dataChanged(const QModelIndex &, const QModelIndex &)'),
                        self.createIndex(destination, 0), self.createIndex(destination, 0))
        elif change == 'insert':
            self.beginInsertRows(QModelIndex(), clist[0][0], clist[-1][0])
            for pos, song in clist:
                song.iconPath = ''
                song.icon = None
                self.retriever.fetchIcon(song)
                self._insertSong(pos, song)
            self.endInsertRows()

    def _updateSong(self, old_song, new_song):
        ''' Updates the song info if they do not match. Preserves fetched icons. '''
        new_song.iconPath = old_song.iconPath
        new_song.icon = old_song.icon
        if not new_song.iconPath:
            self.retriever.fetchIcon(new_song)
        return new_song

    def _popSong(self, pos):
        ''' Pops a song from the list keeping the id_list correct. '''
        del self._id_list[pos]
        return self._songs.pop(pos)

    def _insertSong(self, pos, song):
        ''' Inserts a song in the list keeping the id_list correct. '''
        self._songs.insert(pos, song)
        self._id_list.insert(pos, int(song.id))

    def clear(self):
        ''' Clears the playqueue and resets the views. '''
        self.version = 0
        self._songs = []
        self._id_list = []
        self.reset()

    def supportedDropActions(self):
        ''' Returns the drop actions supported by this model. '''
        return Qt.MoveAction|Qt.CopyAction

    def supportedDragActions(self):
        ''' Returns the actions that can be applied to items dragged from this model. '''
        return Qt.MoveAction

    def mimeTypes(self):
        ''' Returns the MIME types items dragged form this model get supplied with. '''
        return ['mpd/playqueue_id', 'mpd/uri']

    def mimeData(self, indexes):
        ''' Encodes the data for the items in indexes in MIME types for drag and drop actions. '''
        row_list = [index.row() for index in indexes]
        row_list.sort()
        if len(row_list) == 0:
            return 0
        data = QMimeData()
        data.setData('mpd/playqueue_id', pickle.dumps([(row, int(self._songs[row].id)) for row in row_list]))
        data.setData('mpd/uri', pickle.dumps([self._songs[row].file.absolute for row in row_list]))
        return data

    def dropMimeData(self, data, action, row, column, parent):
        ''' Decodes the MIME data from a drop and inserts the items in the mod playqueue. '''
        self.lastEdit = time()
        if row == -1:
            row = len(self._songs)
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
        elif data.hasFormat('mpd/uri'):
            # List of uris to add, can be files from the DB or streams or
            # whatever, as long as mpd can add it to the play queue. 
            uri_list = pickle.loads(str(data.data('mpd/uri')))
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
        ''' Removes the item at `row` in the model from the playqueue. '''
        self.lastEdit = time()
        self.mpdclient.send('delete', (row))

    def removeRows(self, row, count, parent):
        ''' Removes `count` items starting at `row` from the mpd playqueue. '''
        self.lastEdit = time()
        self.mpdclient.send('command_list_ok_begin')
        try:
            for x in xrange(count):
                self.mpdclient.send('delete', (row))
        finally:
            self.mpdclient.send('command_list_end')

    def rowCount(self, index):
        ''' Returns the number of songs in the model. '''
        return len(self._songs)

    def data(self, index, role):
        ''' Returns the data at `index` for the requested `role`. '''
        row = index.row()
        if role == Qt.DisplayRole:
            song = self._songs[row]
            if row != self.playing and song.isStream:
                return [unicode(song.station), '']
            else:
                return [unicode(song.artist), unicode(song.title)]
        if role == Qt.ToolTipRole:
            return self._getTooltip(row)
        if role == Qt.DecorationRole:
            song = self._songs[row]
            if song.iconPath:
                if not song.icon:
                    song.icon = QIcon(song.iconPath)
                return song.icon
            else:
                return None
        if role == Qt.FontRole:
            font = QFont()
            if row == self.playing:
                font.setBold(True)
            return font
        if role == Qt.AccessibleTextRole:
            song = self._songs[row]
            if row != self.playing and song.isStream:
                return unicode(song.station)
            else:
                return '%s by %s' % (unicode(song.title), unicode(song.artist))


    def _getTooltip(self, index):
        ''' Returns the text that should be used for the tooltip of the item at `index`. '''
        song = self._songs[index]
        if song.isStream:
            return "Station:\t %s\nurl:\t %s" % (song.station, song.file.absolute)
        else:
            return "Album:\t %s\nTime:\t %s\nFile:\t %s" % (song.album, song.time.human , song.file.absolute)

    def id_index(self, id):
        ''' Returns the index in the playqueue for the song with `id`. '''
        try:
            return self._id_list.index(int(id))
        except ValueError:
            return None

    def __len__(self):
        return self._songs.__len__()

    def __getslice__(self, start, end):
        return self._songs.__getslice__(start, end)

    def __delslice__(self, start, end):
        ''' Removes multiple items from the view. '''
        if not end or end >= len(self._songs):
            end = len(self._songs)
        self.beginRemoveRows(QModelIndex(), start, end)
        self._songs.__delslice__(start, end)
        self._id_list.__delslice__(start, end)
        self.endRemoveRows()

    def __getitem__(self, index):
        return self._songs.__getitem__(index)


class PlayQueueDelegate(QStyledItemDelegate):
    ''' Delegate for the playqueue view. This delegate is used to switch between different display styles. '''
    def __init__(self, config):
        QStyledItemDelegate.__init__(self)
        self.config = config
        self.oneLine = config.oneLinePlaylist

    def displayText(self, value, locale):
        ''' Returns the text as it should be displayed for the item. '''
        value = value.toStringList()
        artist = unicode(value[0])
        title = unicode(value[1])
        if self.oneLine:
            text = ' - '.join((artist, title))
        else:
            text = '\n'.join((title, artist))
        return QStyledItemDelegate.displayText(self, text, locale)

