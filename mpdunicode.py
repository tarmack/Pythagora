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
# This module subclasses the python-mpd module of J.A. Treuman to give it
# Support for unicode strings. It will transform all value strings to unicode
# but leaves the dictionary keys alone. 
# It also ads support for the idle, noidle and rescan commands, which seem to
# be missing in the original implementation.
# 
# Because it is implemented as a proxy class it is fully transparent. With this
# wrapper it is possible to make your application support unicode without much
# hassle. "import mpdunicode as mpd" in existing code should do the trick.
#-------------------------------------------------------------------------------
from mpd import *

class MPDClient(MPDClient):
    ''' This proxy class wraps round the python-mpd module.
    It converts the dictionary values in the output to unicode
    objects and adds support for unicode input.  It also ads
    support for some missing commands including the idle
    command and friends.
    '''
    def __init__(self, code='utf-8'):
        self.code = code
        self._idle = False
        super(MPDClient, self).__init__()
        self._commands.update({'rescan': self._getitem
                              ,'single': self._getnone
                              ,'consume': self._getnone
                              })

    def idle(self, subsystems=[], timeout=None):
        ''' Calls the idle command on the server and blocks until
        mpd signals with changes or timeout expires. It returns a
        list with the subsystems that had changes.
        '''
        if self._commandlist is not None:
            raise CommandListError("idle not allowed in command list")
        if self._idle:
            raise ProtocolError('Already in idle mode.')
        self._idle = True
        oldTimeout = self._sock.gettimeout()
        if timeout is not None:
            self._sock.settimeout(timeout)
        try:
            rtn = self._docommand('idle', subsystems, self._getlist)
        except socket.timeout:
            try:
                rtn = self.noidle()
            except socket.timeout:
                raise ConnectionError("Connection timed out")
        finally:
            self._sock.settimeout(oldTimeout)
            self._idle = False
        return rtn

    def noidle(self):
        if not self._idle:
            raise ProtocolError('Not in idle mode')
        self._idle = False
        return self._docommand('noidle', [], self._getlist)

    def _writecommand(self, command, args=[]):
        if self._idle and command not in ('idle', 'noidle'):
            raise ProtocolError('%s not allowed in idle mode.' % command)
        args = [unicode(arg).encode(self.code) for arg in args]
        super(MPDClient, self)._writecommand(command, args)

    def _readitem(self, separator):
        item = super(MPDClient, self)._readitem(separator)
        if item:
            item[1] = item[1].decode(self.code)
        return item

    def _reset(self):
        self._idle = False
        super(MPDClient, self)._reset()

