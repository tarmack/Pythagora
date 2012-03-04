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

from playqueue import PlayQueueModel
from playlists import PlaylistsModel
from filesystem import FileSystemModel
from artists import ArtistsModel
from albums import AlbumsModel
from tracks import TracksModel

class ModelManager(object):
    '''
    This class collects and updates the data in the models.
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

    def updatePlayQueue(self, change_list, status):
        if not self.config.server:
            return
        self.playQueue.update(change_list, status)

    def clearForms(self):
        self.playQueue.clear()
        self.playlists.clear()
        self.fileSystem.clear()
        self.artists.clear()
        self.albums.clear()
        self.tracks.clear()

    def setCurrentSong(self, song):
        playing = int(song['pos'])
        self.playQueue.setPlaying(playing)

    def reloadPlaylists(self, playlists):
        self.playlists.update(playlists)

    def reloadLibrary(self, force=False):
        if force:
            self._getLibrary(0)
        else:
            self.mpdclient.send('stats', callback=
                    lambda stats: self._getLibrary(stats['db_update']))

    def _getCachePath(self):
        file_name = 'db_cache - ' + self.config.server[0]
        cache = os.path.expanduser('~/.cache/pythagora')
        if not os.path.isdir(cache):
            os.makedirs(cache)
        return '/'.join((cache, file_name))

    def _getLibrary(self, timestamp):
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
        print 'Downloading of the library took {0:.3f} seconds'.format(time.time() - self._downloadStart)
        path = self._getCachePath()
        with open(path, 'w') as db_cache:
            db_cache.write(timestamp + '\n')
            db_cache.write(pickle.dumps(mainlist))
        thread.start_new_thread(self._reloadLibrary, (mainlist,))

    def _reloadLibrary(self, mainlist):
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


# Code for updating PlayQueueModel.

# Code for updating PlaylistsModel.

# Code for updating library models.

# Put player state in a model like structure?

