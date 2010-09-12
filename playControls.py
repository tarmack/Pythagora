# -*- coding: utf-8 -*
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
from PyQt4.QtCore import SIGNAL

class PlayControls:
    currentVolume = 0
    oldVolume = 0
    def __init__(self, mpdclient):
        self.mpdclient = mpdclient

    def playPause(self):
        try:
            state = self.mpdclient.status()['state']
            if state == 'play':
                self.mpdclient.send('pause', (1,))
            elif state == 'pause':
                self.mpdclient.send('pause', (0,))
            else:
                self.mpdclient.send('play')
        except:
            pass

    def back(self):
        try:
            self.mpdclient.send('previous')
        except:
            pass

    def stop(self):
        try:
            self.mpdclient.send('stop')
        except:
            pass

    def forward(self):
        try:
            self.mpdclient.send('next')
        except:
            pass

    def setRandom(self, value):
        self.mpdclient.send('random', (int(value),))

    def setRepeat(self, value):
        self.mpdclient.send('repeat', (int(value),))

    def setCrossFade(self, value):
        self.mpdclient.send('crossfade', (value,))

    def volumeUp(self, value=2):
        print 'debug: volup'
        self.mpdclient.send('volume', (value,))

    def volumeDown(self, value=2):
        print 'debug: voldown'
        self.mpdclient.send('volume', (-value,))

    def setVolume(self,value):
        '''Change the volume'''
        if value != self.currentVolume:
            try:
                self.mpdclient.send('volume', (value - self.currentVolume,))
            except:
                pass
            self.currentVolume = value

    def toggleMute(self):
        if self.currentVolume == 0:
            self.setVolume(self.oldVolume)
        else:
            self.oldVolume = self.currentVolume
            self.setVolume(0)

    def connectSignals(self, view):
        view.connect(view.playerForm.play, SIGNAL('clicked(bool)'), self.playPause)
        view.connect(view.playerForm.back, SIGNAL('clicked(bool)'), self.back)
        view.connect(view.playerForm.forward, SIGNAL('clicked(bool)'), self.forward)
        view.connect(view.playerForm.stop, SIGNAL('clicked(bool)'), self.stop)
        view.connect(view.playerForm.volume, SIGNAL('valueChanged(int)'), self.setVolume)
        view.connect(view.currentList.crossFade, SIGNAL('valueChanged(int)'), self.setCrossFade)
        view.connect(view.currentList.repeatButton, SIGNAL('toggled(bool)'), self.setRepeat)
        view.connect(view.currentList.randomButton, SIGNAL('toggled(bool)'), self.setRandom)
