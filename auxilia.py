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
import locale
import os
import re
from PyQt4.QtCore import SIGNAL, Qt, QObject, QEvent, QTimer
from PyQt4.QtGui import QAction, QWidgetAction, QToolButton, QTabBar

locale.setlocale(locale.LC_ALL, "")

def songTitle(song):
    return song.get('title', song.get('name', song['file']))

def songArtist(song):
    return song.get('artist', song.get('performer', song.get('composer', '?')))

def songTime(song):
    stime = int(song.get('time', '0'))
    tmin = stime / 60
    tsec = stime - tmin * 60
    return '%i:%02i' % (tmin, tsec)

def cmpUnicode(a, b):
    return locale.strcoll(a, b)#filter(lambda x: x.isalnum(), a), filter(lambda x: x.isalnum(), b))

def cmpTracks(a, b):
    try:
        return int(re.match('^\d+', a).group()) - int(re.match('^\d+', b).group())
    except:
        return cmpUnicode(a, b)

def fileName(name):
    return filter(lambda x: x != '/' , name)

# Actions
#==============================================================================

class Actions:
    def actionPlayAdd(self, parent, slot):
        return self.action(parent, slot\
                , "media-playback-start"\
                , 'Add and play'\
                , 'Add song to playlist and start playing it.')

    def actionPlayReplace(self, parent, slot):
        return self.action(parent, slot\
                , "media-playback-start"\
                , 'Replace and play'\
                , 'Replace the playlist with the selection and start playing.')

    def actionAddSongs(self, parent, slot):
        return self.action(parent, slot\
        , "list-add"\
        , 'Add to playlist'\
        , 'Add the selection to the playlist.')

    def actionJumpArtist(self, parent, slot):
        return self.action(parent, slot\
        , "go-jump"\
        , 'Jump to artist'\
        , 'Jump to all songs from the selected artist in the library.')

    def actionJumpAlbum(self, parent, slot):
        return self.action(parent, slot\
        , "go-jump"\
        , 'Jump to album'\
        , 'Jump to all songs from the selected album in the library.')

    def actionLoad(self, parent, slot):
        return self.action(parent, slot\
        , "document-send"\
        , 'Load playlist'\
        , 'Replace the current playlist.')

    def actionRemove(self, parent, slot):
        return self.action(parent, slot\
        , "list-remove"\
        , 'Remove'\
        , 'Remove selected.')

    def actionLibReload(self, parent, slot):
        return self.action(parent, slot\
        , 'view-refresh'\
        , 'Reload library'\
        , 'Reload the music library from the server.')

    def actionLibUpdate(self, parent, slot):
        return self.action(parent, slot\
        , 'folder-sync'\
        , 'Update library'\
        , 'Update the music database with new and changed files')

    def actionLibRescan(self, parent, slot):
        return self.action(parent, slot\
        , 'folder-sync'\
        , 'Rescan library'\
        , 'Rescan all files in the music directory.')

    def actionBookmark(self, parent, slot):
        return self.action(parent, slot\
        , 'document-save-as'\
        , 'Bookmark Station'\
        , 'Add the station to the bookmarks list.')

    def actionPreview(self, parent, slot):
        return self.action(parent, slot\
        , 'media-playback-start'\
        , 'Preview'\
        , 'Start listening to the station right away.')

    def actionPlayBM(self, parent, slot):
        return self.action(parent, slot\
        , 'media-playback-start'\
        , 'Play'\
        , 'Start listening to the station.')

    def actionScReload(self, parent, slot):
        return self.action(parent, slot\
        , 'view-refresh'\
        , 'Reload'\
        , 'Reload the genre list.')

    #def action(self, parent, slot):
    #    return self.action(parent, slot\
    #    , ''\
    #    , ''\
    #    , '')

    def actionHideRestore(self, parent, slot):
        return self.action(parent, slot\
        , text='Hide'\
        , tooltip='Hide application window in the systemtray.')

    def action(self, parent, slot, icon=None, text='', tooltip=None):
        action = QAction(text, parent)
        if type(icon) == str:
            action.setIcon(PIcon(icon))
        if type(tooltip) == str:
            action.setToolTip(tooltip)
        self.__addAction(action, parent, slot)
        return action

    def __addAction(self, action, parent, slot):
        parent.addAction(action)
        self.view.connect(action, SIGNAL('triggered()'), slot)

    def menuTitle(self, icon, text):
        self.eventEater = EventEater()
        buttonaction = QAction(self.view)
        font = buttonaction.font()
        font.setBold(True)
        buttonaction.setFont(font)
        buttonaction.setText(text)
        buttonaction.setIcon(icon)

        action = QWidgetAction(self.view)
        action.setObjectName('trayMenuTitle')
        titleButton = QToolButton(self.view)
        titleButton.installEventFilter(self.eventEater)
        titleButton.setDefaultAction(buttonaction)
        titleButton.setDown(True)
        titleButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        action.setDefaultWidget(titleButton)

        return action

class EventEater(QObject):
    def eventFilter(self, reciever, event):
        if event.type() == QEvent.MouseButtonPress or event.type() == QEvent.MouseButtonRelease:
            return True
        return False


class DragNDrop:
    # TODO: large drops shoud give busy cursor.
    def dropSong(self, event, pos):
        event.accept()
        itemList = [x.song['file'] for x in event.source().selectedItems()]
        self.addDrop(itemList, pos)

    def dropArtist(self, event, pos):
        event.accept()
        itemList = self.__buildList(event, 'artist')
        self.addDrop(itemList, pos)

    def dropAlbum(self, event, pos):
        event.accept()
        itemList = self.__buildList(event, 'album')
        self.addDrop(itemList, pos)

    def dropPlaylist(self, event, pos):
        event.accept()
        # Get the name of the droped playlist.
        playlist = unicode(event.source().selectedItems()[0].text())
        # Build a list of the songs.
        itemList = (song['file'] for song in self.mpdclient.listplaylistinfo(playlist))
        self.addDrop(itemList, pos)

    def dropFile(self, event, pos):
        pathlist = []
        event.accept()
        itemList = event.source().selectedItems()
        #itemList = [unicode(x.text(0)) for x in source.selectedItems()]
        for item in itemList:
            # Select all chindren of parents.
            if item.childCount():
                itemList.extend([item.child(x) for x in xrange(item.childCount())])
            # Extract the full path from the parents.
            else:
                path = ''
                while item:
                    try:
                        text = unicode(item.text(0))
                        path = os.path.join(text, path)
                    except:
                        pass
                    item = item.parent()
                else:
                    pathlist.append(path[:-1])
        self.addDrop(pathlist, pos)

    def __buildList(self, event, key):
        fileList = []
        selection = (unicode(x.text()) for x in event.source().selectedItems())
        for value in selection:
            songList = self.mpdclient.find(key, value)
            songList.sort(cmpTracks, lambda song:song.get('track',''))
            songList.sort(cmpUnicode, lambda song:song.get('album',''))
            fileList.extend([x['file'] for x in songList])
        return fileList

def PIcon(icon):
    try:
        from PyKDE4.kdeui import KIcon
        return KIcon(icon)
    except ImportError:
        from PyQt4.QtGui import QIcon
        return QIcon('icons/%s.png' % icon)

class StatusTabBar(QTabBar):
    def __init__(self):
        QTabBar.__init__(self)
        self.tabTimer = QTimer()
        self.connect(self.tabTimer, SIGNAL('timeout()'), self.__selectTab)
        self.setAcceptDrops(True)

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
        index = self.tabAt(self.tabPos)
        self.setCurrentIndex(index)
        self.tabTimer.stop()

