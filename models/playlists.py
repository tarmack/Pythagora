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
from PyQt4.QtGui import QApplication

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
        playlist = self._playlists[name]._songs
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
            name = self._names[index.row()]
            return name in self._playlists
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
            self._fetchPlaylist(name)

    def _loadPlaylist(self, name, playlist):
        parent = self.createIndex(self._names.index(name), 0)
        playlist = Playlist(name, playlist, self.mpdclient, self.library)
        self.emit(SIGNAL('layoutAboutToBeChanged()'))
        self.beginInsertRows(parent, 0, len(playlist)-1)
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
                    self._playlists[value]._name = value
                    self.mpdclient.send('rename', (old_name, value))
                else:
                    self._playlists[value] = Playlist(value, [], self.mpdclient, self.library)
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
            name = self._names[parent.row()]
            playlist = self._playlists[name]
            del playlist[row, row+count]
        else:
            for name in (self._names[index] for index in xrange(row, row+count)):
                del self[name]
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
                return self.createIndex(row, column, name)
            else:
                return QModelIndex()
        else:
            if 0 <= row < len(self._names):
                return self.createIndex(row, column)
            else:
                return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()
        name = index.internalPointer()
        if name is None:
            return QModelIndex()
        parent = unicode(name)
        try:
            row = self._names.index(parent)
        except ValueError:
            return QModelIndex()
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
        name = index.internalPointer()
        if role == Qt.DisplayRole or role == Qt.EditRole:
            column = index.column()
            if name is None:
                if column == 0:
                    return self._names[index.row()]
            else:
                playlist = self._playlists[name]
                row = index.row()
                if column == 0:
                    return unicode(row)
                if column == 1:
                    return unicode(playlist[row].artist)
                if column == 2:
                    return unicode(playlist[row].title)
                if column == 3:
                    return unicode(playlist[row].album)

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
            if row == -1:
                self._playlists[name].extend(uri_list)
            else:
                self._playlists[name].insert(row, uri_list)
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
                name = index.internalPointer()
                if name is None:
                    name = self._names[row]
                    playlists.append(name)
                    for song in self._playlists.get(name):
                        uri_list.append(song.file.absolute)
                else:
                    playlist = self._playlists[name]
                    song = playlist[row]
                    uri_list.append(song.file.absolute)
        data = QMimeData()
        data.setData('mpd/playlist', pickle.dumps(playlists))
        data.setData('mpd/uri', pickle.dumps(uri_list))
        return data

    def saveCurrent(self, name):
        if name in self._names:
            self.mpdclient.send('rm', (name,))
        self.mpdclient.send('save', (name,))

    def loadPlaylist(self, name):
        self.mpdclient.send('load', (name,))

    def _fetchPlaylist(self, name):
        self.mpdclient.send('listplaylistinfo', (name,),
                callback=lambda playlist, name=name: self.emit(SIGNAL('loadPlaylist'), name, playlist))

    def __iter__(self):
        return self._names.__iter__()

    def __getitem__(self, name):
        try:
            playlist = self._playlists[name]
        except KeyError:
            self._fetchPlaylist(name)
        while not name in self._playlists:
            QApplication().processEvents()
        playlist = self._playlists[name]
        return playlist

    def __delitem__(self, name):
        self.mpdclient.send('rm', (name,))

class Playlist(object):
    def __init__(self, name, songs, mpdclient, library):
        self._name = name
        self._songs = list(songs)
        self._mpdclient = mpdclient
        self._library = library

    def __iter__(self):
        return (mpdlibrary.Song(song, self._library) for song in self._songs)

    def __getitem__(self, index):
        return mpdlibrary.Song(self._songs[index], self._library)

    def __getslice__(self, start, end, step=1):
        return [self[index] for index in xrange(start, end, step)]

    def __setitem__(self, index, song):
        raise NotImplementedError

    def insert(self, index, song):
        length = len(self)
        if isinstance(song, basestring):
            self._mpdclient.send('playlistadd', (self._name, song))
            self._mpdclient.send('playlistmove', (self._name, length, index))
        else:
            self._mpdclient.send('command_list_ok_begin')
            try:
                for uri in reversed(song):
                    self.insert(index, uri)
                    length += 1
            finally:
                self._mpdclient.send('command_list_end')

    def append(self, song):
        if isinstance(song, mpdlibrary.Song):
            song = song.file.absolute
        elif isinstance(song, mpdlibrary.File):
            song = song.absolute
        self._mpdclient.send('playlistadd', (self._name, song))

    def extend(self, songs):
        self._mpdclient.send('command_list_ok_begin')
        try:
            for song in songs:
                self.append(song)
        finally:
            self._mpdclient.send('command_list_end')

    def __delitem__(self, index):
        self._mpdclient.send('playlistdelete', (self._name, index))

    def __delslice__(self, start, end, step=1):
        if start + step == end:
            del self[start]
        else:
            self._mpdclient.send('command_list_ok_begin')
            try:
                for index in reversed(xrange(start, end, step)):
                    del self[index]
            finally:
                self._mpdclient.send('command_list_end')

    def __len__(self):
        return len(self._songs)

