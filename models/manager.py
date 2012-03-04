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
from playqueue import PlayQueueModel
from playlists import PlaylistsModel
from filesystem import FileSystemModel
from artists import ArtistsModel
from albums import AlbumsModel
from tracks import TracksModel

class ModelManager(object):
    '''
    This class collects and updates the data in the models.

    It uses Qt signals and slots to get notified of changes and notify others
    of changes.
    '''

    def __init__(self, mpdclient, library, config):
        '''
        Initialize all models.
        '''
        self.mpdclient = mpdclient
        self.library = library
        self.config = config
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

# Code for updating PlayQueueModel.

# Code for updating PlaylistsModel.

# Code for updating library models.

# Put player state in a model like structure?
