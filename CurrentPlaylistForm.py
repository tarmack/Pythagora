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
from PyQt4.QtCore import SIGNAL, Qt, QSize
from PyQt4.QtGui import QWidget, QInputDialog, QKeySequence, QListView, QIcon, QFont, \
        QSortFilterProxyModel, QItemDelegate, QStyle, QFontMetrics
from PyQt4 import uic
from time import time

import auxilia
import streamTools

DATA_DIR = ''

# TODO: See if drag pixmap can be alpha blended. (probably impossible)
# TODO: Make cover art download optional.

#===============================================================================
# List and controls for the currently loaded playlist
#===============================================================================
class CurrentPlaylistForm(QWidget, auxilia.Actions):
    '''List and controls for the currently loaded playlist'''
    editing = 0
    def __init__(self, modelManager, view, app, mpdclient, config):
        QWidget.__init__(self)
        self.app = app
        self.view = view
        self.mpdclient = mpdclient
        self.config = config
        self._temp = {}
        self.playQueue = modelManager.playQueue
        self.playQueueDelegate = PlayQueueDelegate(self.config)
        if self.view.KDE:
            uic.loadUi(DATA_DIR+'ui/CurrentListForm.ui', self)
        else:
            uic.loadUi(DATA_DIR+'ui/CurrentListForm.ui.Qt', self)
        self.view.currentListLayout.addWidget(self)

        self.playQueueProxy = QSortFilterProxyModel()
        self.playQueueProxy.setSourceModel(self.playQueue)
        self.playQueueProxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.playQueueProxy.setDynamicSortFilter(True)
        self.playQueueProxy.setFilterRole(Qt.AccessibleTextRole)
        self.currentList.setModel(self.playQueueProxy)
        self.currentList.setItemDelegateForColumn(0, self.playQueueDelegate)
        self.currentList.horizontalHeader().setResizeMode(1)

        if config.oneLinePlaylist:
            self.oneLinePlaylist.setChecked(True)
        self.keepPlayingVisible.setChecked(self.config.keepPlayingVisible)
        self._togglePlaylistTools(self.config.playlistControls)
        self.connect(self.playQueue, SIGNAL('aboutToUpdate'), self.prepareForUpdate)
        self.connect(self.playQueue, SIGNAL('updated'), self.updated)
        self.connect(self.playQueue, SIGNAL('currentChanged'), self._ensurePlayingVisable)


        # Connect to the view for double click action.
        self.connect(self.currentList, SIGNAL('doubleClicked(const QModelIndex &)'), self._playSong)

        self.connect(self.currentFilter,SIGNAL('textEdited(QString)'),self.playQueueProxy.setFilterFixedString)

        self.connect(self.currentRemove,SIGNAL('clicked()'),self._removeSelected)
        self.connect(self.currentClear,SIGNAL('clicked()'),self._clearCurrent)
        self.connect(self.currentSave,SIGNAL('clicked()'),self._saveCurrent)
        self.connect(self.addStream,SIGNAL('clicked()'),self._addStream)

        self.connect(self.currentBottom, SIGNAL('clicked()'), self._togglePlaylistTools)
        self.connect(self.currentList,SIGNAL('selectionChanged()'),self._setEditing)
        self.connect(self.currentList.verticalScrollBar(), SIGNAL('valueChanged(int)'), self._setEditing)
        self.connect(self.keepPlayingVisible,SIGNAL('toggled(bool)'),self._toggleKeepPlayingVisible)
        self.connect(self.oneLinePlaylist,SIGNAL('toggled(bool)'),self._setOneLinePlaylist)
        self.connect(self.showNumbers,SIGNAL('toggled(bool)'),self._setNumbers)
        self.showNumbers.setChecked(self.config.showNumbers)

        # Menu for current playlist.
        # Create actions.
        self.currentMenuPlay = self.action(self.currentList, self._playSong,
                icon="media-playback-start", text='play', tooltip='Start playing the selected song.')
        self.currentMenuRemove = self.action(self.currentList, self._removeSelected,
                icon="list-remove", text='Remove', tooltip="Remove the selected songs from the playlist.")
        self.currentMenuClear = self.action(self.currentList, self._clearCurrent,
                icon="document-new", text='Clear', tooltip="Remove all songs from the playlist.")
        self.currentMenuSave = self.action(self.currentList, self._saveCurrent,
                icon="document-save-as", text='Save', tooltip="Save the current playlist.")
        self.currentMenuCrop = self.action(self.currentList, self._cropCurrent,
                icon="project-development-close", text='Crop', tooltip="Remove all but the selected songs.")

        # Set the Off icon for the repeat and random buttons.
        icon = self.randomButton.icon()
        icon.addPixmap(
                icon.pixmap(32,32,QIcon.Normal),
                QIcon.Normal,
                QIcon.On)
        icon.addPixmap(
                icon.pixmap(32,32,QIcon.Disabled),
                QIcon.Normal,
                QIcon.Off)
        self.randomButton.setIcon(icon)
        icon = self.repeatButton.icon()
        icon.addPixmap(
                icon.pixmap(32,32,QIcon.Normal),
                QIcon.Normal,
                QIcon.On)
        icon.addPixmap(
                icon.pixmap(32,32,QIcon.Disabled),
                QIcon.Normal,
                QIcon.Off)
        self.repeatButton.setIcon(icon)

    def prepareForUpdate(self):
        '''Causes the current play list to be reloaded from the server'''
        self._temp['oldLength'] = len(self.playQueue)
        scrollBar = self.currentList.verticalScrollBar()
        oldScroll = scrollBar.value()
        self._temp['setBottom'] = oldScroll == scrollBar.maximum()
        self._temp['oldScroll'] = oldScroll

    def updated(self):
        self._setEditing()
        self.view.numSongsLabel.setText(str(len(self.playQueue))+' Songs')
        self._setPlayTime(self.playQueue.totalTime())
        self._resize()
        self.app.processEvents()
        scrollBar = self.currentList.verticalScrollBar()
        if self._temp.get('oldLength') == 0:
            self._ensurePlayingVisable(force=True)
        elif self._temp.get('setBottom'):
            scrollBar.setValue(scrollBar.maximum())
        else:
            scrollBar.setValue(self._temp.get('oldScroll', 0))
        try:
            del self._temp['oldLength']
            del self._temp['setBottom']
            del self._temp['oldScroll']
        except KeyError:
            pass

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.Delete):
            self._removeSelected()
        elif event.key() == Qt.Key_Escape:
            self.currentList.reset()
        else:
            QListView.keyPressEvent(self.currentList, event)

    def _getSelectedRows(self):
        return (self.playQueueProxy.mapToSource(index).row() for index in self.currentList.selectedIndexes())

    def _getSelectedIDs(self):
        return (self.playQueue[row].id for row in self._getSelectedRows())

    def _ensurePlayingVisable(self, force=False):
        if time() - self.playQueue.lastEdit <= 5 and not force:
            return
        if self.currentList.isRowHidden(self.playQueue.playing):
            return
        playing = self.playQueueProxy.mapFromSource(self.playQueue.createIndex(self.playQueue.playing, 0))
        self.currentList.scrollTo(playing, 1) # PositionAtTop
        height = self.currentList.viewport().height()
        scrollBar = self.currentList.verticalScrollBar()
        correction = (height / 8) - self.currentList.rowViewportPosition(self.playQueue.playing)
        new_pos = scrollBar.value() - correction
        scrollBar.setValue(new_pos)

    def _saveCurrent(self):
        '''Save the current playlist'''
        lsinfo = self.mpdclient.lsinfo()
        playlists = []
        for somedict in lsinfo:
            if somedict.get('playlist',None) != None:
                playlists.append(somedict['playlist'])

        (name,ok) = QInputDialog.getItem(self,'Save Playlist','Enter or select the playlist name',playlists,0,True)
        if ok == True:
            if name in playlists:
                self.mpdclient.send('rm', (name,))
            self.mpdclient.send('save', (name,))

    def _clearCurrent(self):
        '''Clear the current playlist'''
        self.mpdclient.send('stop')
        self.mpdclient.send('clear')

    def _removeSelected(self):
        '''Remove the selected item(s) from the current playlist'''
        self._removeSongs(self._getSelectedIDs())
        self.currentList.reset()

    def _cropCurrent(self):
        selection = set(self._getSelectedRows())
        rows = set(xrange(len(self.playQueue)))
        self._removeSongs(self.playQueue[row].id for row in (rows - selection))

    def _removeSongs(self, idList):
        self.mpdclient.send('command_list_ok_begin')
        try:
            for id in idList:
                try:
                    self.mpdclient.send('deleteid', (id,))
                except Exception, e:
                    print e
        finally:
            self.mpdclient.send('command_list_end')

    def _playSong(self, index=None):
        if index is not None:
            if hasattr(index, 'row'):
                row = index.row()
            else:
                row = index
            id = self.playQueue[row].id
        else:
            try:
                id = self._getSelectedIDs().next()
            except StopIteration:
                return
        self.mpdclient.send('playid', (id,))

    def _setPlayTime(self, playTime=0):
        self.view.playTimeLabel.setText('Total play time: %s' % auxilia.formatTime(playTime))

    def _setNumbers(self, value):
        self.config.showNumbers = value
        self.currentList.verticalHeader().setVisible(value)

    def _toggleKeepPlayingVisible(self, value):
        self.config.keepPlayingVisible = value
        if value:
            self._ensurePlayingVisable(force=True)

    def _setOneLinePlaylist(self, value):
        self.config.oneLinePlaylist = value
        self.playQueueDelegate.setOneLine(value)
        self._resize()

    def _resize(self):
        metrics = QFontMetrics(QFont())
        length = 0
        for song in self.playQueue:
            artist = metrics.width(song.artist)
            title = metrics.width(song.title)
            if self.config.oneLinePlaylist:
                length = max(artist + title, length)
            else:
                length = max(artist, title, length)
        width = length + self.playQueueDelegate.height + 4
        header = self.currentList.horizontalHeader()
        header.setMinimumSectionSize(width)
        self.currentList.verticalHeader().setDefaultSectionSize(self.playQueueDelegate.height)

    def _togglePlaylistTools(self, value=None):
        text = ('Show Playlist Tools', 'Hide Playlist Tools')
        if value == None:
            value = not self.playlistTools.isVisible()
        scrollBar = self.currentList.verticalScrollBar()
        scrollValue = scrollBar.value()
        scrollMax = scrollBar.maximum()
        self.playlistTools.setVisible(value)
        self.currentBottom.setArrowType(int(value)+1)
        self.currentBottom.setText(text[value])
        self.config.playlistControls = bool(self.playlistTools.isVisible())
        if scrollValue == scrollMax:
            scrollBar.setValue(scrollBar.maximum())

    def _addStream(self):
        '''Ask the user for the url of the stream to add.'''
        (url,ok) = QInputDialog.getText(self
                , 'Add Stream'
                , 'Please enter the url of the stream you like to add to the playlist.'
                , 0
                , 'Add Stream')
        url = str(url)
        if ok == True and url:
            try:
                adrlist = streamTools.getStreamList(url)
            except streamTools.ParseError:
                print 'error: Could not parse stream address.'
                return
            self.mpdclient.send('command_list_ok_begin')
            try:
                for address in adrlist:
                    self.mpdclient.send('add', (address,))
            finally:
                self.mpdclient.send('command_list_end')

    def _setEditing(self):
        self.playQueue.lastEdit = time()


