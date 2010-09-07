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
from PyQt4.QtCore import SIGNAL, QTimer
from PyQt4.QtGui import QMainWindow, QSystemTrayIcon, QLabel, QMenu, QIcon, QWidget
from PyQt4 import uic
from time import time
import sys

import CurrentPlaylistForm
import ShoutcastForm
import PlaylistForm
import LibraryForm
import auxilia
import songwidgets

try:
    if "--nokde" not in sys.argv:
        from PyKDE4.kdeui import KWindowSystem, NET
        KDE = True
    else: KDE = False
except ImportError:
    KDE = False

# TODO: Make window show if minimized when trayicon is clicked.
#       ^ Probably impossible ^ (maybe just hard when compositing with windowpreviews is enabled)
# TODO: Make splitter sizes of not shown parts be rememberd correctly.

class View(QMainWindow, auxilia.Actions):
    def __init__(self, configuration, mpdclient, app):
        QMainWindow.__init__(self)
        self.app = app
        self.focus = time()
        self.shuttingDown = False
        self.config = configuration
        self.mpdclient = mpdclient
        appIcon = QIcon('icons/Pythagora.png')
        try:
            if KDE:
                uic.loadUi('Pythagora.ui', self)
            else: raise
        except:
            uic.loadUi('Pythagora.ui.Qt', self)
        self.KDE = KDE
        self.setWindowTitle('Pythagora')
        self.setWindowIcon(appIcon)
        # Create 'MDP' menu.
        self.reloadLibrary = self.actionLibReload(self.menuMPD, self.__libReload)
        self.updateLibrary = self.actionLibUpdate(self.menuMPD, self.mpdclient.update)
        self.rescanLibrary = self.actionLibRescan(self.menuMPD, self.mpdclient.rescan)
        # Load all forms.
        self.createViews()
        # Fill Statusbar.
        self.serverLabel = QLabel('Not connected')
        self.numSongsLabel = QLabel('Songs')
        self.playTimeLabel = QLabel('playTime')
        self.statusTabs = auxilia.StatusTabBar()
        self.statusTabs.addTab(auxilia.PIcon("media-playlist-repeat"), 'Current Playlist')
        self.statusTabs.addTab(auxilia.PIcon("network-workgroup"), 'Shoutcast')
        self.statusTabs.setShape(1)
        self.statusbar.addWidget(self.statusTabs)
        self.statusbar.addWidget(self.serverLabel)
        self.statusbar.addPermanentWidget(self.numSongsLabel)
        self.statusbar.addPermanentWidget(self.playTimeLabel)
        self.connect(self.statusTabs, SIGNAL('currentChanged(int)'), self.stackedWidget.setCurrentIndex)

        self.connect(self.menuConnect, SIGNAL('aboutToShow()'), self.__buildConnectTo)
        self.connect(self.actionExit,SIGNAL('triggered()'),self.app.quit)
        self.connect(self.actionSettings,SIGNAL('triggered()'),self.showConfig)


        # Set up trayicon and menu.
        self.trayMenu = QMenu('Pythagora MPD client', self)
        self.trayMenu.addAction(self.menuTitle(appIcon, 'Pythagora'))
        self.trayMenu.addMenu(self.menuConnect)
        self.trayMenu.addAction(self.actionSettings)
        self.HideResoreAction = self.actionHideRestore(self.trayMenu, self.__toggleHideRestore)
        self.trayMenu.addAction(self.actionExit)
        self.trayIcon = QSystemTrayIcon(appIcon, self)
        self.trayIcon.setContextMenu(self.trayMenu)
        self.connect(self.trayIcon, SIGNAL('activated(QSystemTrayIcon::ActivationReason)'), self.__toggleHideRestore)
        self.trayIcon.show()

        # Apply configuration.
        self.resize(configuration.mgrSize)
        self.splitter.setSizes(configuration.mgrSplit)
        self.statusTabs.setCurrentIndex(configuration.showShoutcast)
        self.tabs.setCurrentIndex(configuration.tabsIndex)

        self.closeEvent = self.closeEvent
        self.connect(self.app,SIGNAL('aboutToQuit()'),self.shutdown)
        self.show()

