# -*- coding: utf-8 -*-
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
from PyQt4.QtCore import SIGNAL, Qt, QAbstractItemModel, QModelIndex, QMimeData
from PyQt4.QtGui import QIcon
from PyQt4 import uic
from time import time
import cPickle as pickle

import auxilia
import PluginBase
import mpdlibrary

DATA_DIR = ''

def getWidget(view, mpdclient, config, library):
    return FileSystemForm(view, mpdclient, config, library)

class FileSystemForm(PluginBase.PluginBase, auxilia.Actions):
    moduleName = 'F&ileSystem'
    moduleIcon = 'folder-sound'

    def load(self):
        self.fileSystemModel = FileSystemModel(self.library)
        # Load and place the FileSystem form.
        if self.view.KDE:
            uic.loadUi(DATA_DIR+'ui/FileSystemForm.ui', self)
        else:
            uic.loadUi(DATA_DIR+'ui/FileSystemForm.ui.Qt', self)
        self.filesystemTree.setModel(self.fileSystemModel)

        self.view.connect(self.view,SIGNAL('reloadLibrary'),self.reload)
        self.view.connect(self.view,SIGNAL('clearForms'),self.fileSystemModel.clear)

    def reload(self):
        try:
            self.view.setCursor(Qt.WaitCursor)
            t = time()
            self.fileSystemModel.reload()
            print 'load FS took %.3f seconds' % (time() - t)
        finally:
            self.view.setCursor(Qt.ArrowCursor)


class FileSystemModel(QAbstractItemModel):
    file_icon = QIcon(auxilia.PIcon('audio-x-generic'))
    dir_icon = QIcon(auxilia.PIcon('folder-sound'))

    def __init__(self, library):
        QAbstractItemModel.__init__(self)
        self.cache = {}
        self.library = library
        self.root = mpdlibrary.Dir('', self.library)

    def reload(self):
        self.root = mpdlibrary.Dir('', self.library)
        self.reset()

    def clear(self):
        self.root = None
        self.cache = {}
        self.reset()

    def rowCount(self, parent):
        if parent.isValid():
            parent = parent.internalPointer()
            return len(parent)
        else:
            return len(self.root)

    def columnCount(self, parent):
        return 1

    def index(self, row, column, parent):
        if parent.isValid():
            parent = parent.internalPointer()
        else:
            parent = self.root
        return self.createIndex(row, column, parent[row])

    def createIndex(self, row, column, item):
        old = self.cache.get(item._value)
        if old is None:
            self.cache[item._value] = item
        else:
            item = old
        return QAbstractItemModel.createIndex(self, row, column, item)

    def hasChildren(self, index):
        if index.isValid():
            item = index.internalPointer()
        else:
            item = self.root
        return isinstance(item, mpdlibrary.Dir) and len(item) > 0

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()
        item = index.internalPointer()
        parent = item.parent
        if parent == '':
            return QModelIndex()
        row = parent.parent.index(parent)
        return self.createIndex(row, 0, parent)

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return 'File System'

    def flags(self, index):
        defaultFlags = QAbstractItemModel.flags(self, index)
        if index.isValid():
            return Qt.ItemIsDragEnabled | defaultFlags
        else:
            return defaultFlags

    def data(self, index, role):
        if index.isValid():
            item = index.internalPointer()
        else:
            return
        if role == Qt.DisplayRole:
            return unicode(item) or '/'
        if role == Qt.DecorationRole:
            if isinstance(item, mpdlibrary.Dir):
                return self.dir_icon
            else:
                return self.file_icon

    def mimeData(self, indexes):
        items = (index.internalPointer() for index in indexes if index.isValid())
        uri_list = self._getURIs(items)
        uri_list.sort()
        data = QMimeData()
        data.setData('mpd/uri', pickle.dumps(uri_list))
        return data

    def _getURIs(self, items, uri_list=None):
        if uri_list is None:
            uri_list = []
        for item in items:
            if isinstance(item, mpdlibrary.Dir):
                self._getURIs(item, uri_list)
            else:
                uri_list.append(unicode(item.absolute))
        return uri_list

