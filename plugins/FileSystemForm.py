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
from PyQt4 import uic
from time import time

import auxilia
import PluginBase
from models import FileSystemModel

DATA_DIR = ''

def getWidget(view, mpdclient, config, library):
    return FileSystemForm(view, mpdclient, config, library)

class FileSystemForm(PluginBase.PluginBase, auxilia.Actions):
    moduleName = 'F&ileSystem'
    moduleIcon = 'folder-sound'

    def load(self):
        self.fileSystemModel = FileSystemModel(self.library)
        # Load and place the FileSystem form.
        uic.loadUi(DATA_DIR+'ui/FileSystemForm.ui', self)
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

