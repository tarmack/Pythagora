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
from PyQt4.QtGui import QIcon, QMessageBox, QFileDialog, QTableWidget, QTableWidgetItem, QLineEdit, QKeySequence, QAction, QDialog
import os.path
import auxilia

from ui import Configuration as Configuration_Ui

DATA_DIR = ''

class Configuration(object):
    types = {
                int: QVariant.toInt,
                bool: QVariant.toBool,
                unicode: QVariant.toString,
                list: QVariant.toList,
                QSize: QVariant.toSize,
                }
    defaults = {
                'firstTime':            True,
                'knownHosts':           {u'Local': [u'localhost', u'6600', u'']},
                'server':               [u'Local', u'localhost', u'6600', u''],
                'coverPath':            u'~/Music/covers',
                'showNotification':     False,
                'notificationTimeout':  0,
                'oneLinePlaylist':      False,
                'tabsIndex':            0,
                'keepPlayingVisible':   False,
                'showNumbers':          False,
                'playlistControls':     False,
                'mgrSize':              QSize(800, 400),
                'mgrSplit':             [400,200],
                'mgrScSplit':           [400,200],
                'libSplit1':            [3,5],
                'libSplit2':            [3,5],
                'playlistSplit':        [5,20],
                'tabOrder':             [u'&Library', u'F&ileSystem', u'&PlayLists', u'&Shoutcast'],
                }

    def __getattr__(self, attr):
        try:
            self.defaults[attr]
        except KeyError:
            raise AttributeError("'%s' object has no attribute '%s'" %
                                 (self.__class__.__name__, attr))
        value = self._getOption(attr)
        setattr(self, attr, value)
        return value

    def __setattr__(self, attr, value):
        super(Configuration, self).__setattr__(attr, value)
        if attr in self.defaults:
            self.storeOption(attr, value)

    def _getOption(self, option):
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
                QSettings().setValue(option, unicode(value))
            else: QSettings().setValue(option, valueType(value))
        except Exception, e:
            print 'error: ', e, '\n', 'error: ', option, value

    def save(self):
        for option in self.defaults:
            self.storeOption(option, getattr(self, option))

    def showConfiguration(self, parent, modal=False):
        '''Display the configuration dialog and activate the changes.'''
        self.parent = parent
        self.setup = ConfigDialog(parent)
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
            # Select current server.
            if self.server:
                current = self.setup.serverTable.findItems(self.server[1], Qt.MatchExactly)
                if current:
                    self.setup.serverTable.setCurrentItem(current[0])
        except Exception, e:
            print 'error: problem showing config', e

        # Hide dbus options if the module is not present.
        try:
            __import__('dbus')
        except ImportError:
            self.setup.showNotificationWidget.setVisible(False)
        self.setup.showNotification.setChecked(self.showNotification)
        self.setup.notificationTimeout.setValue(self.notificationTimeout)

        self.setup.coverPath.setText(self.coverPath)

        self.setup.connect(self.setup.buttonBox, SIGNAL('accepted()'), self._accept)
        if modal:
            self.setup.exec_()
        else: self.setup.show()

    def _accept(self):
        knownHosts = {}
        for row in xrange(self.setup.serverTable.rowCount()):
            server = self._getServer(row)
            if server:
                knownHosts.update(server)
        self.knownHosts = knownHosts
        server = self.server
        selection = self.setup.serverTable.selectedItems()
        if selection:
            row = self.setup.serverTable.row(selection[0])
            for name, host in self._getServer(row).iteritems():
                self.server = [name]+host
        else:
            print 'debug: no server selected'
            self.server = None
        self.showNotification = self.setup.showNotification.isChecked()
        self.notificationTimeout = self.setup.notificationTimeout.value()
        self.coverPath = unicode(self.setup.coverPath.text())
        _checkDir("Cover", self.coverPath)
        if server[1:] != self.server[1:]:
            self.parent.emit(SIGNAL('reconnect()'))

    def _getServer(self, row):
        name = self.setup.serverTable.item(row, 0).text()
        host = [self.setup.serverTable.item(row, col).text() for col in [1, 2]]
        host.append(self.setup.serverTable.cellWidget(row, 3).text())
        if name == '' or host == ['', '', '']:
            return None
        return {unicode(name): [unicode(x) for x in host]}


def _checkDir(name, dir):
    if dir and not os.path.isdir(os.path.expanduser(unicode(dir))):
        msgBox = QMessageBox()
        msgBox.setText("%s Directory does not exist" % name)
        msgBox.setInformativeText("Do you wish to create it?")
        msgBox.setStandardButtons(QMessageBox.Yes|QMessageBox.No)
        ret = msgBox.exec_()
        if ret == QMessageBox.Yes:
            os.makedirs(unicode(dir))


class ConfigDialog(QDialog, Configuration_Ui):
    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.setWindowTitle('Pythagora settings')
        self.setWindowIcon(QIcon('Pythagora.png'))
        self.setAttribute(Qt.WA_QuitOnClose, False)

        # Setup the serverTable.
        actionRemove = QAction(auxilia.PIcon("list-remove"), 'Remove', self.serverTable)
        self.serverTable.addAction(actionRemove)
        self.serverTable.connect(actionRemove, SIGNAL('triggered()'), self._removeServer)
        self.serverTable.setColumnWidth(0, 160)
        self.serverTable.setColumnWidth(1, 120)
        self.serverTable.setColumnWidth(2, 50)
        self._addServer()

        self.connect(self.serverTable, SIGNAL('cellChanged(int, int)'), self._cellChanged)
        self.connect(self.coverDirButton,SIGNAL('clicked()'),self._selectCoverDir)
        self.serverTable.keyPressEvent = self._keyPressEvent

    def _selectCoverDir(self):
        directory = os.path.expanduser(unicode(self.coverPath.text()))
        fd = QFileDialog(self, 'Select: Shared Cover Directory', directory)
        fd.setFileMode(QFileDialog.DirectoryOnly)
        if fd.exec_() == 1:
            dir = unicode(fd.selectedFiles().first())
            self.coverPath.setText(dir)

    def _cellChanged(self, row, col):
        if row+1 == self.serverTable.rowCount():
            self._addServer()
        elif col == 1:
            item = self.serverTable.item(row, 2)
            if item and item.text() == '':
                item.setText('6600')

    def _addServer(self):
        self.serverTable.blockSignals(True)
        row = self.serverTable.rowCount()
        self.serverTable.insertRow(row)
        for col in range(3):
            self.serverTable.setItem(row, col, QTableWidgetItem(''))
        password = QLineEdit()
        password.setEchoMode(QLineEdit.Password)
        self.serverTable.setCellWidget(row, 3, password)
        self.serverTable.blockSignals(False)

    def _removeServer(self):
        selection = self.serverTable.selectedItems()
        if selection:
            row = self.serverTable.row(selection[0])
            self._cellChanged(row, 0)
            self.serverTable.removeRow(row)

    def _keyPressEvent(self, event):
        if event.matches(QKeySequence.Delete):
            self._removeServer()
        else:
            QTableWidget.keyPressEvent(self.serverTable, event)

