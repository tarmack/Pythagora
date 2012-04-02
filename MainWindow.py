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
from PyQt4.QtCore import SIGNAL, SLOT, QTimer, Qt, QObject, QEvent, QPoint, QPointF, QSize
from PyQt4.QtGui import QMainWindow, QLabel, QMenu, QIcon, QWidget, QAction, QWidgetAction, QToolButton, \
        QBrush, QFontMetrics, QPainter, QLinearGradient, QPalette, QPen, QApplication, QPixmap, QVBoxLayout
from time import time
import os
import cPickle as pickle
try:
    import dbus
    dbus # Use it once to silence PyFlakes
except ImportError:
    dbus = None

import mpdlibrary
import CurrentPlaylistForm
import plugins
import auxilia
from ui import KDE, MainWindow, PlayerForm

DATA_DIR = ''

if KDE:
    from PyKDE4.kdeui import KWindowSystem
    from PyKDE4.kdeui import KStatusNotifierItem
    from PyKDE4.kdeui import KStandardAction
else:
    from PyQt4.QtGui import QSystemTrayIcon

class View(QMainWindow, auxilia.Actions, MainWindow):
    partyMode = False
    hide_window = True

    def __init__(self, modelManager, configuration, mpdclient, library, app):
        QMainWindow.__init__(self)
        self.modelManager = modelManager
        self.app = app
        self.app.commitData = self.commitData
        self.focus = time()
        self.shuttingDown = False
        self.config = configuration
        self.mpdclient = mpdclient
        self.library = library
        self.appIcon = os.path.abspath(DATA_DIR+'icons/Pythagora.png')
        self.setupUi(self)
        self.setWindowTitle('Pythagora')
        self.setWindowIcon(QIcon(self.appIcon))
        # Create standard views.
        self.playerForm = PlayerForm(self.modelManager, self.config)
        self.topLayout.addWidget(self.playerForm)
        self.connect(self.modelManager.playerState, SIGNAL('currentSongChanged'), self.playerForm.updateSong)
        self.connect(self.modelManager.playerState, SIGNAL('volumeChanged'), self.playerForm.setVolume)
        self.connect(self.modelManager.playerState, SIGNAL('progressChanged'), self.playerForm.setProgress)
        self.connect(self.modelManager.playerState, SIGNAL('playStateChanged'), self.playerForm.setPlayState)
        self.connect(self.modelManager.playerState, SIGNAL('bitrateChanged'), self.playerForm.songLabel.setBitrate)
        self.dbusNotifications = DBusNotifications(self.config)
        self.connect(self.modelManager.playerState, SIGNAL('currentSongChanged'), self.dbusNotifications.showNotification)
        self.toolBarLayout = self.playerForm.toolBarLayout
        self.currentList = CurrentPlaylistForm.CurrentPlaylistForm(
                self.modelManager, self, self.app, self.config)
        self.currentListLayout.addWidget(self.currentList)
        self.connect(self.playerForm.play, SIGNAL('clicked(bool)'), self.modelManager.playerState.playPause)
        self.connect(self.playerForm.back, SIGNAL('clicked(bool)'), self.modelManager.playerState.previousSong)
        self.connect(self.playerForm.forward, SIGNAL('clicked(bool)'), self.modelManager.playerState.nextSong)
        self.connect(self.playerForm.stop, SIGNAL('clicked(bool)'), self.modelManager.playerState.stop)
        self.connect(self.playerForm.volume, SIGNAL('valueChanged(int)'), self.modelManager.playerState.setVolume)

        # Standard toolbar buttons.
        self.exitAction = self.actionExit(self, self.app.quit)
        self.exitButton = QToolButton()
        self.exitButton.setAutoRaise(True)
        self.exitButton.setIconSize(QSize(22, 22))
        self.exitButton.setDefaultAction(self.exitAction)
        self.settingsAction = self.actionSettings(self, self.showConfig)
        self.settingsButton = QToolButton()
        self.settingsButton.setAutoRaise(True)
        self.settingsButton.setIconSize(QSize(22, 22))
        self.settingsButton.setDefaultAction(self.settingsAction)
        # Create 'Connect to' menu.
        self.menuConnect = QMenu('Connect To')
        self.menuConnect.menuAction().setIcon(auxilia.PIcon('network-disconnect'))
        self.connectButton = QToolButton()
        self.connectButton.setAutoRaise(True)
        self.connectButton.setIconSize(QSize(22, 22))
        self.connectButton.setPopupMode(QToolButton.InstantPopup)
        self.connectButton.setIcon(auxilia.PIcon('network-disconnect'))
        self.connectButton.setText('Connect To')
        self.connectButton.setMenu(self.menuConnect)
        # Create 'MDP' menu.
        self.menuMPD = QMenu('MPD')
        self.menuMPD.menuAction().setIcon(auxilia.PIcon('network-workgroup'))
        self.connect(self.menuConnect, SIGNAL('aboutToShow()'), self._buildConnectTo)
        self.mpdButton = QToolButton()
        self.mpdButton.setAutoRaise(True)
        self.mpdButton.setIconSize(QSize(22, 22))
        self.mpdButton.setPopupMode(QToolButton.InstantPopup)
        self.mpdButton.setIcon(auxilia.PIcon('network-workgroup'))
        self.mpdButton.setText('MPD')
        self.mpdButton.setMenu(self.menuMPD)
        self.reloadLibrary = self.actionLibReload(self.menuMPD, lambda: self.modelManager.reloadLibrary(True))
        self.updateLibrary = self.actionLibUpdate(self.menuMPD, lambda: self.mpdclient.send('update'))
        self.rescanLibrary = self.actionLibRescan(self.menuMPD, lambda: self.mpdclient.send('rescan'))
        # Create 'Outputs' menu.
        self.menuOutputs = QMenu('Outputs')
        self.menuOutputs.menuAction().setIcon(auxilia.PIcon('audio-card'))
        self.connect(self.menuOutputs, SIGNAL('aboutToShow()'), self._buildOutputs)
        self.outputsButton = QToolButton()
        self.outputsButton.setAutoRaise(True)
        self.outputsButton.setIconSize(QSize(22, 22))
        self.outputsButton.setPopupMode(QToolButton.InstantPopup)
        self.outputsButton.setIcon(auxilia.PIcon('audio-card'))
        self.outputsButton.setText('Outputs')
        self.outputsButton.setMenu(self.menuOutputs)
        # Fill Toolbar.
        self.toolBarLayout.addWidget(self.exitButton)
        self.toolBarLayout.addWidget(self.settingsButton)
        self.toolBarLayout.addWidget(self.connectButton)
        self.toolBarLayout.addWidget(self.outputsButton)
        self.toolBarLayout.addWidget(self.mpdButton)
        self.toolBarLayout.addStretch(1)
        # Fill Statusbar.
        self.serverLabel = QLabel('Not connected')
        self.numSongsLabel = QLabel('Songs')
        self.playTimeLabel = QLabel('playTime')
        self.statusbar.addWidget(self.serverLabel)
        self.statusbar.addPermanentWidget(self.numSongsLabel)
        self.statusbar.addPermanentWidget(self.playTimeLabel)

        # Set up trayicon and menu.
        if KDE:
            self.trayIcon = KTrayIcon(self.appIcon, self)
        else:
            self.trayIcon = QTrayIcon(self.appIcon, self)
        outputsMenuAction = self.menuOutputs.menuAction()
        connectMenuAction = self.menuConnect.menuAction()
        self.trayIcon.addMenuItem(outputsMenuAction)
        self.trayIcon.addMenuItem(connectMenuAction)
        self.trayIcon.addMenuItem(self.settingsAction)
        self.connect(self.trayIcon, SIGNAL('activate()'), self.toggleHideRestore)
        self.connect(self.trayIcon, SIGNAL('secondaryActivateRequested(QPoint)'), self._playPause)
        self.connect(self.trayIcon, SIGNAL('scrollRequested(int, Qt::Orientation)'),
                lambda amount: self.modelManager.playerState.volumeUp((amount+30)/60))
        self.connect(self.modelManager.playerState, SIGNAL('playStateChanged'), self.trayIcon.setState)

        self.connect(self.tabs, SIGNAL('currentChanged(int)'), self._tabsIndexChanged)
        self.connect(self.tabs.tabBar(), SIGNAL('tabMoved(int,int)'), self._tabMoved)
        self.connect(self.splitter, SIGNAL('splitterMoved(int, int)'), self._storeSplitter)

        # Apply configuration.
        self.resize(configuration.mgrSize)
        self.splitter.setSizes(configuration.mgrSplit)
        self.tabs.setCurrentIndex(configuration.tabsIndex)

        self.closeEvent = self.closeEvent
        self.connect(self.app,SIGNAL('aboutToQuit()'),self.shutdown)

