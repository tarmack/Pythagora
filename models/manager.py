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
import os
import time
import thread
import mutex
import cPickle as pickle

from state import PlayerState
from playqueue import PlayQueueModel
from playlists import PlaylistsModel
from filesystem import FileSystemModel
from artists import ArtistsModel
from albums import AlbumsModel
from tracks import TracksModel

class ModelManager(object):
    '''
    This class manages the data in the models.
    '''

    def __init__(self, mpdclient, library, config):
        '''
        Initialize all models.
        '''
        self.mpdclient = mpdclient
        self.library = library
        self.config = config
        self.libraryMutex = mutex.mutex()
        self.playQueue = PlayQueueModel(mpdclient, library, config)
        self.playlists = PlaylistsModel(mpdclient, library)
        self.fileSystem = FileSystemModel(library)
        self.artists = ArtistsModel(library)
        self.albums = AlbumsModel(library)
        self.tracks = TracksModel(library)
        self.playerState = PlayerState(self.mpdclient, self.playQueue)

    ##################
    # Main interface #
    ##################
    def processChanges(self, changes):
        '''
        Updates the models according to the change groups in the changes
        argument.
        '''
        print 'debug: Processing changes'
        self.mpdclient.send('status', callback=
                lambda status, changes=changes: self._progressChanges(changes, status))

    def _progressChanges(self, changes, status):
        print 'debug: retrieved status form server.'
        if status is None:
            # Status returns None when the connection is in
            # "command list" mode. We will get a decent
            # update when that finishes.
            return
        if 'database' in changes:
            self.reloadLibrary(force=True)

        if 'playlist' in changes:
            self.updatePlayQueue(status)
        else:
            self.playQueue.setPlaying(status.get('songid'))

        self.playerState.update(status)

        if 'stored_playlist' in changes:
            self.reloadPlaylists()

    def clearForms(self):
        '''
        Clear all models.
        '''
        self.playQueue._clear()
        self.playlists.clear()
        self.fileSystem.clear()
        self.artists.clear()
        self.albums.clear()
        self.tracks.clear()

    ##############
    # Play queue #
    ##############
    def updatePlayQueue(self, status=None):
        '''
        Updates the play queue model.
        '''
        if not self.config.server:
            return
        if status is None:
            self.mpdclient.send('status', callback=self.updatePlayQueue)
            return
        self.mpdclient.send('plchanges', (self.playQueue.version,), callback=
                lambda changes: self.playQueue.update(changes, status))


    ####################
    # Stored playlists #
    ####################
    def reloadPlaylists(self):
        self.mpdclient.send('listplaylists', callback=
                self.playlists.update)


    ###############
    # MPD Library #
    ###############
    def reloadLibrary(self, force=False):
        '''
        Reloads the library in the library models.

        The library is loaded from cache when it is available and force is not
        True. The timestamp of the cached content is checked against the
        server.
        The cache is automatically updated when necessary.
        '''
        if force:
            self._getLibrary(0)
        else:
            self.mpdclient.send('stats', callback=
                    lambda stats: self._getLibrary(stats['db_update']))

    def _getCachePath(self):
        '''
        Returns the path of the library cache file for the current server.
        '''
        file_name = 'db_cache - ' + self.config.server[0]
        cache = os.path.expanduser('~/.cache/pythagora')
        if not os.path.isdir(cache):
            os.makedirs(cache)
        return '/'.join((cache, file_name))

    def _getLibrary(self, timestamp):
        '''
        Retrieves the library from the appropriate source.
        '''
        path = self._getCachePath()
        if os.path.exists(path):
            with open(path) as db_cache:
                if db_cache.readline().strip('\n') == timestamp:
                    mainlist = pickle.loads(db_cache.read())
                    thread.start_new_thread(self._reloadLibrary, (mainlist,))
                    return
        self._downloadStart = time.time()
        self.mpdclient.send('listallinfo', callback=
                lambda mainlist: self._cacheLibrary(timestamp, mainlist))

    def _cacheLibrary(self, timestamp, mainlist):
        '''
        Updates the library cache.
        '''
        print 'Downloading of the library took {0:.3f} seconds'.format(time.time() - self._downloadStart)
        path = self._getCachePath()
        with open(path, 'w') as db_cache:
            db_cache.write('%i\n' % timestamp)
            db_cache.write(pickle.dumps(mainlist))
        thread.start_new_thread(self._reloadLibrary, (mainlist,))

    def _reloadLibrary(self, mainlist):
        '''
        Reloads the library and updates all library models.
        '''
        self._parseStart = time.time()
        server = self.config.server
        self.libraryMutex.lock(self.library.reload, mainlist)
        self.libraryMutex.unlock()
        print 'library parsing took {0:.3} seconds'.format(time.time() - self._parseStart)
        if self.config.server == server:
            p = time.time()
            t = time.time()

            self.artists.reload(self.library.artists())
            print 'load Artist took %.3f seconds' % (time.time() - t); t = time.time()
            self.albums.reload(self.library.albums())
            print 'load Album took %.3f seconds' % (time.time() - t); t = time.time()
            self.tracks.reload(self.library.songs())
            print 'load Tracks took %.3f seconds' % (time.time() - t); t = time.time()
            self.fileSystem.reload()
            print 'load file system took %.3f seconds' % (time.time() - t)
            print 'library load took %.3f seconds' % (time.time() - p)

