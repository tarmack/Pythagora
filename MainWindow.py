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
from PyQt4.QtGui import QSystemTrayIcon, QLabel, QHeaderView, QMenu, QIcon
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

class View(auxilia.Actions):
    def __init__(self, configuration, mpdclient, app):
        self.focus = time()
        self.shuttingDown = False
        self.config = configuration
        self.mpdclient = mpdclient
        appIcon = QIcon('icons/Pythagora.png')
        try:
            if KDE:
                self.view = uic.loadUi('Pythagora.ui')
            else: raise
        except:
            self.view = uic.loadUi('Pythagora.ui.Qt')
        self.view.setWindowTitle('Pythagora')
        self.view.setWindowIcon(appIcon)
        # Set attributes not set trough xml file.
        self.view.back.setIcon(auxilia.PIcon("media-skip-backward"))
        self.view.stop.setIcon(auxilia.PIcon("media-playback-stop"))
        self.view.forward.setIcon(auxilia.PIcon("media-skip-forward"))
        self.view.trackView.header().setResizeMode(1, QHeaderView.Stretch)
        self.view.songLabel = songwidgets.SongLabel()
        self.view.songLabel.setAcceptDrops(True)
        self.view.titleLayout.addWidget(self.view.songLabel)
        # Load all forms.
        self.createViews()
        # Fill Statusbar.
        self.view.serverLabel = QLabel('Not connected')
        self.view.numSongsLabel = QLabel('Songs')
        self.view.playTimeLabel = QLabel('playTime')
        self.view.statusTabs = auxilia.StatusTabBar()
        self.view.statusTabs.addTab(auxilia.PIcon("media-playlist-repeat"), 'Current Playlist')
        self.view.statusTabs.addTab(auxilia.PIcon("network-workgroup"), 'Shoutcast')
        self.view.statusTabs.setShape(1)
        self.view.statusbar.addWidget(self.view.statusTabs)
        self.view.statusbar.addWidget(self.view.serverLabel)
        self.view.statusbar.addPermanentWidget(self.view.numSongsLabel)
        self.view.statusbar.addPermanentWidget(self.view.playTimeLabel)
        self.view.connect(self.view.statusTabs, SIGNAL('currentChanged(int)'), self.view.stackedWidget.setCurrentIndex)
        self.view.connect(self.view.currentBottom, SIGNAL('clicked()'), self.__togglePlaylistTools)

        self.view.connect(self.view.menuConnect, SIGNAL('aboutToShow()'), self.__buildConnectTo)
        self.view.connect(self.view.actionExit,SIGNAL('triggered()'),self.app.quit)
        self.view.connect(self.view.actionSettings,SIGNAL('triggered()'),self.showConfig)


        # Set up trayicon and menu.
        self.trayMenu = QMenu('Pythagora MPD client', self.view)
        self.trayMenu.addAction(self.menuTitle(appIcon, 'Pythagora'))
        self.trayMenu.addMenu(self.view.menuConnect)
        self.trayMenu.addAction(self.view.actionSettings)
        self.HideResoreAction = self.actionHideRestore(self.trayMenu, self.__toggleHideRestore)
        self.trayMenu.addAction(self.view.actionExit)
        self.view.trayIcon = QSystemTrayIcon(appIcon, self.view)
        self.view.trayIcon.setContextMenu(self.trayMenu)
        self.view.connect(self.view.trayIcon, SIGNAL('activated(QSystemTrayIcon::ActivationReason)'), self.__toggleHideRestore)
        self.view.trayIcon.show()

        # Apply configuration.
        self.view.resize(configuration.mgrSize)
        self.view.splitter.setSizes(configuration.mgrSplit)
        self.view.scSplitter.setSizes(configuration.mgrScSplit)
        self.view.libSplitter_1.setSizes(configuration.libSplit1)
        self.view.libSplitter_2.setSizes(configuration.libSplit2)
        self.view.playlistSplitter.setSizes(configuration.playlistSplit)
        self.view.statusTabs.setCurrentIndex(configuration.showShoutcast)
        self.view.tabs.setCurrentIndex(configuration.tabsIndex)
        self.view.keepPlayingVisible.setChecked(configuration.keepPlayingVisible)
        self.__togglePlaylistTools(configuration.playlistControls)

        self.view.closeEvent = self.closeEvent
        self.view.connect(self.app,SIGNAL('aboutToQuit()'),self.shutdown)
        self.view.show()