#==============================================================================
# Code for switching tabs on drag & drop. (__init__() continues)
#==============================================================================

        # Instantiate timer
        self.tabTimer = QTimer()
        self.connect(self.tabTimer, SIGNAL('timeout()'), self._selectTab)

        # Overload the default dragEvents.
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
        tabPos = event.pos()
        moved = tabPos.manhattanLength() - self.tabPos.manhattanLength()
        if moved > 7 or moved < -7:
            self.tabTimer.start(500)
        self.tabPos = tabPos


    def _selectTab(self):
        '''Changes the view to the tab where the mouse was hovering above.'''
        index = self.tabs.tabBar().tabAt(self.tabPos)
        self.tabs.setCurrentIndex(index)
        self.tabTimer.stop()


#==============================================================================

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F11:
            self._togglePartymode()
        else:
            super(View, self).keyPressEvent(event)

    def createPluginViews(self):
        '''Set all plugin tabs up.'''
        loadedPlugins = {}
        for plugin in plugins.allPlugins:
            plugin = plugin.getWidget(self.modelManager, self.mpdclient, self.config, self.library)
            if plugin:
                loadedPlugins[plugin.moduleName] = plugin
        for name in self.config.tabOrder:
            if name in loadedPlugins:
                plugin = loadedPlugins.pop(name)
                self.tabs.addTab(plugin, auxilia.PIcon(plugin.moduleIcon), plugin.moduleName)
        for plugin in loadedPlugins.values():
            self.tabs.addTab(plugin, auxilia.PIcon(plugin.moduleIcon), plugin.moduleName)
            order = self.config.tabOrder
            order.append(plugin.moduleName)
            self.config.tabOrder = order

    def shutdown(self):
        self.shuttingDown = True
        self.app.processEvents()
        self.mpdclient.disconnect()
        self.config.mgrSize = self.size()
        print 'debug: shutdown finished'

    def commitData(self, sessionManager):
        self.hide_window = False
        QApplication.commitData(self.app, sessionManager)

    def showConfig(self):
        self.config.showConfiguration(self)

    def closeEvent(self, event):
        '''Catch MainWindow's close event so we can hide it instead.'''
        if self.hide_window:
            self.hide()
            event.ignore()
        else:
            QMainWindow.closeEvent(self, event)

    def _storeSplitter(self):
        self.config.mgrSplit = self.splitter.sizes()

    def _tabsIndexChanged(self, value):
        self.config.tabsIndex = self.tabs.currentIndex()

    def _tabMoved(self, old, new):
        print "DEBUG: Tab from", old, "moved to", new
        order = self.config.tabOrder
        order.insert(new, order.pop(old))
        self.config.tabOrder = order

    def toggleHideRestore(self):
        '''Show or hide the window based on some parameters. We can detect
        when we are obscured and come to the top. In other cases we hide if
        mapped and show if not.
        '''
        if KDE:
            if KWindowSystem.activeWindow() == self.winId() and self.isVisible():
                self.hide()
            else:
                self.show()
                KWindowSystem.forceActiveWindow(self.winId())
        else:
            if self.isVisible():
                self.hide()
            else: self.show()

    def _playPause(self):
        self.playerForm.play.emit(SIGNAL('clicked(bool)'), True)

    def _buildConnectTo(self):
        self.menuConnect.clear()
        self.menuConnect.addAction(auxilia.PIcon('dialog-cancel'), 'None (disconnect)')
        connected = self.mpdclient.connected()
        for server in self.config.knownHosts:
            if connected and self.config.server and self.config.server[0] == server:
                icon = auxilia.PIcon('network-connect')
            else: icon = auxilia.PIcon('network-disconnect')
            self.menuConnect.addAction(icon, server)

    def _buildOutputs(self):
        self.menuOutputs.clear()
        if self.mpdclient.connected():
            print 'debug: Building output menu.'
            for output in self.mpdclient.outputs():
                action = QAction(output.get('outputname', 'No name'), self.menuOutputs)
                action.setCheckable(True)
                action.setChecked(output.get('outputenabled', '0') == '1')
                action.outputid = output.get('outputid')
                self.menuOutputs.addAction(action)

    def _togglePartymode(self):
        if self.partyMode:
            self.toolBar.show()
            self.showNormal()
            QApplication.instance().processEvents()
            if self.partyMode != self.geometry().size():
                self.showMaximized()
            self.partyMode = False
        else:
            self.partyMode = self.geometry().size()
            self.toolBar.hide()
            self.showFullScreen()


