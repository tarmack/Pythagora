# -*- coding: utf-8 -*-
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
from PyQt4.QtCore import SIGNAL, Qt, QAbstractItemModel, QModelIndex, QMimeData

import cPickle as pickle
import time

import mpdlibrary


class PlaylistsModel(QAbstractItemModel):
    def __init__(self, mpdclient, library):
        QAbstractItemModel.__init__(self)
        self.mpdclient = mpdclient
        self.library = library
        self._playlists = {}
        self._names = []
        self._dates = {}
        self.connect(self, SIGNAL('loadPlaylist'), self._loadPlaylist)
        self.connect(self, SIGNAL('updatePlaylist'), self._updatePlaylist)

    def update(self, playlists):
        '''Reload the lists from the server'''
        for name, date in ((playlist['playlist'], playlist['last-modified']) for playlist in playlists):
            if name not in self._names:
                self.beginInsertRows(QModelIndex(), len(self._names), len(self._names))
                self._names.append(name)
                self.endInsertRows()
            if name in self._playlists and self._modified(name, date):
                self.mpdclient.send('listplaylistinfo', (name,),
                        callback=lambda pl, name=name: self.emit(SIGNAL('updatePlaylist'), name, pl))
            self._dates[name] = time.mktime(time.strptime(date, "%Y-%m-%dT%H:%M:%SZ"))
        if len(playlists) < len(self._names):
            self._names = [name for name in self._names if name in (pl['playlist'] for pl in playlists)]

    def _modified(self, name, date):
        old_date = self._dates.get(name, 0)
        modified = time.mktime(time.strptime(date, "%Y-%m-%dT%H:%M:%SZ"))
        return old_date < modified

    def _updatePlaylist(self, name, songs):
        parent = self.createIndex(self._names.index(name), 0)
        playlist = self._playlists[name]
        self.emit(SIGNAL('layoutAboutToBeChanged()'))
        for pos, song in enumerate(songs):
            if song in playlist[pos:]:
                # song is in there, check position.
                index = pos + playlist[pos:].index(song)
                if index != pos:
                    self.beginMoveRows(parent, index, index, parent, pos)
                    playlist.insert(pos, playlist.pop(index))
                    self.endMoveRows()
            else:
                song = mpdlibrary.Song(song, self.library)
                song.playlist = name
                # New song, insert at the right place.
                self.beginInsertRows(parent, pos, pos)
                playlist.insert(pos, song)
                self.endInsertRows()
        if pos+1 < len(playlist):
            # Some songs have been deleted.
            self.beginRemoveRows(parent, pos+1, len(playlist)-1)
            del playlist[pos+1:]
            self.endRemoveRows()
        self.emit(SIGNAL('layoutChanged()'))

    def hasChildren(self, index):
        if index.isValid():
            item = index.internalPointer()
            return item is None
        else:
            return bool(self._names)

    def canFetchMore(self, parent):
        if parent.isValid():
            item = self._names[parent.row()]
            if item and not item in self._playlists:
                return True
        return False

    def fetchMore(self, parent):
        if parent.isValid():
            name = self._names[parent.row()]
            self._playlists[name] = []
            self.mpdclient.send('listplaylistinfo', (name,),
                    callback=lambda playlist, name=name: self.emit(SIGNAL('loadPlaylist'), name, playlist))

    def _loadPlaylist(self, name, playlist):
        count = len(playlist)
        parent = self.createIndex(self._names.index(name), 0)
        playlist = [mpdlibrary.Song(s, self.library) for s in playlist]
        for song in playlist:
            song.playlist = name
        self.emit(SIGNAL('layoutAboutToBeChanged()'))
        self.beginInsertRows(parent, 0, count-1)
        self._playlists[name] = playlist
        self.endInsertRows()
        self.emit(SIGNAL('layoutChanged()'))

    def clear(self):
        self._playlists = {}
        self._names = []
        self._dates = {}
        self.reset()

    def setData(self, index, value, role):
        if index.isValid() and role == Qt.EditRole and index.column() == 0:
            self.emit(SIGNAL('layoutAboutToBeChanged()'))
            value = unicode(value.toString())
            row = index.row()
            if value == '':
                if self._names[row] == '':
                    self.beginRemoveRows(QModelIndex(), row, row)
                    del self._names[row]
                    self.endRemoveRows()
                    return True
            else:
                old_name = self._names[row]
                if old_name == value:
                    return False
                self._names[row] = value
                if old_name:
                    self._dates[value] = self._dates.pop(old_name)
                    self._playlists[value] = self._playlists.pop(old_name)
                    for song in self._playlists[value]:
                        song.playlist = value
                    self.mpdclient.send('rename', (old_name, value))
                else:
                    self._playlists[value] = []
                index = self.createIndex(row, 0)
                self.emit(SIGNAL('dataChanged(const QModelIndex &, const QModelIndex &)'), index, index)
                return True
            self.emit(SIGNAL('layoutChanged()'))
        return False

    def revert(self):
        while '' in self._names:
            row = self._names.index('')
            self.beginRemoveRows(QModelIndex(), row, row)
            del self._names[row]
            self.endRemoveRows()

    def insertRows(self, row, count, parent):
        if not parent.isValid():
            self.beginInsertRows(QModelIndex(), row, count)
            for row in xrange(row, row+count):
                self._names.insert(row, '')
            self.endInsertRows()
            return True
        return False

    def removeRows(self, row, count, parent):
        if parent.isValid():
            name = parent.internalPointer()
            self.mpdclient.send('command_list_ok_begin')
            try:
                for index in xrange(row, row+count):
                    self.mpdclient.send('playlistdelete', (name, index))
            finally:
                self.mpdclient.send('command_list_end')
        else:
            for name in [self._names[index] for index in xrange(row, row+count)]:
                self.mpdclient.send('rm', (name,))
        return True

    def rowCount(self, parent):
        if parent.isValid():
            name = self._names[parent.row()]
            if name in self._playlists:
                return len(self._playlists[name])
            else:
                return 0
        else:
            return len(self._names)

    def columnCount(self, parent):
        return 4

    def index(self, row, column, parent):
        if parent.isValid():
            name = self._names[parent.row()]
            if name in self._playlists and row < len(self._playlists[name]):
                item = self._playlists[name][row]
                return self.createIndex(row, column, item)
            else:
                return QModelIndex()
        else:
            if 0 <= row < len(self._names):
                item = self._names[row]
                return self.createIndex(row, column)
            else:
                return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()
        item = index.internalPointer()
        if item is None:
            return QModelIndex()
        parent = unicode(item.playlist)
        row = self._names.index(parent)
        return self.createIndex(row, 0)

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                if section == 0:
                    return 'Playlist'
                if section == 1:
                    return 'Artist'
                if section == 2:
                    return 'Title'
                if section == 3:
                    return 'album'
            else:
                return section

    def flags(self, index):
        defaultFlags = QAbstractItemModel.flags(self, index)
        if index.isValid():
            if index.column() == 0:
                return Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled | Qt.ItemIsEditable | defaultFlags
            else:
                return Qt.ItemIsDragEnabled | defaultFlags
        else:
            return Qt.ItemIsDropEnabled | defaultFlags

    def data(self, index, role):
        if not index.isValid():
            return
        item = index.internalPointer()
        if role == Qt.DisplayRole or role == Qt.EditRole:
            column = index.column()
            if item is None:
                if column == 0:
                    return self._names[index.row()]
            else:
                if column == 0:
                    return unicode(index.row())
                if column == 1:
                    return unicode(item.artist)
                if column == 2:
                    return unicode(item.title)
                if column == 3:
                    return unicode(item.album)

    def mimeTypes(self):
        return ['mpd/uri']

    def dropMimeData(self, data, action, row, column, parent):
        if data.hasFormat('mpd/uri'):
            # If the drop ends on an item, that item is the parent.
            # No valid parent == no list == no sigar, too bad.
            if not parent.isValid():
                return False
            # List of uris to add, can be files from the DB or streams or
            # whatever, as long as mpd can add it to a playlist.
            uri_list = pickle.loads(str(data.data('mpd/uri')))
            name = self._names[parent.row()]
            self.mpdclient.send('command_list_ok_begin')
            try:
                for uri in uri_list:
                    self.mpdclient.send('playlistadd', (name, uri))
                if row != -1:
                    length = len(self._playlists[name])
                    for x in xrange(len(uri_list)):
                        self.mpdclient.send('playlistmove', (name, length, row+x))
            finally:
                self.mpdclient.send('command_list_end')
            self.emit(SIGNAL('dataChanged(const QModelIndex &, const QModelIndex &)'), parent, parent)
            return True
        return False

    def mimeData(self, indexes):
        playlists = []
        uri_list = []
        rows_done = []
        for index in sorted((index for index in indexes if index.isValid()), key=lambda i:i.row()):
            row = index.row()
            if not row in rows_done:
                rows_done.append(row)
                item = index.internalPointer()
                if item is None:
                    name = self._names[row]
                    playlists.append(name)
                    for song in self._playlists.get(name):
                        uri_list.append(song.file.absolute)
                else:
                    uri_list.append(item.file.absolute)
        data = QMimeData()
        data.setData('mpd/playlist', pickle.dumps(playlists))
        data.setData('mpd/uri', pickle.dumps(uri_list))
        return data

    @property
    def playlists(self):
        return list(self._names)

    def saveCurrent(self, name):
        if name in self._names:
            self.mpdclient.send('rm', (name,))
        self.mpdclient.send('save', (name,))

