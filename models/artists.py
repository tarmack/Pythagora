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
from PyQt4.QtCore import Qt, QAbstractListModel, QMimeData

import cPickle as pickle


class ArtistsModel(QAbstractListModel):
    def __init__(self, library):
        QAbstractListModel.__init__(self)
        self.library = library
        self._artists = []

    def reload(self, artists):
        self._artists = list(artists)
        self.reset()

    def data(self, index, role):
        if not index.isValid:
            return
        artist = index.internalPointer()
        if role == Qt.DisplayRole:
            return unicode(artist)

    def clear(self):
        self._artists = []
        self.reset()

    def rowCount(self, parent):
        return len(self._artists)

    def index(self, row, column, parent):
        return self.createIndex(row, column, self._artists[row])

    def flags(self, index):
        defaultFlags = QAbstractListModel.flags(self, index)
        if index.isValid():
            return Qt.ItemIsDragEnabled | defaultFlags
        else:
            return defaultFlags

    def mimeData(self, indexes):
        artists = (index.internalPointer() for index in indexes if index.isValid())
        uri_list = []
        for artist in artists:
            uri_list.extend(song.file.absolute for song in artist.songs)
        uri_list.sort()
        data = QMimeData()
        data.setData('mpd/uri', pickle.dumps(uri_list))
        return data

