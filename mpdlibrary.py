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
        return [Artist(self, value) for value in self._artists.keys()]

    def albums(self):
        '''Returns a list containing all albums in the library.'''
        return [Album(self, album) for album in self._albums.keys()]

    def songs(self):
        '''Returns a list containing all songs in the library.'''
        return [Song(self, song) for song in self._songList]

    def genres(self):
        '''Returns a list containing all genres in the library.'''
        return [Genre(self, genre) for genre in self._genres.keys()]

    def artistGenres(self, artist):
        '''Returns a list containing all genres listed in songs by the given artist.'''
        genres = set()
        for song in self.artistSongs(artist):
            genres.update(songGenre(song))
        return [Genre(self, genre) for genre in genres]

    def albumGenres(self, album):
        '''Returns a list containing all genres listed in songs on the given album.'''
        genres = set()
        for song in self.albumSongs(album):
            genres.update(songGenre(song))
        return [Genre(self, genre) for genre in genres]

    def genreArtists(self, genre):
        '''Returns a list containing all artists in the given genre.'''
        artists = set()
        for song in self.genreSongs(genre):
            artists.add(songArtist(song))
        return [Artist(self, artist) for artist in artists]

    def genreAlbums(self, genre):
        '''Returns a list containing all albums in the given genre.'''
        albums = set()
        for song in self.genreSongs(genre):
            albums.add(songAlbum(song))
        return [Album(self, album) for album in albums]

    def genreSongs(self, genre):
        '''Returns a list containing all songs in the given genre.'''
        return [Song(self, song) for song in self._genres.get(genre.lower(), [])]

    def artistSongs(self, artist):
        '''Returns a list containing all songs from the supplied artist.'''
        return [Song(self, song) for song in self._artists.get(artist, [])]

    def artistAlbums(self, artist):
        '''Returns a list containing all albums the artist is listed on.'''
        albums = set()
        for song in self.artistSongs(artist):
            album = songAlbum(song, '')
            albums.add(album)
        return [Album(self, album) for album in albums]

    def albumSongs(self, album, artists=[]):
        '''Returns a list containing all songs on the supplied album title.
        The optional artist argument can be used to only get the songs of a particular artist or list of artists.'''
        if type(artists) in (str, unicode):
            artists = [artists]
        songs = self._albums.get(album, [])
        if artists != []:
            songs = [Song(self, song) for song in songs if songArtist(song, '') in artists]
        return songs

    def albumArtists(self, album):
        '''Returns a list containing all artists listed on the album.'''
        songlist = self.albumSongs(album)
        artists = set()
        for song in songlist:
            artists.add(songArtist(song))
        return [Artist(self, artist) for artist in artists]

    def ls(self, path, fslist=None):
        '''Returns a list of songs and directories contained in the given path.'''
        if path.startswith('/'):
            path = path[1:]
        if fslist is None:
            fslist = self._filesystem
        part, sep, path = path.partition('/')
        if part == '':
            if type(fslist.get('file', None)) in (str, unicode):
                #return Song(self, fslist)
                return fslist
            else:
                #return [Dir(self, path) for path in fslist.keys()]
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
    return _getSongAttr(song, ('title', 'name', 'file'))

def songArtist(song, alt=''):
    value = _getSongAttr(song, ('artist', 'performer', 'composer'))
    if not value:
        value = alt
    return value

def songAlbum(song, alt=''):
    return song.get('album', alt)

def songTrack(song, alt=''):
    return song.get('track', alt)

def songGenre(song):
    value = song.get('genre', '')
    if type(value) in (str, unicode):
        value = value.lower()
    else:
        value = [x.lower() for x in value]
    return value

def songStation(song):
    if isStream(song):
        value = _getSongAttr(song, ('name', 'file'))
        return _getTextField(value)
    else:
        return ''

def songTime(song):
    stime = int(song.get('time', '0'))
    thour = stime / 3600
    stime -= thour * 3600
    tmin = stime / 60
    tsec = stime - tmin * 60
    if thour > 0:
        return '%i:%02i:%02i' % (thour, tmin, tsec)
    return '%i:%02i' % (tmin, tsec)

def isStream(song):
    return song.get('file', '').startswith('http://')