class PlayQueueDelegate(QItemDelegate):
    ''' Delegate for the playqueue view. This delegate is used to switch between different display styles. '''
    def __init__(self, config):
        QItemDelegate.__init__(self)
        self.setOneLine(config.oneLinePlaylist)

    def setOneLine(self, value):
        self.oneLine = value
        self.height = QFontMetrics(QFont()).height()
        if not value:
            self.height *= 2

    def sizeHint(self, option, index):
        #size = QStyledItemDelegate.sizeHint(self, option, index)
        #print "sizeHint for index:", index.row()
        artist, title = [unicode(val) for val in index.data(Qt.DisplayRole).toStringList()]
        if self.oneLine:
            width = self.height + option.fontMetrics.width(' - '.join((artist, title)))
        else:
            width = self.height + max(option.fontMetrics.width(artist),
                    option.fontMetrics.width(title))
        return QSize(width + 4, self.height)

    def paint(self, painter, option, index):
        #print "painting row:", index.row()
        #QStyledItemDelegate.paint(self, painter, option, index)
        style = option.widget.style()
        style.drawControl(QStyle.CE_ItemViewItem, option, painter)
        artist, title = [unicode(val) for val in index.data(Qt.DisplayRole).toStringList()]
        font = QFont(index.data(Qt.FontRole))
        icon = QIcon(index.data(Qt.DecorationRole))
        painter.setFont(font)
        rect = option.rect
        rect.adjust(1, 0, -2, 0)
        iconSize = self.height - 2
        pixmap = icon.pixmap(iconSize, iconSize)
        left = rect.left() + ((iconSize - pixmap.width()) / 2)
        top = rect.top()+1 + ((iconSize - pixmap.height()) / 2)
        painter.drawPixmap(left, top, pixmap)
        rect.setLeft(rect.left() + iconSize + 2)
        if self.oneLine:
            painter.drawText(rect, Qt.AlignBottom, ' - '.join((artist, title)))
        else:
            painter.drawText(rect, Qt.AlignTop, title)
            painter.drawText(rect, Qt.AlignBottom, artist)

