# -*- coding: utf-8 -*
#-------------------------------------------------------------------------------{{{
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
#-------------------------------------------------------------------------------}}}
from PyQt4.QtCore import SIGNAL

class PlayControls:#{{{1
    currentVolume = 0
    oldVolume = 0
    def __init__(self, mpdclient):#{{{2
        self.mpdclient = mpdclient

    def playPause(self):#{{{2
        try:
            state = self.mpdclient.status()['state']
            if state == 'play':
                self.mpdclient.pause(1)
            elif state == 'pause':
                self.mpdclient.pause(0)
            else:
                self.mpdclient.play()
        except:
            pass

    def back(self):#{{{2
        try:
            self.mpdclient.previous()
        except:
            pass

    def stop(self):#{{{2
        try:
            self.mpdclient.stop()
        except:
            pass

    def forward(self):#{{{2
        try:
            self.mpdclient.next()
        except:
            pass

    def setRandom(self, value):#{{{2
        self.mpdclient.random(int(value))

    def setRepeat(self, value):#{{{2
        self.mpdclient.repeat(int(value))

    def setCrossFade(self, value):#{{{2
        self.mpdclient.crossfade(value)

    def volumeUp(self, value=2):#{{{2
        self.setVolume(self.currentVolume + value)

    def volumeDown(self, value=2):#{{{2
        self.setVolume(self.currentVolume - value)

    def setVolume(self,value):#{{{2
        '''Change the volume'''
        if value != self.currentVolume:
            try:
                self.mpdclient.volume(value - self.currentVolume)
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
        view.connect(view.play, SIGNAL('clicked(bool)'), self.playPause)
        view.connect(view.back, SIGNAL('clicked(bool)'), self.back)
        view.connect(view.forward, SIGNAL('clicked(bool)'), self.forward)
        view.connect(view.stop, SIGNAL('clicked(bool)'), self.stop)
        view.connect(view.volume, SIGNAL('valueChanged(int)'), self.setVolume)
        view.connect(view.crossFade, SIGNAL('valueChanged(int)'), self.setCrossFade)
        view.connect(view.repeatButton, SIGNAL('toggled(bool)'), self.setRepeat)
        view.connect(view.randomButton, SIGNAL('toggled(bool)'), self.setRandom)
