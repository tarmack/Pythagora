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
from ui import FileSystemForm

import PluginBase

DATA_DIR = ''

def getWidget(modelManager, mpdclient, config, library):
    return FileSystemForm(modelManager, mpdclient, config, library)

class FileSystemForm(PluginBase.PluginBase, FileSystemForm):
    moduleName = 'F&ileSystem'
    moduleIcon = 'folder-sound'

    def load(self):
        self.fileSystemModel = self.modelManager.fileSystem
        # Load and place the FileSystem form.
        self.setupUi(self)
        self.filesystemTree.setModel(self.fileSystemModel)

