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
import re
import sys
from PyQt4.QtCore import SIGNAL
from PyQt4.QtGui import QAction, QIcon

DATA_DIR = ''

try:
    if "--nokde" in sys.argv:
        raise ImportError
    from PyKDE4.kdeui import KIcon
    KDE = True
except ImportError:
    KDE = False

locale.setlocale(locale.LC_ALL, "")

def cmpUnicode(a, b):
    return locale.strcoll(a, b)#filter(lambda x: x.isalnum(), a), filter(lambda x: x.isalnum(), b))

def cmpTracks(a, b):
    try:
        return int(re.match('^\d+', a).group()) - int(re.match('^\d+', b).group())
    except:
        return cmpUnicode(a, b)

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
        self.connect(action, SIGNAL('triggered()'), slot)

def PIcon(icon):
    if KDE:
        return KIcon(icon)
    else:
        return QIcon(DATA_DIR+'icons/%s.png' % icon)

def formatTime(seconds):
    seconds = int(seconds)
    form = '%i'
    result = []
    units = (60*60*24, 60*60, 60)
    for size in units:
        if seconds > size-1 or form == '%02i':
            count = seconds / size
            seconds -= (count * size)
            result.append(form % count)
            form = '%02i'
    result.append('%02i' % seconds)
    if len(result) < 2:
        result.insert(0, '0')
    return ':'.join(result)