class PlayerForm(QWidget, PlayerForm):
    def __init__(self, modelManager, config):
        QWidget.__init__(self)
        self.modelManager = modelManager
        self.iconPath = ''
        self._currentSong = None
        self.setupUi(self)
        # Set attributes not set trough xml file.
        self.back.setIcon(auxilia.PIcon("media-skip-backward"))
        self.stop.setIcon(auxilia.PIcon("media-playback-stop"))
        self.forward.setIcon(auxilia.PIcon("media-skip-forward"))
        self.pauseIcon = auxilia.PIcon("media-playback-pause")
        self.startIcon = auxilia.PIcon("media-playback-start")
        self.songLabel = SongLabel(config)
        self.titleLayout.addWidget(self.songLabel)
        self.setAcceptDrops(True)
        self.progress.mouseReleaseEvent = self._progressSeekEvent
        self.progress.mouseMoveEvent = self._progressShowTimeEvent
        self.progress.setMouseTracking(True)
        self.songIcon.mousePressEvent = self._iconOverlayEvent

    def updateSong(self, song):
        self.songLabel.updateSong(song)
        if not song is None:
            self.progress.setMaximum(song.time or 1)
            if song.iconPath:
                self.setSongIcon(song.iconPath)
            else:
                if not self._currentSong is None:
                    self.disconnect(self._currentSong, SIGNAL('iconChanged'), self._iconChanged)
                self.connect(song, SIGNAL('iconChanged'), self._iconChanged)
        else:
            self.setSongIcon(None)
        self._currentSong = song

    def _iconChanged(self, songID, iconPath):
        self.setSongIcon(iconPath)

    def setSongIcon(self, iconPath):
        self.iconPath = iconPath
        if iconPath is not None:
            height = self.songIcon.geometry().height()
            self.songIcon.setPixmap(QPixmap(iconPath).scaled(1000, height, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.songIcon.clear()

    def setProgress(self, progress):
        '''
        Moves the progress indicator to the correct position, calculates the
        timestamps and puts them in place.
        '''
        songTime = mpdlibrary.Time(self.progress.maximum())
        if songTime <= 1:
            self.progress.setValue(0)
            self.progress.setFormat(progress.human)
        else:
            self.progress.setValue(progress)
            self.progress.setFormat('/'.join((progress.human, songTime.human)))

    def setVolume(self, volume):
        self.volume.setValue(volume)

    def setPlayState(self, state):
        if state == 'play':
            self.play.setIcon(self.pauseIcon)
        else:
            self.play.setIcon(self.startIcon)
        # Put in trayicon class.
        #self.view.trayIcon.setState(state)
        self.state = state

    def dragEnterEvent(self, event):
        if event.provides('mpd/uri'):
            event.accept()

    def dropEvent(self, event):
        if event.provides('mpd/uri'):
            event.accept()
            data = event.mimeData()
            uri_list = pickle.loads(str(data.data('mpd/uri')))
            self.modelManager.playQueue.clear()
            self.modelManager.playQueue.extend(uri_list)
            self.modelManager.playerState.currentSong = 0
            self.modelManager.playerState.play()

    def _progressSeekEvent(self, event):
        if event.button() == Qt.LeftButton:
            position = float(event.x()) / int(self.progress.geometry().width())
        time = self.modelManager.playerState.currentSong.time
        if time > 0:
            self.modelManager.playerState.progress = int(time * position)

    def _progressShowTimeEvent(self, event):
        position = float(event.x()) / int(self.progress.geometry().width())
        seconds = position * self.progress.maximum()
        self.progress.setToolTip(mpdlibrary.Time(seconds).human)

    def _iconOverlayEvent(self, event):
        popup = QMenu(self)
        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        popup.setLayout(layout)
        iconLabel = QLabel(popup)
        layout.addWidget(iconLabel)

        closeEvent = lambda event: popup.setParent(None)

        geometry = self.songIcon.geometry()
        songIcon = QPixmap(self.iconPath)
        iconLabel.setGeometry(geometry)
        iconLabel.setPixmap(songIcon)
        iconLabel.mousePressEvent = closeEvent
        popup.popup(geometry.topLeft())


class SongLabel(QLabel):
    title = 'title'
    artist = 'artist'
    album = 'album'
    station = 'station'
    bitrate = ''
    parts = ('artist', 'album', 'station')
    prepends = {
            'artist': 'by',
            'album': 'from',
            'station': 'on',
            }
    def __init__(self, config):
        QLabel.__init__(self)
        self.config = config
        self.songInToolTip = False
        self.setAlignment(Qt.AlignBottom)
        self.titleFont = self.font()
        self.titleFont.setPointSize(self.font().pointSize()+6)
        self.artistFont = self.font()
        self.artistFont.setPointSize(self.font().pointSize()+2)
        self.albumFont = self.font()
        self.albumFont.setItalic(True)
        self.stationFont = self.font()
        self.stationFont.setItalic(True)

    def updateSong(self, song):
        if song is None:
            if self.config.server is None:
                label = 'Disconnected'
            else:
                label = 'Connected to %s.' % self.config.server[0]
            self.setText(label)
        else:
            title = song.title
            artist = song.artist
            album = song.album
            station = song.station
            if album == 'None':
                album = ''
            self.setText(title, artist, album, station)

    def setText(self, title='', artist='', album='', station=''):
        self.title = title
        self.artist = artist
        self.album = album
        if station != title:
            self.station = station
        else:
            self.station = ''
        self.repaint()

    def setBitrate(self, bitrate):
        self.bitrate = bitrate if bitrate and bitrate != '0' else ''
        self.setToolTip(self.getToolTip())

    def getToolTip(self):
        title = ''
        artist = ''
        album = ''
        station = ''
        bitrate = ''
        if self.songInToolTip:
            if self.title:
                title = '<b><big>%s</big></b>' % self.title
            if self.artist:
                artist = 'by <big>%s</big>' % self.artist
            if self.album:
                album = 'from <i>%s</i>' % self.album
            if self.station:
                station = 'on <i>%s</i>' % self.station
        if self.bitrate:
            bitrate = 'bitrate: %skbps' % self.bitrate
        return '<br>'.join((item for item in (title, artist, album, station, bitrate) if item))

    def paintEvent(self, event):
        self.songInToolTip = False
        gradient = self._gradient()
        self.spaceLeft = self.contentsRect()
        for part in self.parts:
            font = getattr(self, '%sFont' % part)
            text = getattr(self, part)
            if text:
                self._write(self.prepends.get(part, ''), self.font(), gradient)
                self._write(text, font, gradient)
        if self.spaceLeft.width() <= 3:
            self.songInToolTip = True
        self.spaceLeft = self.contentsRect()
        self.spaceLeft.setBottom(self.spaceLeft.bottom() - QFontMetrics(self.artistFont).height())
        self._write(self.title, self.titleFont, gradient)
        if self.spaceLeft.width() <= 3:
            self.songInToolTip = True
        self.setToolTip(self.getToolTip())

    def _write(self, text, font, pen):
        width = QFontMetrics(font).width(text+' ')
        painter = QPainter(self)
        painter.setFont(font)
        painter.setPen(pen)
        painter.drawText(self.spaceLeft, Qt.AlignBottom, text)
        self.spaceLeft.setLeft(self.spaceLeft.left() + width ) # move the left edge to the end of what we just painted.

    def _gradient(self):
        left = QPointF(self.contentsRect().topLeft())
        right = QPointF(self.contentsRect().topRight())
        gradient = QLinearGradient(left, right)
        gradient.setColorAt(0.9, self.palette().color(QPalette.WindowText))
        gradient.setColorAt(1.0, self.palette().color(QPalette.Window))
        pen = QPen()
        pen.setBrush(QBrush(gradient))
        return pen


class DBusNotifications(QObject):
    def __init__(self, config):
        QObject.__init__(self)
        self.config = config
        self._currentSong = None
        if dbus is None:
            self.config.showNotification = False
            return
        self.notificationId = dbus.UInt32(0)
        self.appName = unicode(QApplication.applicationName().toUtf8())
        self.appIcon = os.path.abspath(DATA_DIR+'icons/Pythagora.png')
        self.notificationSummary = '%s, now playing:' % self.appName
        self.notificationHints = dbus.Dictionary(
            {'suppress-sound':  True,
             'desktop-entry':   'pythagora',
             'image_path':      ''},
            'sv')
        self._connect()

    def _connect(self):
        try:
            self.dbusNotification = dbus.SessionBus().get_object(
                'org.freedesktop.Notifications',
                '/org/freedesktop/Notifications',
                'org.freedesktop.Notifications')
        except dbus.DBusException, e:
            self.config.showNotification = False
            print 'debug: error using dbus - %s' % e

    def showNotification(self, song):
        if (not song is None) and self.config.showNotification:
            if song.iconPath:
                self._showNotification(song)
            else:
                if not self._currentSong is None:
                    self.disconnect(self._currentSong, SIGNAL('iconChanged'), self._iconChanged)
                self._currentSong = song
                self.connect(song, SIGNAL('iconChanged'), self._iconChanged)

    def _iconChanged(self, songID, iconPath):
        self._showNotification(self._currentSong)

    def _showNotification(self, song):
        label = richTextLabel(song)
        self.notificationHints.update({'image_path': song.iconPath})
        # Show notification
        try:
            self.notificationId = self.dbusNotification.Notify(
                self.appName,                           #app_name
                self.notificationId,                    #replaces_id
                self.appIcon,                           #app_icon
                self.notificationSummary,               #summary
                label,                                  #body
                [''],                                   #actions
                self.notificationHints,                 #hints
                self.config.notificationTimeout * 1000) #timeout
        except dbus.DBusException:
            print 'debug: Error while showing notification. Will try again for the next song.'


class TrayIconCommon(object):
    def updateSong(self, song):
        label = richTextLabel(song)
        self.setToolTip(song.iconPath, label)

    def addMenuItem(self, action):
        self.actionList.append(action)


if KDE:
    class KTrayIcon(KStatusNotifierItem, TrayIconCommon):
        actionList = []
        def __init__(self, icon, parent):
            KStatusNotifierItem.__init__(self, parent)
            self.setStandardActionsEnabled(False)
            self.connect(self.contextMenu(), SIGNAL('aboutToShow()'), self._buildMenu)
            self.actionQuit = KStandardAction.quit(parent.app, SLOT("quit()"), self)
            self.hideResoreAction = QAction('Minimize', self.contextMenu())
            self.connect(self.hideResoreAction, SIGNAL('triggered()'), SIGNAL("activate()"))
            self.icon = icon
            self.parent = parent
            self.setIconByName(icon)
            self.setCategory(1)
            self.setStatus(2)

        def setState(self, state):
            if state == 'play':
                self.setIconByName("media-playback-start")
            elif state == 'pause':
                self.setIconByName("media-playback-pause")
            else:
                self.setIconByName("media-playback-stop")

        def setToolTip(self, iconPath, text):
            if not iconPath:
                iconPath = self.icon
            super(KTrayIcon, self).setToolTip(iconPath, 'Pythagora,&nbsp;Now&nbsp;Playing:', text)

        def activate(self, pos):
            self.emit(SIGNAL('activate()'))

        def _buildMenu(self):
            if self.parent.isVisible():
                self.hideResoreAction.setText('Minimize')
            else:
                self.hideResoreAction.setText('Restore')
            for action in self.actionList:
                self.contextMenu().addAction(action)
            self.contextMenu().addSeparator()
            self.contextMenu().addAction(self.hideResoreAction)
            self.contextMenu().addAction(self.actionQuit)

else:
    class QTrayIcon(QSystemTrayIcon, TrayIconCommon, auxilia.Actions):
        def __init__(self, icon, parent):
            QSystemTrayIcon.__init__(self, QIcon(icon), parent)
            self.parent = parent
            self.pauseIcon = auxilia.PIcon("media-playback-pause")
            self.startIcon = auxilia.PIcon("media-playback-start")
            self.stopIcon = auxilia.PIcon("media-playback-stop")
            self.actionList = []
            self.menu = QMenu('Pythagora MPD client', parent)
            self.menu.addAction(menuTitle(QIcon(icon), 'Pythagora', parent))
            self.setContextMenu(self.menu)
            self.hideResoreAction = QAction('Minimize', self.menu)
            self.connect(self.hideResoreAction, SIGNAL('triggered()'), self._activated)
            self.connect(self, SIGNAL('activated(QSystemTrayIcon::ActivationReason)'), self._activated)
            self.connect(self.menu, SIGNAL('aboutToShow()'), self._buildMenu)
            self.show()

        def setState(self, state):
            if state == 'play':
                self.setIcon(self.startIcon)
            elif state == 'pause':
                self.setIcon(self.pauseIcon)
            else:
                self.setIcon(self.stopIcon)

        def setToolTip(self, iconPath, text):
            super(QTrayIcon, self).setToolTip('Pythagora,&nbsp;Now&nbsp;Playing:<br>%s' % text)

        def _activated(self, reason=None):
            if reason == QSystemTrayIcon.MiddleClick:
                self.emit(SIGNAL('secondaryActivateRequested(QPoint)'), QPoint())
            if reason == None or reason == QSystemTrayIcon.Trigger:
                self.emit(SIGNAL('activate()'))

        def _buildMenu(self):
            if self.parent.isVisible():
                self.hideResoreAction.setText('Minimize')
            else:
                self.hideResoreAction.setText('Restore')
            for action in self.actionList:
                self.menu.addAction(action)
            self.menu.addSeparator()
            self.menu.addAction(self.hideResoreAction)
            self.menu.addAction(self.parent.exitAction)


        def event(self, event):
            if event.type() == 31: # enum: QEvent.wheel
                event.accept()
                self.emit(SIGNAL('scrollRequested(int, Qt::Orientation)'), event.delta(), Qt.Horizontal)
                return True
            else:
                super(QTrayIcon, self).event(event)
                return False


    class EventEater(QObject):
        def eventFilter(self, reciever, event):
            if event.type() == QEvent.MouseButtonPress or event.type() == QEvent.MouseButtonRelease:
                return True
            return False

    def menuTitle(icon, text, parent):
        eventEater = EventEater()
        buttonaction = QAction(parent)
        font = buttonaction.font()
        font.setBold(True)
        buttonaction.setFont(font)
        buttonaction.setText(text)
        buttonaction.setIcon(icon)

        action = QWidgetAction(parent)
        action.setObjectName('trayMenuTitle')
        titleButton = QToolButton(parent)
        titleButton.installEventFilter(eventEater)
        titleButton.setDefaultAction(buttonaction)
        titleButton.setDown(True)
        titleButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        action.setDefaultWidget(titleButton)

        return action


def richTextLabel(song):
    title = song.title
    artist = song.artist
    album = song.album
    station = song.station
    if album == 'None':
        album = ''
    if station and station != title:
        station = 'on <i>%s</i>' % station
    else:
        station = ''
    if title:
        title = '<b><big>%s</big></b>' % title
    if artist:
        artist = 'by <big>%s</big>' % artist
    if album:
        album = 'from <i>%s</i>' % album
    return '<br>'.join((item for item in (title, artist, album, station) if item))

