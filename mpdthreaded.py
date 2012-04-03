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
# This module is intended as an extension on the mpdunicode or the python-mpd
# module of J.A. Treuman. It can be used to offload the mpd communication in a
# separate thread via the send method. It will execute the callback function
# given in the 'callback' argument with the answer from the mpd server.
# The callback function is run from the spawned thread so make sure it only
# calls thread safe code, for instance set an event in your favorite event
# handler.
# The module maps the standard MPDClient methods, so you can still directly
# call to the protocol methods and they will block waiting for the results.
# Please note that the threaded idle mode deviates from the protocol by
# allowing any command while in idle mode. If the server is in idle mode any
# command other than noidle will be transparently prepended with the noidle
# command. This is done to make your life easier.
#------------------------------------------------------------------------------
try:
    from mpdunicode import *
    from mpdunicode import MPDClient as MPDClientBase
except ImportError:
    from mpd import *
    from mpd import MPDClient as MPDClientBase
import threading
import Queue
import sys

class MPDClient(object):
    '''This proxy class wraps round the mpd(unicode) module. It supplies a
    threaded interface to the mpd server on top of the normal methods in the
    mpd module.
    If an exception is raised in the spawned tread this exception is given as
    the first argument to the callback function.
    '''
    def __init__(self):
        self._connection = None
        self._blocked_event = threading.Event()
        self._blocked_value = None

    def __getattr__(self, command):
        if hasattr(self._connection, command):
            if self.connected():
                return lambda *args: self._doBlocking(command, args)
            else:
                raise ConnectionError('Not connected.')
        else:
            raise AttributeError("'%s' object has no attribute '%s'" %
                                 (self.__class__.__name__, command))

    def send(self, command, args=(), callback=None, callbackArgs=()):
        '''Put the command on the command queue.
        If supplied the callback argument is called with the results as its
        first argument and additional arguments from the tuple given in
        callbackArgs.
        '''
        self._connection.send(command, args, callback, callbackArgs)

    def _doBlocking(self, command, args):
        '''Sends the command to the mpd server and blocks until the results are
        available.
        '''
        print 'debug: blocking on', command, ' with arguments ', args
        if not self.connected():
            raise ConnectionError('Not connected')
        self.send(command, args, callback=self._returnBlocking)
        self._blocked_event.wait()
        value = self._blocked_value
        self._blocked_value = None
        self._blocked_event.clear()
        return value

    def _returnBlocking(self, value):
        self._blocked_value = value
        self._blocked_event.set()

    def connect(self, server, port, callback=None, callbackArgs=()):
        '''Spawn a new connection thread connected to server on port.
        When a connection is established or an error occurred the function
        given as callback is called.
        '''
        try:
            self._connection.abort = True
        except AttributeError:
            pass
        self._connection = MPDThread(server, port, callback, callbackArgs)

    def connected(self):
        '''Returns True when the connection thread is running and has
        established a connection.
        '''
        return self._connection and self._connection.is_alive() and not self._connection.connecting

    def disconnect(self):
        '''Closes the current connection and exits the thread.
        If a command is currently being executed the thread will exit after all
        work for that command is done. It will discard any subsequent commands
        in the queue.
        '''
        self._connection.abort = True
        self._connection.send('close', (), None, ())