def _getSongAttr(song, attrs):
    '''Returns the value for the first key in attrs that exists.'''
    if isStream(song):
        # mpd puts stream metadata in the title attribute as "{artist} - {song}"
        value = song.get('title', '')
        if ' - ' in value:
            artist, title = value.split(' - ', 1)
            if 'artist' in attrs:
                return artist
            if 'title' in attrs:
                return title
    for attr in attrs:
        if attr in song:
            return song[attr].strip() if type(song[attr]) in (str, unicode) else song[attr]

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


class LibraryObject(object):
    _attributes = {}
    def __new__(cls, library, value):
        string = _getTextField(value)
        return unicode.__new__(cls, string)

    def __init__(self, library, value):
        self._library = library
        self._value = value

    def all(self):
        if type(self._value) in (str, unicode):
            return [self._value]
        else:
            return self._value

    def __getattr__(self, attr):
        try:
            return self._attributes[attr](self._value)
        except KeyError:
            raise AttributeError("'%s' object has no attribute '%s'"
                    % (self.__class__.__name__, attr))


class Artist(LibraryObject, unicode):
    def __init__(self, library, value):
        LibraryObject.__init__(self, library, value)
        self._attributes.update({
                'songs':    self._library.artistSongs,
                'albums':   self._library.artistAlbums,
                'genres':   self._library.artistGenres,
                })

class Album(LibraryObject, unicode):
    def __init__(self, library, value):
        LibraryObject.__init__(self, library, value)
        self._attributes.update({
                'songs':    self._library.albumSongs,
                'artists':  self._library.albumArtists,
                'genres':   self._library.albumGenres,
                })

class Genre(LibraryObject, unicode):
    def __init__(self, library, value):
        LibraryObject.__init__(self, library, value)
        self._attributes.update({
                'songs':    self._library.genreSongs,
                'artists':  self._library.genreArtists,
                'albums':   self._library.genreAlbums,
                })

class Time(LibraryObject, unicode):
    def __new__(cls, value):
        return LibraryObject.__new__(cls, None, value)

    def __init__(self, value):
        LibraryObject.__init__(self, None, value)
        self._value = int(value)
        self._attributes.update({
                'hours':    lambda value: value / 3600,
                'minutes':  lambda value: (value - (value * 3600)) / 60,
                'seconds':  lambda value: value - ((value - (value / 3600 * 3600)) / 60 * 60),
                'human':    lambda value: songTime({'time': value}),
                })

class Text(LibraryObject, unicode):
    def __new__(cls, value):
        return LibraryObject.__new__(cls, None, value)

    def __init__(self, value):
        LibraryObject.__init__(self, None, value)

class Song(dict, LibraryObject):
    def __init__(self, library, value):
        dict.__init__(self, value)
        LibraryObject.__init__(self, library, self)

    def __getattr__(self, attr):
        try:
            return self.__getitem__(attr)
        except KeyError:
            raise AttributeError("'%s' object has no attribute '%s'"
                    % (self.__class__.__name__, attr))

    def __contains__(self, key):
        try:
            self.__getitem__(key)
            return True
        except KeyError:
            return False

    def get(self, key, alt=None):
        try:
            return self.__getitem__(key)
        except KeyError:
            return alt

    def __getitem__(self, item):
        value = dict(self._value)
        if item == 'artist':
            return Artist(self._library, songArtist(value))
        elif item == 'title':
            return Text(songTitle(value))
        elif item == 'album':
            return Album(self._library, songAlbum(value))
        elif item == 'genre':
            return Genre(self._library, songGenre(value))
        elif item == 'file':
            return File(self._library, value['file'])
        elif item == 'track':
            return Text(songTrack(value))
        elif item == 'time':
            return Time(value['time'])
        elif item == 'station' and isStream(value):
            # Only applicable when the Song object
            # is created from a play queue item.
            return Text(songStation(value))
        else:
            return Text(value[item])


class Path(unicode, LibraryObject):
    def __new__(cls, library, value):
        return unicode.__new__(cls, value)

    def __init__(self, library, value):
        LibraryObject.__init__(self, library, value)
        if isinstance(value, Dir):
            self._parent = value

    def parent(self):
        return self._parent.parent() + self._parent

class File(Path):
    def dir(self):
        return Dir(self._library, self.rsplit('/', 1)[0])

class Dir(Path):
    def ls(self):
        return self._library.ls(self)


