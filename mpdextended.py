# -*- coding: utf-8 -*
#------------------------------------------------------------------------------
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
#------------------------------------------------------------------------------
# This module is intended as an extension on the mpdunicode module. It can be
# used to offload the mpd communication in a separate thread via the send
# method.  It will execute the callback function given in the third argument
# with the answer from the mpd server.
# The callback function is run from the spawned thread so make sure it only
# calls thread safe code, for instance set an event in your favorite event
# handler.
# The module maps the standard MPDClient methods, so you can still directly
# call to the protocol methods and they will be blocking. Please note that it
# is currently not safe to call blocking commands from multiple threads.
# Also note that the threaded idle mode deviates from the protocol by
# allowing any command while in idle mode. If the server is in idle mode any
# command other than noidle will be transparently prepended with the noidle
# command. This is done to make your life easier.
#------------------------------------------------------------------------------
import mpdunicode
import threading
import Queue
import sys

class MPDClient():
    '''This proxy class wraps round the mpdunicode module.
    '''
    def __init__(self):
        self.connection = MPDThread(None, None, None, None)

    def __getattr__(self, command):
        if hasattr(self.connection, command):
            return lambda *args: self.send(command, args, False)

    def send(self, command, args=(), callback=None, callbackArgs=None):
        self.connection.send(command, args, callback, callbackArgs)
        if callback == False:
            value = self.connection.returnQueue.get()
            if isinstance(value, Exception):
                raise value
            else:
                return value

    def connect(self, server, port, callback=False, callbackArgs=None):
        self.connection = MPDThread(server, port, callback, callbackArgs)

    def connected(self):
        if self.connection.connecting:
            return False
        if self.connection._sock:
            try:
                self.ping()
                return True
            except:
                try:
                    self.disconnect()
                except:
                    pass
                return False
        else: return False

class MPDThread(mpdunicode.MPDClient, threading.Thread):
    def __init__(self, server, port, callback, callbackArgs):
        threading.Thread.__init__(self)
        self.daemon = True
        self.queue = Queue.Queue()
        self.returnQueue = Queue.Queue(1)
        self._lock = threading.RLock()
        super(MPDThread, self).__init__()
        self.connecting = False
        if server != None:
            self.connecting = True
            self.send('connect', (server, port), callback, callbackArgs)

    def send(self, command, args=(), callback=None, callbackArgs=None):
        if not self.is_alive():
            self.start()
        self.queue.put((command, args, callback, callbackArgs))
        if command != 'noidle' and self._idle:
            self._writecommand('noidle', [])

    def run(self):
        while True:
            command, args, callback, callbackArgs = self.queue.get()
            print 'debug: got ', command, ' with arguments ', args, 'from queue.'
            try:
                value = self.__do(command, args)
            except mpdunicode.ConnectionError, e:
                print 'debug: MPD thread - ConnectionError: ', e, '\n', sys.exc_info()
                value = mpdunicode.ConnectionError(e)
            except mpdunicode.CommandListError, e:
                print 'debug: MPD thread - CommandListError: ', e, '\n', sys.exc_info()
                value = mpdunicode.CommandListError(e)
            except Exception, e:
                print 'debug: MPD thread - Exception: ', e, '\n', sys.exc_info()
                value = sys.exc_info()[0]
            if command == 'connect':
                self.connecting = False
            if callback == False:
                self.returnQueue.put(value)
            elif callback == None:
                continue
            elif callbackArgs == None:
                callback(value)
            else:
                callback(value, *callbackArgs)

    def __do(self, command, args):
        try:
            function = self.__getattribute__(command)
        except AttributeError:
            function = self.__getattr__(command)
        return function(*args)

    def _docommand(self, command, args, retval):
        if command not in ('idle', 'noidle') and self._idle:
            self._writecommand('noidle', [])
        with self._lock:
            return super(MPDThread, self)._docommand(command, args, retval)

    def _writecommand(self, command, args=[]):
        if command.startswith('command_list') and self._idle:
            self._writecommand('noidle', [])
            with self._lock:
                super(MPDThread, self)._writecommand(command, args)
        else:
            super(MPDThread, self)._writecommand(command, args)