class MPDThread(MPDClientBase, threading.Thread):
    '''This class represents the interface thread to the mpd server.
    '''
    _idle = False
    def __init__(self, server, port, callback, callbackArgs):
        threading.Thread.__init__(self)
        self.daemon = True
        self.queue = Queue.PriorityQueue(256)
        self._lock = threading.Lock()
        MPDClientBase.__init__(self)
        self.connecting = False
        self.exit = False
        self.abort = False
        self.priority = 0
        self.callbackQueue = Queue.Queue()
        self.callbackThread = CallbackThread(self.callbackQueue)
        if server != None:
            self.connecting = True
            self.send('connect', (server, port), callback, callbackArgs)
            self.start()

    def send(self, command, args, callback, callbackArgs):
        '''Put the command on the command queue.
        If supplied the callback argument is called with the results as its
        first argument and additional arguments from the tuple given in
        callbackArgs.
        '''
        if self.queue.empty():
            self.priority = 0
        self.priority += 1
        priority = self.priority
        if command == 'idle':
            priority += 256
        with self._lock:
            if not (command == 'idle' and self._idle):
                self.queue.put((priority, command, args, callback, callbackArgs))
                if command != 'noidle' and self._idle:
                    self._write_proxy('noidle', [])

    def idle(self, subsystems=[], timeout=None):
        ''' Calls the idle command on the server and blocks until
        mpd signals with changes or timeout expires. It returns a
        list with the subsystems that had changes.
        '''
        if self._idle:
            raise ProtocolError('Already in idle mode.')
        self._idle = True
        oldTimeout = self._sock.gettimeout()
        if timeout is not None:
            self._sock.settimeout(timeout)
        try:
            self._lock.release()
            rtn = self._execute('idle', subsystems)
        except socket.timeout:
            try:
                if self._commands['noidle'] is None:
                    if hasattr(MPDClientBase, '_getlist'):
                        self._commands['noidle'] = self._getlist
                    else:
                        self._commands['noidle'] = self._fetch_list
                rtn = self.noidle()
                self._commands['noidle'] = None
                if rtn == []:
                    rtn = ['timeout']
            except socket.timeout:
                raise ConnectionError("Connection timed out")
        finally:
            self._lock.acquire()
            self._sock.settimeout(oldTimeout)
            self._idle = False
        return rtn

    def run(self):
        while True:
            _, command, args, callback, callbackArgs = self.queue.get()
            with self._lock:
                print 'debug: got ', command, ' with arguments ', args, 'from queue.'
                try:
                    value = self._do(command, args)
                except CommandError, e:
                    print 'debug: MPD thread - CommandError: ', e, '\n', sys.exc_info()
                    value = sys.exc_info()[1]
                except Exception, e:
                    print 'debug: MPD thread - Exception: ', e, '\n', sys.exc_info()
                    value = sys.exc_info()[1]
                    self.exit = True
                finally:
                    self.queue.task_done()
            if command == 'connect':
                self.connecting = False
            if self.abort:
                self.exit = True
            elif callback is not None:
                #callback(value, *callbackArgs)
                self.callbackQueue.put((callback, (value,) + callbackArgs))
            if self.exit:
                self.callbackQueue.put((sys.exit, (0,)))
                try:
                    self._do('close', ())
                    self._do('disconnect', ())
                except:
                    pass
                while not self.queue.empty():
                    self.queue.get()
                    self.queue.task_done()
                sys.exit(1)

    def _do(self, command, args):
        try:
            function = self.__getattribute__(command)
        except AttributeError:
            function = self.__getattr__(command)
        return function(*args)

    if hasattr(MPDClientBase, '_docommand'):
        def _docommand(self, command, args, retval):
            if command not in ('idle', 'noidle') and self._idle:
                self._writecommand('noidle', [])
            return super(MPDThread, self)._docommand(command, args, retval)

        def _execute(self, command, args):
            retval = self._commands[command]
            return self._docommand(command, args, retval)
    else:
        def _execute(self, command, args):
            if command not in ('idle', 'noidle') and self._idle:
                self._write_command('noidle', [])
            return super(MPDThread, self)._execute(command, args)

    if hasattr(MPDClientBase, '_writecommand'):
        def _writecommand(self, command, args=[]):
            if command.startswith('command_list') and self._idle:
                self._writecommand('noidle', [])
            if self._idle and command not in ('idle', 'noidle'):
                raise ProtocolError('%s not allowed in idle mode.' % command)
                super(MPDThread, self)._writecommand(command, args)
            else:
                super(MPDThread, self)._writecommand(command, args)
    else:
        def _write_command(self, command, args=[]):
            if command.startswith('command_list') and self._idle:
                self._write_command('noidle', [])
            if self._idle and command not in ('idle', 'noidle'):
                raise ProtocolError('%s not allowed in idle mode.' % command)
                super(MPDThread, self)._write_command(command, args)
            else:
                super(MPDThread, self)._write_command(command, args)

    def _reset(self):
        self._idle = False
        super(MPDThread, self)._reset()

    if hasattr(MPDClientBase, '_writecommand'):
        def _write_proxy(self, command, args=[]):
            self._writecommand(command, args)
    else:
        def _write_proxy(self, command, args=[]):
            self._write_command(command, args)


class CallbackThread(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.daemon = True
        self._queue = queue
        self.start()

    def run(self):
        while True:
            func, args = self._queue.get()
            func(*args)
