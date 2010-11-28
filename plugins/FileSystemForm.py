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
from PyQt4.QtCore import SIGNAL, Qt
from PyQt4.QtGui import QTreeWidgetItem
from PyQt4 import uic
from time import time
import os

import auxilia
import PluginBase

DATA_DIR = ''

class FileSystemForm(PluginBase.PluginBase, auxilia.Actions):
    moduleName = 'F&ileSystem'
    moduleIcon = 'folder-sound'

    def load(self):
        self.library = None
        # Load and place the FileSystem form.
        if self.view.KDE:
            uic.loadUi(DATA_DIR+'ui/FileSystemForm.ui', self)
        else:
            uic.loadUi(DATA_DIR+'ui/FileSystemForm.ui.Qt', self)

        self.view.connect(self.view,SIGNAL('reloadLibrary'),self.reload)
        self.view.connect(self.view,SIGNAL('clearForms'),self.filesystemTree.clear)

        self.connect(self.filesystemTree, SIGNAL('itemExpanded(QTreeWidgetItem*)'), lambda item: item.loadChildren())

    def reload(self, mpdLibrary):
        try:
            self.view.setCursor(Qt.WaitCursor)
            self.filesystemTree.setUpdatesEnabled(False)
            self.library = mpdLibrary
            t = time()
            self.__loadFileSystemView('/')
            print 'load FS took %.3f seconds' % (time() - t)
        finally:
            self.filesystemTree.setUpdatesEnabled(True)
            self.view.setCursor(Qt.ArrowCursor)



    def __loadFileSystemView(self, path):
        parent = self.filesystemTree.invisibleRootItem()
        self.filesystemTree.clear()
        filelist = self.library.ls(path)
        for name in filelist:
            nextPath = os.path.join(path, name)
            attr = self.library.attributes(nextPath)
            item = FilesystemWidget(name, attr, self.library)
            parent.addChild(item)
        parent.sortChildren(0, 0)

class FilesystemWidget(QTreeWidgetItem):
    '''Widget used in the filesystem tree.'''
    def __init__(self, text, attr, library):
        self.library = library
        QTreeWidgetItem.__init__(self)
        self.setText(0, text)
        if attr == 'file':
            self.setIcon(0, auxilia.PIcon('audio-x-generic'))
        else:
            self.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)
            self.setIcon(0, auxilia.PIcon('folder-sound'))

    def getPath(self, path=''):
        text = unicode(self.text(0))
        if path == '':
            path = text
        else:
            path = os.path.join(text, path)
        parent = self.parent()
        if parent:
            return parent.getPath(path)
        else:
            return path

    def getDrag(self):
        song = self.library.ls(self.getPath())
        if 'file' in song:
            return [song]
        songList = []
        self.loadChildren()
        for i in xrange(self.childCount()):
            child = self.child(i)
            songList.extend(child.getDrag())
        return songList

    def loadChildren(self):
        path = self.getPath()
        filelist = self.library.ls(path)
        for name in filelist:
            nextPath = os.path.join(path, name)
            attr = self.library.attributes(nextPath)
            item = FilesystemWidget(name, attr, self.library)
            self.addChild(item)
        self.sortChildren(0, 0)
        self.loadChildren = lambda : None


def getWidget(view, mpdclient, config):
    return FileSystemForm(view, mpdclient, config)
