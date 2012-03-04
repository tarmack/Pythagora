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
from PyQt4.QtGui import QWidget

class PluginBase(QWidget):
    """ This is the base class for Pythagora plugins.
    It serves mainly as documentation. But should be inherited to account for
    changes to the interface.

    Your subclass should at least implement the load function to setup its
    display and instantiate variables.

    The music library can be retrieved by connecting to the 'reloadLibrary'
    signal. This signal will provide an instance of mpdlibrary.
    The 'clearForms' signal will be emitted when the data in the forms
    should be discarded, for instance when a new connection is made.
    """
    # moduleName will be shown on the tab of the plugin. You can use '&' to
    # indicate the keyboard shortcut key.
    moduleName = ''
    # moduleIcon should be the name of the icon to show in the tab of the
    # plugin.
    moduleIcon = ''

    def __init__(self, modelManager, view, mpdclient, config, library):
        """ Initiates the plugin providing the view, mpdclient and config
        instances.
        * The view class can be used to connect to signals and emit them if needed.
        * The mpdclient instance can be used to communicate with the mpdserver.
        * The config instance can be used to store configuration and state.
          Please adhere to the philosophy of storing any changes directly.
          QSettings is used as a backend so storing and retrieving settings is
          really cheap.
        """
        QWidget.__init__(self)
        self.modelManager = modelManager
        self.view = view
        self.config = config
        self.mpdclient = mpdclient
        self.library = library
        self.load()
