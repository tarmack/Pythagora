# -*- coding: utf-8 -*-
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
from PyQt4.QtCore import QObject, SIGNAL, QTimer

import mpdlibrary

class PlayerState(QObject):
    '''
    Manages the player state and information.
    '''
    _state = {
            'progress':     mpdlibrary.Time(0),
            'playState':    '',
            'volume':       0,
            'xFade':        0,
            'bitrate':      0,
            'random':       False,
            'repeat':       False,
            'single':       False,
            'consume':      False,
            }
    def __init__(self, playQueue):
        QObject.__init__(self)
        self.playQueue = playQueue
        self._progressTimer = QTimer()
        self._progressTimer.start(1000)
        self.connect(self._progressTimer, SIGNAL('timeout()'), self._updateProgress)
        self.connect(self.playQueue, SIGNAL('currentSongChanged'), self, SIGNAL('currentSongChanged'))

    def __getattr__(self, attr):
        try:
            return self._state[attr]
        except KeyError:
            raise AttributeError("'%s' object has no attribute '%s'" %
                                 (self.__class__.__name__, attr))

    def __setattr__(self, attr, value):
        if attr == 'progress':
            if not isinstance(value, mpdlibrary.Time):
                value = mpdlibrary.Time(value)
        # Integer values.
        elif attr in ('volume', 'xFade', 'bitrate'):
            value = int(value)
        # boolean values.
        elif attr in ('random', 'repeat', 'single', 'consume'):
            value = bool(int(value))

        try:
            oldValue = self._state[attr]
        except KeyError:
            QObject.__setattr__(self, attr, value)
            return
        self._state[attr] = value
        if value != oldValue:
            self.emit(SIGNAL(attr+'Changed'), value)

    @property
    def currentSong(self):
        '''
        Returns the Song object from the play queue of the current song.
        '''
        if self.playQueue.playing is None:
            return None
        else:
            return self.playQueue[self.playQueue.playing]

    def _updateProgress(self):
        self.progress = self.progress + 1

