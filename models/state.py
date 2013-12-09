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
    _default_state = {
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
    def __init__(self, mpdclient, playQueue):
        QObject.__init__(self)
        self.mpdclient = mpdclient
        self.playQueue = playQueue
        self.reset()
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
        if attr not in self._default_state:
            return QObject.__setattr__(self, attr, value)
        if attr == 'playState':
            if value in ('play', 'stop'):
                self.mpdclient.send(value)
            elif value == 'pause':
                self.mpdclient.send(value, (1,))
            else:
                raise AttributeError('playState can only be set to "play", "pause" of "stop". Got %s instead.' % value)
        elif attr == 'progress':
            self.mpdclient.send('seekid', (self.playQueue.playing, value))
        else:
            if attr == 'xFade':
                attr = 'crossfade'
            elif attr == 'volume':
                attr = 'setvol'
                self._setState('volume', value)
            elif attr in ('random', 'repeat', 'single', 'consume'):
                value = int(value)
            self.mpdclient.send(attr, (value,))

    def _setState(self, item, value):
        if item == 'progress':
            if not isinstance(value, mpdlibrary.Time):
                value = mpdlibrary.Time(value)
        # Integer values.
        elif item in ('volume', 'xFade', 'bitrate'):
            value = int(value)
            if item == 'volume' and value > 0:
                self._muteVolume = 0
        # boolean values.
        elif item in ('random', 'repeat', 'single', 'consume'):
            value = bool(int(value))

        oldValue = self._state[item]
        self._state[item] = value
        if value != oldValue:
            self.emit(SIGNAL(item+'Changed'), value)

    def reset(self):
        self.playQueue.setPlaying(None)
        self._state = self._default_state.copy()
        self._muteVolume = 0

    def update(self, status):
        self._setState('progress', status.get('time', '0:0').split(':')[0])
        self._setState('playState', status['state'])
        self._setState('volume', status['volume'])
        self._setState('xFade', status.get('xfade', 0))
        self._setState('bitrate', status.get('bitrate', 0))
        self._setState('random', status['random'])
        self._setState('repeat', status['repeat'])
        self._setState('single', status['single'])
        self._setState('consume', status['consume'])

    def _updateProgress(self):
        if self.playState == 'play':
            self._setState('progress', self.progress + 1)


    #########################
    # Convenience methods. #
    #########################
    @property
    def currentSong(self):
        '''
        Returns the Song object from the play queue of the current song.
        '''
        if self.playQueue.playing is None:
            return None
        else:
            index = self.playQueue.id_index(self.playQueue.playing)
            return self.playQueue[index]

    @currentSong.setter
    def currentSong(self, value):
        if isinstance(value, int):
            self.mpdclient.send('seek', (value, 0))
        elif isinstance(value, mpdlibrary.Song):
            self.mpdclient.send('seekid', (value.id, 0))
        else:
            raise AttributeError('currentSong only accepts int or mpdlibrary.Song. Got %s instead.' % type(value))

    def playPause(self):
        if self._state['playState'] == 'play':
            self.playState = 'pause'
        else:
            self.playState = 'play'

    def play(self):
        self.playState = 'play'

    def stop(self):
        self.playState = 'stop'

    def nextSong(self):
        self.mpdclient.send('next')

    def previousSong(self):
        self.mpdclient.send('previous')

    def volumeUp(self, amount=2):
        value = self._state['volume'] + amount
        self.volume = value

    def volumeDown(self, amount=2):
        value = self._state['volume'] - amount
        self.volume = value

    def setVolume(self, value):
        self.volume = value

    def setRandom(self, value):
        self.random = value

    def setRepeat(self, value):
        self.repeat = value

    def setSingle(self, value):
        self.single = value

    def setXFade(self, value):
        self.xFade = value

    def setConsume(self, value):
        self.consume = value

    def seek(self, value):
        self.progress = value

    def mute(self):
        if self._muteVolume:
            self.volume = self._muteVolume
            self._muteVolume = 0
        else:
            self._muteVolume = self.volume
            self.volume = 0
