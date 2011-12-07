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
import locale
import time
import gc

locale.setlocale(locale.LC_ALL, "")


class Library:
    '''Supplies a storage model for the mpd database.'''
    def __init__(self, mainlist=[]):
        self.reload(mainlist)

    def reload(self, mainlist):
        '''Reloads the current instance with the new list from MPD. Returns the instance for your convenience'''
        self._songList = [song for song in mainlist if 'file' in song]
        self._artists = ListDict()
        self._albums = ListDict()
        self._genres = ListDict()
        self._filesystem = {}
        # Force the collection of cyclic references to the old objects.
        start = time.time()
        print 'info: Garbage collection %i freed items in %.3f seconds.' % (gc.collect(), time.time() - start)
        # parse the list and prepare it for loading in the library browser and the file system view.
        for index, song in enumerate(self._songList):
            album = song.get('album', 'None')
            self._albums[album] = index

            artist = 'Unknown'
            for field in ('artist', 'performer', 'composer'):
                if field in song:
                    artist = song[field]
                    break
            self._artists[artist] = index

            genre = song.get('genre', None)
            if genre:
                    self._genres[genre] = index

            # Build the file system tree.
            fslist = self._filesystem
            path = song['file'].split('/')
            while path:
                part = path.pop(0)
                if path == []:
                    fslist[part] = index
                else:
                    fslist[part] = fslist.get(part, {})
                    fslist = fslist[part]
        return self

    def artists(self):
        '''Returns a list containing all artists in the library.'''
        return (Artist(value, self) for value in sorted(self._artists.keys(), locale.strcoll))

    def albums(self):
        '''Returns a list containing all albums in the library.'''
        return (Album(album, self) for album in sorted(self._albums.keys(), locale.strcoll))

    def songs(self):
        '''Returns a list containing all songs in the library.'''
        return (Song(song, self) for song in self._songList)

    def genres(self):
        '''Returns a list containing all genres in the library.'''
        return (Genre(genre, self) for genre in self._genres.keys())

    def artistSongs(self, artist):
        '''Returns a list containing all songs from the supplied artist.'''
        return (Song(self._songList[index], self) for index in self._artists.get(artist, []))

    def artistAlbums(self, artist):
        '''Returns a list containing all albums the artist is listed on.'''
        albums = set()
        for song in self.artistSongs(artist):
            albums.update(song.album.all())
        return (Album(album, self) for album in albums)

    def artistGenres(self, artist):
        '''Returns a list containing all genres listed in songs by the given artist.'''
        genres = set()
        for song in self.artistSongs(artist):
            genres.update(song.genre.all())
        return (Genre(genre, self) for genre in genres)

    def albumSongs(self, album, artists=[]):
        '''Returns a list containing all songs on the supplied album title.
        The optional artist argument can be used to only get the songs of a particular artist or list of artists.'''
        if type(artists) in (str, unicode):
            artists = [artists]
        songs = (Song(self._songList[index], self) for index in self._albums.get(album, []))
        for song in sorted(songs, _sortAlbumSongs):
            if artists == [] or song.artist in artists:
                yield song

    def albumArtists(self, album):
        '''Returns a list containing all artists listed on the album.'''
        artists = set()
        for song in self.albumSongs(album):
            artists.update(song.artist.all())
        return (Artist(artist, self) for artist in artists)

    def albumGenres(self, album):
        '''Returns a list containing all genres listed in songs on the given album.'''
        genres = set()
        for song in self.albumSongs(album):
            genres.update(song.genre.all())
        return (Genre(genre, self) for genre in genres)

    def genreSongs(self, genre):
        '''Returns a list containing all songs in the given genre.'''
        return (Song(self._songList[index], self) for index in self._genres.get(genre, []))

    def genreArtists(self, genre):
        '''Returns a list containing all artists in the given genre.'''
        artists = set()
        for song in self.genreSongs(genre):
            artists.update(song.artist.all())
        return (Artist(artist, self) for artist in artists)

    def genreAlbums(self, genre):
        '''Returns a list containing all albums in the given genre.'''
        albums = set()
        for song in self.genreSongs(genre):
            albums.update(song.album.all())
        return (Album(album, self) for album in albums)

    def ls(self, path):
        '''Returns a list of songs and directories contained in the given path.'''
        if path.startswith('/'):
            path = path[1:]
        fslist = self._fsNode(path)
        for key, value in sorted(fslist.items()):
            if isinstance(value, int):
                yield File(self._songList[value]['file'], self)
            else:
                yield Dir(path + '/' + key, self)

    def _fsNode(self, path):
        fslist = self._filesystem
        for part in (x for x in path.split('/') if x):
            fslist = fslist.get(part)
        return fslist

def _sortAlbumSongs(x, y):
    # Sorting album songs by disc number, then by track number
    return cmp(int(x.disc), int(y.disc)) or cmp(int(x.track), int(y.track))


class ListDict(dict):
    '''A dictionary for storing the library data.'''
    def __setitem__(self, keys, values):
        if type(values) is not list:
            values = [values]
        if type(keys) is not list:
            keys = [keys]
        for key in keys:
            part = self.get(key, [])
            values = [x for x in values if x not in part]
            dict.__setitem__(self, key, part + values)


class LibraryObject(object):
    _attributes = {}
    def __new__(cls, value, library):
        if type(value) is not cls and getattr(value, '__iter__', False):
            value = value[0]
        return super(LibraryObject, cls).__new__(cls, value)

    def __init__(self, value, library):
        self._library = library
        if not value:
            value = self
        self._value = value

    def all(self):
        if type(self._value) in (str, unicode):
            return [self._value]
        else:
            return self._value

    def __getattr__(self, attr):
        try:
            funt = self._attributes[attr].__get__(self._library)
            return funt(self)
        except KeyError:
            raise AttributeError("LibraryObject '%s' has no attribute '%s'"
                    % (self.__class__.__name__, attr))

    def __call__(self):
        return self

