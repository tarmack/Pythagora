# -*- coding: utf-8 -*
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
from PyQt4.QtCore import QSize, Qt, SIGNAL, QVariant, QSettings
from PyQt4.QtGui import QIcon, QMessageBox, QFileDialog, QTableWidget, QTableWidgetItem, QLineEdit, QKeySequence, QAction
from PyQt4 import uic
import os.path
import auxilia

DATA_DIR = ''

class Configuration(object):
    types = {
                int: QVariant.toInt,
                bool: QVariant.toBool,
                str: QVariant.toString,
                list: QVariant.toList,
                QSize: QVariant.toSize,
                }
    defaults = {
                'knownHosts':           {'Local': ['localhost','6600','']},
                'server':               ['Local','localhost','6600',''],
                'musicPath':            '~/Music',
                'scBookmarkFile':       '~/Music/shoutcast-bookmarks.xml',
                'showNotification':     False,
                'notificationTimeout':  0,
                'oneLinePlaylist':      False,
                'showShoutcast':        False,
                'tabsIndex':            0,
                'keepPlayingVisible':   False,
                'playlistControls':     False,
                'mgrSize':              QSize(800, 400),
                'mgrSplit':             [400,200],
                'mgrScSplit':           [400,200],
                'libSplit1':            [3,5],
                'libSplit2':            [3,5],
                'playlistSplit':        [5,20],
                'tabOrder':             ['&Library', 'F&ileSystem', '&PlayLists', '&Shoutcast'],
                }

    def __getattr__(self, attr):
        try:
            self.defaults[attr]
        except KeyError:
            raise AttributeError("'%s' object has no attribute '%s'" %
                                 (self.__class__.__name__, attr))
        value = self.__getOption(attr)
        setattr(self, attr, value)
        return value

    def __setattr__(self, attr, value):
        super(Configuration, self).__setattr__(attr, value)
        if attr in self.defaults:
            self.storeOption(attr, value)

    def __getOption(self, option):
        if option == 'knownHosts':
            settings = QSettings()
            hosts = {}
            settings.beginGroup('Servers')
            knownHosts = settings.allKeys()
            if not knownHosts:
                return self.defaults[option]
            for name in knownHosts:
                host = settings.value(name)
                hosts[unicode(name)] = [unicode(col.toString()) for col in host.toList()]
            settings.endGroup()
            return hosts
        valueType = type(self.defaults[option])
        QtType = self.types[valueType]
        value = QtType(QSettings().value(option,self.defaults[option]))
        if not value and value == None:
            return None
        if option == 'tabOrder':
            return [unicode(x.toString()) for x in value]
        if option == 'server':
            return [unicode(col.toString()) for col in value]
        if valueType == list:
            return [int(x.toInt()[0]) for x in value]
        if valueType == int:
            return int(value[0])
        return valueType(value)

    def storeOption(self, option, value):
        try:
            valueType = type(self.defaults[option])
            if option == 'knownHosts':
                settings = QSettings()
                settings.remove("Servers")
                settings.beginGroup('Servers')
                for name, host in value.iteritems():
                    settings.setValue(name, host)
                settings.endGroup()
            elif value == None:
                QSettings().setValue(option, str(value))
            else: QSettings().setValue(option, valueType(value))
        except Exception, e:
            print 'error: ', e, '\n', 'error: ', option, value

    def save(self):
        for option in self.defaults:
            self.storeOption(option, getattr(self, option))

    def showConfiguration(self, parent, modal=False):
        '''Display the configuration dialog and activate the changes.'''
        self.parent = parent
        self.setup = uic.loadUi(DATA_DIR+'ui/Configuration.ui')
        self.setup.setWindowTitle('Pythagora settings')
        self.setup.setWindowIcon(QIcon('Pythagora.png'))
        self.setup.setAttribute(Qt.WA_QuitOnClose, False)

        # Hide dbus options if module not present
        try:
            import dbus
        except ImportError:
            self.setup.showNotificationWidget.setVisible(False)
        self.setup.showNotification.setChecked(self.showNotification)
        self.setup.notificationTimeout.setValue(self.notificationTimeout)

        self.setup.musicPath.setText(self.musicPath)
        self.setup.scBookmarkFile.setText(self.scBookmarkFile)

        # Setup the serverTable.
        actionRemove = QAction(auxilia.PIcon("list-remove"), 'Remove', self.setup.serverTable)
        self.setup.serverTable.addAction(actionRemove)
        self.setup.serverTable.connect(actionRemove, SIGNAL('triggered()'), self.__removeServer)
        self.setup.serverTable.setColumnWidth(0, 160)
        self.setup.serverTable.setColumnWidth(1, 120)
        self.setup.serverTable.setColumnWidth(2, 50)
        try:
            for row, server in enumerate(self.knownHosts):
                self.setup.serverTable.insertRow(row)
                self.setup.serverTable.setItem(row, 0, QTableWidgetItem(server))
                for col, value in enumerate(self.knownHosts[server]):
                    col += 1
                    if col == 3:
                        password = QLineEdit(value)
                        password.setEchoMode(QLineEdit.Password)
                        self.setup.serverTable.setCellWidget(row, col, password)
                    else:
                        self.setup.serverTable.setItem(row, col, QTableWidgetItem(value))
            self.__addServer()
            # Select current server.
            if self.server:
                current = self.setup.serverTable.findItems(self.server[1], Qt.MatchExactly)
                if current:
                    self.setup.serverTable.setCurrentItem(current[0])
        except Exception, e:
            print 'error: problem showing config', e


        self.setup.connect(self.setup.serverTable, SIGNAL('cellChanged(int,int)'), self.__cellChanged)
        self.setup.connect(self.setup.musicDirButton,SIGNAL('clicked()'),self.__selectMusicDir)
        self.setup.connect(self.setup.scFileButton,SIGNAL('clicked()'),self.__selectBookmarkFile)
        self.setup.connect(self.setup.buttonBox, SIGNAL('accepted()'), self.__accept)
        self.setup.serverTable.keyPressEvent = self.__keyPressEvent
        if modal:
            self.setup.exec_()
        else: self.setup.show()

    def __accept(self):
        knownHosts = {}
        for row in xrange(self.setup.serverTable.rowCount()):
            server = self.__getServer(row)
            if server:
                knownHosts.update(server)
        self.knownHosts = knownHosts
        server = self.server
        selection = self.setup.serverTable.selectedItems()
        if selection:
            row = self.setup.serverTable.row(selection[0])
            for name, host in self.__getServer(row).iteritems():
                self.server = [name]+host
        else:
            print 'debug: no server selected'
            self.server = None
        self.showNotification = self.setup.showNotification.isChecked()
        self.notificationTimeout = self.setup.notificationTimeout.value()
        self.musicPath = unicode(self.setup.musicPath.text())
        self.__checkDir("Music",self.musicPath)
        self.scBookmarkFile = unicode(self.setup.scBookmarkFile.text())
        self.__checkDir("ShoutCast bookmarks",unicode(self.scBookmarkFile).rpartition('/')[0])
        if server[1:] != self.server[1:]:
            self.parent.emit(SIGNAL('reconnect()'))

    def __getServer(self, row):
        name = self.setup.serverTable.item(row, 0).text()
        host = [self.setup.serverTable.item(row, col).text() for col in [1, 2]]
        host.append(self.setup.serverTable.cellWidget(row, 3).text())
        if name == '' or host == ['', '', '']:
            return None
        return {unicode(name): [unicode(x) for x in host]}

    def __addServer(self):
        self.setup.serverTable.blockSignals(True)
        row = self.setup.serverTable.rowCount()
        self.setup.serverTable.insertRow(row)
        for col in range(3):
            self.setup.serverTable.setItem(row, col, QTableWidgetItem(''))
        password = QLineEdit()
        password.setEchoMode(QLineEdit.Password)
        self.setup.serverTable.setCellWidget(row, 3, password)
        self.setup.serverTable.blockSignals(False)

    def __keyPressEvent(self, event):
        if event.matches(QKeySequence.Delete):
            self.__removeServer()
        else:
            QTableWidget.keyPressEvent(self.setup.serverTable, event)

    def __removeServer(self):
        selection = self.setup.serverTable.selectedItems()
        if selection:
            row = self.setup.serverTable.row(selection[0])
            self.__cellChanged(row, 0)
            self.setup.serverTable.removeRow(row)

    def __cellChanged(self, row, col):
        if row+1 == self.setup.serverTable.rowCount():
            self.__addServer()
        elif col == 1:
            item = self.setup.serverTable.item(row, 2)
            if item.text() == '':
                item.setText('6600')

    def __checkDir(self,name,dir):
        if not os.path.isdir(os.path.expanduser(str(dir))):
            msgBox = QMessageBox()
            msgBox.setText("%s Directory does not exist" % name)
            msgBox.setInformativeText("Do you wish to create it?")
            msgBox.setStandardButtons(QMessageBox.Yes|QMessageBox.No)
            ret = msgBox.exec_()
            if ret == QMessageBox.Yes:
                os.makedirs(str(dir))

    def __selectMusicDir(self):
        directory = os.path.expanduser(unicode(self.setup.musicPath.text()))
        fd = QFileDialog(self.setup, 'Select: Shared Music Directory', directory)
        fd.setFileMode(QFileDialog.DirectoryOnly)
        #fd.setOption(QFileDialog.DontUseNativeDialog, True)
        if fd.exec_() == 1:
            dir = str(fd.selectedFiles().first())
            self.setup.musicPath.setText(dir)

    def __selectBookmarkFile(self):
        directory = os.path.expanduser(unicode(self.setup.scBookmarkFile.text()))
        fd = QFileDialog(self.setup, 'Select: ShoutCast Bookmark File', directory)
        fd.setNameFilter('XML files (*.xml)')
        fd.setDefaultSuffix('xml')
        #fd.setOption(QFileDialog.DontUseNativeDialog, True)
        if fd.exec_() == 1:
            dir = str(fd.selectedFiles().first())
            self.setup.scBookmarkFile.setText(dir)

