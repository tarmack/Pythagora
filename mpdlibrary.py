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
class Library:
    '''Supplies a storage model for the mpd database.'''
    def __init__(self, mainlist):
        self._songList = []
        self._artists = {}
        self._albums = {}
        self._genres = {}
        self._filesystem = {}
        # parse the list and prepare it for loading in the library browser and the file system view.
        for song in (x for x in mainlist if 'file' in x):
            self._songList.append(song)
            album = songAlbum(song, 'None')
            artist = songArtist(song, 'Unknown')
            genre = song.get('genre', None)
            appendToList(self._artists, artist, song)
            appendToList(self._albums, album, song)
            if genre:
                appendToList(self._genres, genre, song)

            # Build the file system tree.
            fslist = self._filesystem
            path = song['file'].split('/')
            while path:
                part = path.pop(0)
                if path == []:
                    fslist[part] = song
                else:
                    fslist[part] = fslist.get(part, {})
                    fslist = fslist[part]

    def artists(self):
        '''Returns a list containing all artists in the library.'''
        return self._artists.keys()

    def albums(self):
        '''Returns a list containing all albums in the library.'''
        return self._albums.keys()

    def songs(self):
        '''Returns a list containing all songs in the library.'''
        return self._songList[:]

    def genres(self):
        '''Returns a list containing all genres in the library.'''
        return self._genres.keys()

    def artistGenres(self, artist):
        '''Returns a list containing all genres listed in songs by the given artist.'''
        genres = set()
        for song in self.artistSongs(artist):
            genres.update(songGenre(song))
        return list(genres)

    def albumGenres(self, album):
        '''Returns a list containing all genres listed in songs on the given album.'''
        genres = set()
        for song in self.albumSongs(album):
            genres.update(songGenre(song))
        return list(genres)

    def genreArtists(self, genre):
        '''Returns a list containing all artists in the given genre.'''
        artists = set()
        for song in self.genreSongs(genre):
            artists.add(songArtist(song))
        return list(artists)

    def genreAlbums(self, genre):
        '''Returns a list containing all albums in the given genre.'''
        albums = set()
        for song in self.genreSongs(genre):
            albums.add(songAlbum(song))
        return list(albums)

    def genreSongs(self, genre):
        '''Returns a list containing all songs in the given genre.'''
        return self._genres.get(genre.lower(), [])

    def artistSongs(self, artist):
        '''Returns a list containing all songs from the supplied artist.'''
        return self._artists.get(artist, [])

    def artistAlbums(self, artist):
        '''Returns a list containing all albums the artist is listed on.'''
        albumlist = set()
        for song in self.artistSongs(artist):
            album = songAlbum(song, '')
            albumlist.add(album)
        return list(albumlist)

    def albumSongs(self, album, artists=[]):
        '''Returns a list containing all songs on the supplied album title.
        The optional artist argument can be used to only get the songs of a particular artist or list of artists.'''
        if type(artists) in (str, unicode):
            artists = [artists]
        songlist = self._albums.get(album, [])
        if artists != []:
            songlist = [song for song in songlist if songArtist(song, '') in artists]
        return songlist

    def albumArtists(self, album):
        '''Returns a list containing all artists listed on the album.'''
        songlist = self.albumSongs(album)
        artistlist = set()
        for song in songlist:
            artistlist.add(songArtist(song))
        return list(artistlist)

    def ls(self, path, fslist=None):
        '''Returns a list of songs and directories contained in the given path.'''
        if path.startswith('/'):
            path = path[1:]
        if fslist is None:
            fslist = self._filesystem
        part, sep, path = path.partition('/')
        if part == '':
            if type(fslist.get('file', None)) in (str, unicode):
                return fslist
            else:
                return fslist.keys()
        fslist = fslist.get(part, {})
        return self.ls(path, fslist)

    def attributes(self, path):
        '''Returns whether path is a directory or a song file.'''
        if path.startswith('/'):
            path = path[1:]
        fslist = self._filesystem
        for part in path.split('/'):
            if part:
                fslist = fslist[part]
        if fslist.get('file', None) == path:
            return 'file'
        else:
            return 'directory'


def songTitle(song):
    value = _getSongAttr(song, ('title', 'name', 'file'))
    return _getTextField(value)

def songArtist(song, alt=''):
    value = _getSongAttr(song, ('artist', 'performer', 'composer'))
    if not value:
        value = alt
    return _getTextField(value)

def songAlbum(song, alt=''):
    value = song.get('album', alt)
    return _getTextField(value)

def songTrack(song, alt=''):
    value = song.get('track', alt)
    return _getTextField(value)

def songGenre(song):
    value = song.get('genre', [])
    if type(value) in (str, unicode):
        value = [value.lower()]
    else:
        value = [x.lower() for x in value]
    return value

def songTime(song):
    stime = int(song.get('time', '0'))
    thour = stime / 3600
    stime -= thour * 3600
    tmin = stime / 60
    tsec = stime - tmin * 60
    if thour > 0:
        return '%i:%02i:%02i' % (thour, tmin, tsec)
    return '%i:%02i' % (tmin, tsec)


def _getSongAttr(song, attrs):
    '''Returns the value for the first key in attrs that exists.'''
    for attr in attrs:
        if attr in song:
            return song[attr]

def _getTextField(value):
    if getattr(value, '__iter__', False):
        return value[0]
    else:
        return value

def appendToList(listDict, keys, value, deduplicate=False):
    '''In place add value to listDict at key.
    If any of them are lists the values in those lists are used as value and
    key. Everything gets added to everything. The optional deduplicate makes
    appendToList only add values that are not yet in the list.
    '''
    if type(value) != list:
        value = [value]
    if type(keys) != list:
        keys = [keys]
    for key in keys:
        part = listDict.get(key, [])
        if deduplicate:
            # filter all that are already in there.
            value = [x for x in value if x not in part]
        listDict[key] = part + value