class Text(LibraryObject, unicode):
    pass

class Artist(LibraryObject, unicode):
    _attributes = {
            'songs':    Library.artistSongs,
            'albums':   Library.artistAlbums,
            'genres':   Library.artistGenres,
            }

class Album(LibraryObject, unicode):
    _attributes = {
            'songs':    Library.albumSongs,
            'artists':  Library.albumArtists,
            'genres':   Library.albumGenres,
            }

class Genre(LibraryObject, unicode):
    _attributes = {
            'songs':    Library.genreSongs,
            'artists':  Library.genreArtists,
            'albums':   Library.genreAlbums,
            }

    def __init__(self, value, library):
        LibraryObject.__init__(self, value, library)
        if type(value) != list:
            value = [value]
        self._value = [x for x in value if type(value) in (str, unicode)]

class Time(LibraryObject, int):
    _attributes = {
            'hours':    lambda lib, value: value / 3600,
            'minutes':  lambda lib, value: value / 60,
            }

    @property
    def human(self):
        time = self
        thour = time / 3600
        time -= thour * 3600
        tmin = time / 60
        tsec = time - tmin * 60
        if thour > 0:
            return '%i:%02i:%02i' % (thour, tmin, tsec)
        return '%i:%02i' % (tmin, tsec)


class Track(Text):
    def __int__(self):
        track = str(self)
        if '/' in track:
            track = track.split('/', 1)[0]
        if track == '':
            track = 0
        return int(track)


class DiscNumber(Text):
    def __int__(self):
        disc_number = str(self)
        if '/' in disc_number:
            disc_number = disc_number.split('/', 1)[0]
        if disc_number == '':
            disc_number = 0
        return int(disc_number)


class Song(dict, LibraryObject):
    def __init__(self, value, library):
        dict.__init__(self, value)
        LibraryObject.__init__(self, self, library)

    def __getattr__(self, attr):
        try:
            return self.__getitem__(attr)
        except KeyError:
            return LibraryObject.__getattr__(self, attr)

    def __contains__(self, key):
        try:
            self.__getitem__(key)
            return True
        except KeyError:
            return False

    def __getitem__(self, item):
        if item == 'artist':
            return Artist(self._getAttr('artist', 'performer', 'composer') or 'Unknown',
                    self._library)
        elif item == 'title':
            return Text(self._getAttr('title', 'name', 'file'),
                    self._library)
        elif item == 'album':
            return Album(self._getAttr('album') or 'None',
                    self._library)
        elif item == 'genre':
            return Genre(self._getAttr('genre'),
                    self._library)
        elif item == 'file':
            return File(self._getAttr('file'),
                    self._library)
        elif item == 'time':
            return Time(self._getAttr('time') or 0,
                    self._library)
        elif item == 'track':
            return Track(self._getAttr('track') or '',
                    self._library)
        elif item == 'disc':
            return DiscNumber(self._getAttr('disc') or '',
                    self._library)
        elif item == 'station':
            # Only applicable when the Song object
            # is created from a play queue item.
            if self.isStream:
                return Text(self._getAttr('name', 'file'),
                    self._library)
            else:
                return Text('', self._library)
        elif item == 'isStream':
            return dict.get(self, 'file', '').startswith('http://')
        else:
            value = self._getAttr(item)
            if value is None:
                raise KeyError
            return Text(value, self._library)

    def _getAttr(self, *attrs):
        '''Returns the value for the first key in attrs that exists.'''
        value = None
        if ('artist' in attrs or 'title' in attrs) and self.isStream:
            # mpd puts stream metadata in the title attribute as "{artist} - {song}"
            value = dict.get(self, 'title', None)
            if value is not None:
                if ' - ' in value:
                    artist, title = value.split(' - ', 1)
                    if 'artist' in attrs:
                        value = artist
                    if 'title' in attrs:
                        value = title
                elif 'title' not in attrs:
                    value = ''
            elif 'title' in attrs:
                value = self.station
        else:
            for attr in attrs:
                if dict.__contains__(self, attr):
                    value = dict.__getitem__(self, attr)
                    break
        return value.strip() if type(value) in (str, unicode) else value


class Path(LibraryObject, unicode):
    _attributes = {
            'absolute': lambda lib, self: self._value,
            'parent': lambda lib, self: Dir('/'.join(self._value.split('/')[:-1]), lib)
            }
    def __new__(cls, value, library=None):
        return unicode.__new__(cls, value.rsplit('/', 1)[-1])

class File(Path):
    @property
    def song(self):
        return Song(self._library._fsNode(self._value), self._library)

class Dir(Path):
    def __len__(self):
        return len(self._library._fsNode(self._value))

    def __iter__(self):
        return self._library.ls(self._value)

    def __getitem__(self, index):
        if not hasattr(self, 'node'):
            self.node = sorted(self._library._fsNode(self._value).items())
        key, value = self.node[index]
        if type(value) is int:
            return File(self._library._songList[value]['file'], self._library)
        else:
            return Dir(self._value + '/' + key, self._library)

    def index(self, item):
        item = unicode(item)
        if not hasattr(self, 'node'):
            self.node = sorted(self._library._fsNode(self._value).items())
        for index, (path, subNode) in enumerate(self.node):
            if path == item:
                return index