#==============================================================================
# Code for switching tabs on drag & drop. (__init__() continues)
#==============================================================================

        # Instantiate timer
        self.tabTimer = QTimer()
        self.connect(self.tabTimer, SIGNAL('timeout()'), self.__selectTab)

        # Overload the default dragEvents. (none?)
        self.tabs.dragLeaveEvent = self.dragLeaveEvent
        self.tabs.dragEnterEvent = self.dragEnterEvent
        self.tabs.dragMoveEvent = self.dragMoveEvent

    def dragEnterEvent(self, event):
        '''Starts timer on enter and sets first position.'''
        self.tabPos = event.pos()
        event.accept()
        self.tabTimer.start(500)

    def dragLeaveEvent(self, event):
        '''If the mouse leaves the tabWidget stop the timer.'''
        self.tabTimer.stop()

    def dragMoveEvent(self, event):
        '''Keep track of the mouse and change the position, restarts the timer when moved.'''
        # TODO: Set threshold for movement.
        self.tabPos = event.pos()
        self.tabTimer.start()

    def __selectTab(self):
        '''Changes the view to the tab where the mouse was hovering above.'''
        index = self.tabs.tabBar().tabAt(self.tabPos)
        self.tabs.setCurrentIndex(index)
        self.tabTimer.stop()

    def __libReload(self):
        self.emit(SIGNAL('reloadLibrary()'))

#==============================================================================

    def createViews(self):
        '''Set up our different view handlers.'''
        self.playerForm = PlayerForm(self, self.app, self.mpdclient, self.config)
        self.currentList = CurrentPlaylistForm.CurrentPlaylistForm(self, self.app, self.mpdclient, self.config)
        self.libraryForm = LibraryForm.LibraryForm(self, self.app, self.mpdclient, self.config)
        self.playlistsForm = PlaylistForm.PlaylistForm(self, self.app, self.mpdclient, self.config)
        self.shoutcast = ShoutcastForm.ShoutcastForm(self, self.app, self.mpdclient, self.config)

    def shutdown(self):
        self.shuttingDown = True
        self.app.processEvents()
        try:
            self.mpdclient.close()
            self.mpdclient.disconnect()
            print 'debug: called close'
        except:
            pass
        if self.config:
            self.config.mgrSize = self.size()
            self.config.showShoutcast = self.stackedWidget.currentIndex()
            self.config.tabsIndex = self.tabs.currentIndex()
            self.config.keepPlayingVisible = bool(self.keepPlayingVisible.checkState())
            self.config.playlistControls = bool(self.playlistTools.isVisible())
            self.config.mgrSplit = self.splitter.sizes()
            self.config.mgrScSplit = self.scSplitter.sizes()
            self.config.libSplit1 = self.libSplitter_1.sizes()
            self.config.libSplit2 = self.libSplitter_2.sizes()
            self.config.playlistSplit = self.playlistSplitter.sizes()
            self.config.save()
        print 'debug: shutdown finished'

    def showConfig(self):
        self.config.showConfiguration(self)

    def closeEvent(self, event):
        '''Catch MainWindow's close event so we can hide it instead.'''
        self.__toggleHideRestore()
        event.ignore()

    def __toggleHideRestore(self, reason=None):
        '''Show or hide the window based on some parameters. We can detect
        when we are obscured and come to the top. In other cases we hide if
        mapped and show if not.
        '''
        if reason == QSystemTrayIcon.MiddleClick:
            self.playerForm.play.emit(SIGNAL('clicked(bool)'), True)
        if KDE:
            info = KWindowSystem.windowInfo( self.winId(), NET.XAWMState | NET.WMState | ((2**32)/2), NET.WM2ExtendedStrut)
            mapped = bool(info.mappingState() == NET.Visible and not info.isMinimized())
            if not reason or reason == QSystemTrayIcon.Trigger:
                if not mapped:
                    self.HideResoreAction.setText('Hide')
                    self.show()
                elif not reason or KWindowSystem.activeWindow() == self.winId():
                    self.HideResoreAction.setText('Show')
                    self.hide()
                else:
                    self.activateWindow()
                    self.raise_()
        else:
            if self.isVisible():
                self.hide()
            else: self.show()


    def __buildConnectTo(self):
        self.menuConnect.clear()
        self.menuConnect.addAction(auxilia.PIcon('dialog-cancel'), 'None (disconnect)')
        connected = self.mpdclient.connected()
        for server in self.config.knownHosts:
            if connected and self.config.server and self.config.server[0] == server:
                icon = auxilia.PIcon('network-connect')
            else: icon = auxilia.PIcon('network-disconnect')
            self.menuConnect.addAction(icon, server)

class PlayerForm(QWidget):
    def __init__(self, view, app, mpdclient, config):
        QWidget.__init__(self)
        self.view = view
        try:
            if self.view.KDE:
                uic.loadUi('PlayerForm.ui', self)
            else: raise
        except:
            uic.loadUi('PlayerForm.ui.Qt', self)
        self.playerForm = self
        self.view.topLayout.addWidget(self)
        # Set attributes not set trough xml file.
        self.back.setIcon(auxilia.PIcon("media-skip-backward"))
        self.stop.setIcon(auxilia.PIcon("media-playback-stop"))
        self.forward.setIcon(auxilia.PIcon("media-skip-forward"))
        self.songLabel = songwidgets.SongLabel()
        self.songLabel.setAcceptDrops(True)
        self.titleLayout.addWidget(self.songLabel)