#==============================================================================
# Code for switching tabs on drag & drop. (__init__() continues)
#==============================================================================

        # Instantiate timer
        self.tabTimer = QTimer()
        self.view.connect(self.tabTimer, SIGNAL('timeout()'), self.__selectTab)

        # Overload the default dragEvents. (none?)
        self.view.tabs.dragLeaveEvent = self.dragLeaveEvent
        self.view.tabs.dragEnterEvent = self.dragEnterEvent
        self.view.tabs.dragMoveEvent = self.dragMoveEvent

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
        index = self.view.tabs.tabBar().tabAt(self.tabPos)
        self.view.tabs.setCurrentIndex(index)
        self.tabTimer.stop()
#==============================================================================

    def createViews(self):
        '''Set up our different view handlers.'''
        self.playlists = PlaylistForm.PlaylistForm(self.view, self.app, self.mpdclient)
        self.currentList = CurrentPlaylistForm.CurrentPlaylistForm(self.view, self.app, self.mpdclient, self.config)
        self.liberry = LibraryForm.LibraryForm(self.view, self.app, self.mpdclient, self.config)
        self.shoutcast = ShoutcastForm.ShoutcastForm(self.view, self.app, self.mpdclient, self.config.scBookmarkFile)

    def shutdown(self):
        self.shuttingDown = True
        self.timer.stop()
        self.app.processEvents()
        try:
            self.mpdclient.close()
            self.mpdclient.disconnect()
            print 'debug: called close'
        except:
            pass
        if self.config:
            self.config.mgrSize = self.view.size()
            self.config.showShoutcast = self.view.stackedWidget.currentIndex()
            self.config.tabsIndex = self.view.tabs.currentIndex()
            self.config.keepPlayingVisible = bool(self.view.keepPlayingVisible.checkState())
            self.config.playlistControls = bool(self.view.playlistTools.isVisible())
            self.config.mgrSplit = self.view.splitter.sizes()
            self.config.mgrScSplit = self.view.scSplitter.sizes()
            self.config.libSplit1 = self.view.libSplitter_1.sizes()
            self.config.libSplit2 = self.view.libSplitter_2.sizes()
            self.config.playlistSplit = self.view.playlistSplitter.sizes()
            self.config.save()
        print 'debug: shutdown finished'

    def showConfig(self):
        self.config.showConfiguration(self.view)

    def closeEvent(self, event):
        '''Catch MainWindow's close event so we can hide it instead.'''
        self.__toggleHideRestore()
        event.ignore()

    def __togglePlaylistTools(self, value=None):
        text = ('Show Playlist Tools', 'Hide Playlist Tools')
        if value == None:
            if self.view.playlistTools.isVisible():
                self.view.playlistTools.setVisible(False)
            else:
                self.view.playlistTools.setVisible(True)
            value = self.view.playlistTools.isVisible()
        else:
            self.view.playlistTools.setVisible(value)
        self.view.currentBottom.setArrowType(int(value)+1)
        self.view.currentBottom.setText(text[value])

    def __toggleHideRestore(self, reason=None):
        '''Show or hide the window based on some parameters. We can detect
        when we are obscured and come to the top. In other cases we hide if
        mapped and show if not.
        '''
        if reason == QSystemTrayIcon.MiddleClick:
            self.playControls.playPause()
        if KDE:
            info = KWindowSystem.windowInfo( self.view.winId(), NET.XAWMState | NET.WMState | ((2**32)/2), NET.WM2ExtendedStrut)
            mapped = bool(info.mappingState() == NET.Visible and not info.isMinimized())
            if not reason or reason == QSystemTrayIcon.Trigger:
                if not mapped:
                    self.HideResoreAction.setText('Hide')
                    self.view.show()
                elif not reason or KWindowSystem.activeWindow() == self.view.winId():
                    self.HideResoreAction.setText('Show')
                    self.view.hide()
                else:
                    self.view.activateWindow()
                    self.view.raise_()
        else:
            if self.view.isVisible():
                self.view.hide()
            else: self.view.show()


    def __buildConnectTo(self):
        self.view.menuConnect.clear()
        self.view.menuConnect.addAction(auxilia.PIcon('dialog-cancel'), 'None (disconnect)')
        connected = self.mpdclient.connected()
        for server in self.config.knownHosts:
            if connected and self.config.server and self.config.server[0] == server:
                icon = auxilia.PIcon('network-connect')
            else: icon = auxilia.PIcon('network-disconnect')
            self.view.menuConnect.addAction(icon, server)

