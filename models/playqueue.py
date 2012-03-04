# -*- coding: utf-8 -*
#-------------------------------------------------------------------------------
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
from PyQt4.QtCore import SIGNAL, Qt, QAbstractListModel, QModelIndex, QMimeData
from PyQt4.QtGui import QIcon, QFont

import cPickle as pickle
from time import time

import mpdlibrary
import iconretriever


class PlayQueueModel(QAbstractListModel):
    '''
    A model of the mpd playqueue for use in the Qt model/view framework.
    '''
    def __init__(self, mpdclient, config):
        QAbstractListModel.__init__(self)
        self.lastEdit = time()
        self._boldFont = QFont()
        self._boldFont.setBold(True)
        self._stdFont = QFont()
        self.playing = -1
        self.clear()
        self._oneLine = config.oneLinePlaylist
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
        ''' Updates the playqueue model with the changes in `plist`.
            Returns True if the last thing done is adding to the end.'''
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
        return change == 'insert'

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
        self._iconChanges = 0
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
            #print "DecorationRole for row:", row
            song = self._songs[row]
            if song.iconPath:
                if not song.icon:
                    song.icon = QIcon(song.iconPath)
                return song.icon
            else:
                return None
        if role == Qt.FontRole:
            if row == self.playing:
                return self._boldFont
            else:
                return self._stdFont
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


class PlayQueueSong(mpdlibrary.Song):
    def __new__(cls, song, library, parent):
        return mpdlibrary.Song.__new__(cls, song, library)

    def __init__(self, song, library, parent):
        mpdlibrary.Song.__init__(self, song, library)
        self.parent = parent

    def setIcon(self, iconPath):
        self.iconPath = iconPath
        #self.parent.newIcon()
        index = int(self.pos)
        self.parent.emit(SIGNAL('dataChanged(const QModelIndex &, const QModelIndex &)'),
                self.parent.createIndex(index, 0), self.parent.createIndex(index, 0))

