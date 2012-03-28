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
from PyQt4.QtCore import SIGNAL, Qt, QModelIndex, QMimeData
from PyQt4.QtGui import QMessageBox, QKeySequence, QListView, QTableView, QFontMetrics, QFont
from PyQt4 import uic

import auxilia
import PluginBase

DATA_DIR = ''

def getWidget(modelManager, mpdclient, config, library):
    return PlaylistForm(modelManager, mpdclient, config, library)

class PlaylistForm(PluginBase.PluginBase, auxilia.Actions):
    '''Display and manage the currently known playlists.'''
    moduleName = '&PlayLists'
    moduleIcon = 'document-multiple'

    def load(self):
        self.playlistModel = self.modelManager.playlists
        self.playQueue = self.modelManager.playQueue
        # Load and place the stored playlists form.
        if self.config.KDE:
            uic.loadUi(DATA_DIR+'ui/PlaylistsForm.ui', self)
        else:
            uic.loadUi(DATA_DIR+'ui/PlaylistsForm.ui.Qt', self)
        self.playlistSplitter.setSizes(self.config.playlistSplit)

        # Playlist list
        self.playlistList.setModel(self.playlistModel)
        self.playlistList.keyPressEvent = self._listKeyPressEvent
        self.connect(self.playlistList.selectionModel(),
                SIGNAL('currentChanged(const QModelIndex &, const QModelIndex &)'),
                self.songList.setRootIndex)
        self.connect(self.playlistList, SIGNAL('itemDoubleClicked(QListWidgetItem*)'), self._addList)
        # Create actions.
        self.playlistListPlayAdd = self.actionPlayAdd(self.playlistList, self._addPlayList)
        self.playlistListPlayReplace = self.actionPlayReplace(self.playlistList, self._loadPlayList)
        self.playlistListAdd = self.actionAddSongs(self.playlistList, self._addList)
        self.playlistListReplace = self.actionLoad(self.playlistList, self._loadList)
        self.playlistListRemove = self.actionRemove(self.playlistList, self._deleteList)

        # Song list
        self.songList.setModel(self.playlistModel)
        self.songList.setColumnHidden(0, True)
        self.songList.horizontalHeader().setResizeMode(3) # QHeaderView::ResizeToContents
        self.songList.verticalHeader().setDefaultSectionSize(QFontMetrics(QFont()).height())
        self.songList.keyPressEvent = self._songKeyPressEvent
        # Create actions.
        self.songListPlayAdd = self.actionPlayAdd(self.songList, self._addPlaySongs)
        self.songListPlayReplace = self.actionPlayReplace(self.songList, self._clearPlaySong)
        self.songListAdd = self.actionAddSongs(self.songList, self._addSongs)
        self.songListRemove = self.actionRemove(self.songList, self._removeSongs)

        # overload new button dropEvent()
        self.newButton.dragEnterEvent = self._newListDragEnterEvent
        self.newButton.dropEvent = self._newListDropEvent

        # Connect to the buttons.
        self.connect(self.newButton, SIGNAL('clicked()'), self._newList)
        self.connect(self.loadButton, SIGNAL('clicked()'), self._loadList)
        self.connect(self.deleteButton, SIGNAL('clicked()'), self._deleteList)
        self.connect(self.playlistSplitter, SIGNAL('splitterMoved(int, int)'), self._storeSplitter)


    def _listKeyPressEvent(self, event):
        if event.matches(QKeySequence.Delete):
            self._deleteList()
        elif event.key() == Qt.Key_Escape:
            self.playlistList.setCurrentIndex(QModelIndex())
        else:
            QListView.keyPressEvent(self.playlistList, event)

    def _songKeyPressEvent(self, event):
        if event.matches(QKeySequence.Delete):
            self._removeSongs()
        elif event.key() == Qt.Key_Escape:
            self.songList.setCurrentIndex(QModelIndex())
        else:
            QTableView.keyPressEvent(self.songList, event)

    def _newListDragEnterEvent(self, event):
        if event.provides('mpd/uri'):
            event.accept()

    def _newListDropEvent(self, event):
        if event.provides('mpd/uri'):
            event.accept()
            parent = self._newList()
            data = QMimeData()
            data.setData('mpd/uri', event.mimeData().data('mpd/uri'))

            def disconnect(item, row=-1, column=-1):
                if parent.row() == row:
                    self.disconnect(self.playlistList.itemDelegate(parent),
                            SIGNAL('commitData(QWidget *)'),
                            addSongs)
                    self.disconnect(self.playlistModel,
                            SIGNAL('rowsAboutToBeRemoved(const QModelIndex &, int , int)'),
                            disconnect)

            def addSongs(editor, data=data):
                # Make sure to disconnect from the signals.
                if parent.data(Qt.DisplayRole):
                    disconnect(None, parent.row())
                    self.playlistModel.dropMimeData(data, Qt.CopyAction, 0, 0, parent)

            self.connect(self.playlistList.itemDelegate(parent),
                    SIGNAL('commitData(QWidget *)'),
                    addSongs)
            self.connect(self.playlistModel,
                    SIGNAL('rowsAboutToBeRemoved(const QModelIndex &, int , int)'),
                    disconnect)

    def _getSelectedPlaylist(self):
        try:
            index = self.playlistList.selectionModel().selectedIndexes()[0]
        except ValueError:
            return
        return self.playlistModel.data(index, Qt.DisplayRole)

    def _getSelectedSongs(self):
        playlist = self.playlistModel[self._getSelectedPlaylist()]
        return (playlist[index.row()] for index in self.songList.selectedIndexes() if index.column() == 1)

    def _newList(self):
        ''' Insert a new row in the list of playlists and open the editor on it. '''
        self.playlistModel.insertRow(0, QModelIndex())
        index = self.playlistModel.index(0, 0, QModelIndex())
        self.playlistList.setCurrentIndex(index)
        self.playlistList.edit(index)
        return index

    def _deleteList(self):
        '''Delete the currently selected playlist.'''
        name = self._getSelectedPlaylist()
        resp = QMessageBox.question(self,
                'Delete Playlist',
                'Are you sure you want to delete '+name,
                QMessageBox.Yes|QMessageBox.No,
                QMessageBox.No)
        if resp == QMessageBox.Yes:
            del self.playlistModel[name]
            self.playlistList.setCurrentIndex(QModelIndex())

    def _removeSongs(self):
        name = self._getSelectedPlaylist()
        if name is None:
            return
        playlist = self.playlistModel[name]
        indexList = sorted(index.row() for index in self.songList.selectedIndexes() if index.column() == 1)
        start = indexList.pop(0)
        end = start + 1
        for index in indexList:
            if index != end:
                del playlist[start:end]
                start = index
            end = index + 1
        del playlist[start:end]

    def _loadPlayList(self):
        self._loadList()
        self.modelManager.playerState.play()

    def _addPlayList(self):
        last = len(self.playQueue)
        self._addList()
        self.modelManager.playerState.currentSong = last
        self.modelManager.playerState.play()

    def _loadList(self):
        '''Load the currently selected playlist onto the server.
           Note: this operation clears the current playlist.
        '''
        self.playQueue.clear()
        self._addList()

    def _addList(self):
        '''Load the currently selected playlist onto the server.
        '''
        name = self._getSelectedPlaylist()
        self.playlistModel.loadPlaylist(name)

    def _addSongs(self):
        self.playQueue.extend(self._getSelectedSongs())

    def _addPlaySongs(self):
        last = len(self.playQueue)
        self._addSongs()
        self.modelManager.playerState.currentSong = last
        self.modelManager.playerState.play()

    def _clearPlaySong(self):
        self.playQueue.clear()
        self._addPlaySongs()

    def _storeSplitter(self):
        self.config.playlistSplit = self.playlistSplitter.sizes()

