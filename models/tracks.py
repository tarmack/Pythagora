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
from PyQt4.QtCore import Qt, QAbstractItemModel, QModelIndex, QMimeData

import cPickle as pickle


class TracksModel(QAbstractItemModel):
    def __init__(self, library):
        QAbstractItemModel.__init__(self)
        self.library = library
        self._songs = []

    def findRow(self, song):
        return self._songMap[song.file.absolute]

    def reload(self, songs):
        if not hasattr(songs, '__getitem__'):
            songs = list(songs)
        self._songs = songs
        self._songMap = {}
        for index, song in enumerate(self._songs):
            self._songMap[song.file.absolute] = index
        self.reset()

    def data(self, index, role):
        if not index.isValid:
            return
        song = self._songs[index.row()]
        if role == Qt.UserRole:
            return song
        if role == Qt.DisplayRole:
            column = index.column()
            if column == 0:
                return unicode(song.track)
            if column == 1:
                return unicode(song.title)
            if column == 2:
                return song.time.human
        if role == Qt.ToolTipRole:
            return "Artist:\t %s\nAlbum:\t %s\nFile:\t %s" % (song.artist, song.album, song.file)

    def clear(self):
        self._songs = []
        self.reset()

    def rowCount(self, parent):
        return len(self._songs)

    def columnCount(self, parent):
        return 3

    def index(self, row, column, parent):
        if self._songs:
            return self.createIndex(row, column)
        else:
            return QModelIndex()

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == 0:
                return 'Track'
            if section == 1:
                return 'Title'
            if section == 2:
                return 'Time'

    def flags(self, index):
        defaultFlags = QAbstractItemModel.flags(self, index)
        if index.isValid():
            return Qt.ItemIsDragEnabled | defaultFlags
        else:
            return defaultFlags

    def mimeData(self, indexes):
        uri_list = [self._songs[index.row()].file.absolute for index in indexes if index.column() == 0]
        uri_list.sort()
        data = QMimeData()
        data.setData('mpd/uri', pickle.dumps(uri_list))
        return data

