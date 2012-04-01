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
import array
import collections

locale.setlocale(locale.LC_ALL, "")


class Library(object):
    '''Supplies a storage model for the mpd database.'''
    def __init__(self, mainlist=[], options={}):
        self.options = options
        self.reload(mainlist)

    def reload(self, mainlist):
        '''Reloads the current instance with the new list from MPD. Returns the instance for your convenience'''
        reload_start = time.time()
        self._song_list = [song for song in mainlist if 'file' in song]
        self._artists = LibraryIndex()
        self._albums = LibraryIndex()
        self._genres = LibraryIndex()
        if self.options.get('filesystem', True):
            self._filesystem = {}
        # parse the list and prepare it for loading in the library browser and the file system view.
        for index, song in enumerate(self._song_list):
            album = song.get('album', 'None')
            self._albums[album] = index

            artist = 'Unknown'
            for field in ('artist', 'performer', 'composer'):
                if field in song:
                    artist = song[field]
                    break
            self._artists[artist] = index
            if 'albumartist' in song:
                self._artists[song['albumartist']] = index

            genre = song.get('genre', None)
            if genre:
                    self._genres[genre] = index

            if self.options.get('filesystem', True):
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

        print('info: Setting up of the library took %.3f seconds.' % (time.time() - reload_start))
        self._artists._order.sort(cmp=locale.strcoll)
        self._albums._order.sort(cmp=locale.strcoll)
        self._genres._order.sort(cmp=locale.strcoll)
        print('info: Building of the library took %.3f seconds.' % (time.time() - reload_start))
        return self

    def artists(self):
        '''Returns a view over all artists in the library.'''
        return LibraryView(Artist, self, self._artists)

    def albums(self):
        '''Returns a view over all albums in the library.'''
        return LibraryView(Album, self, self._albums)

    def songs(self):
        '''Returns a view over all songs in the library.'''
        return LibraryView(Song, self, self._song_list)

    def genres(self):
        '''Returns a view over all genres in the library.'''
        return LibraryView(Genre, self, self._genres)

    def artist_songs(self, artist):
        '''Returns a view over all songs from the supplied artist.'''
        return LibraryView(Song, self, self._song_list, self._artists.get(artist, []))

    def artist_albums(self, artist):
        '''Returns a view over all albums the artist is listed on.'''
        albums = set()
        for song in self.artist_songs(artist):
            albums.update(song.album.all())
        return LibraryView(Album, self, sorted(albums, locale.strcoll))

    def artist_genres(self, artist):
        '''Returns a view over all genres listed in songs by the given artist.'''
        genres = set()
        for song in self.artist_songs(artist):
            genres.update(song.genre.all())
        return LibraryView(Genre, self, sorted(genres, locale.strcoll))

    def album_songs(self, album, artists=[]):
        '''Returns a view over all songs on the supplied album title.
        The optional artist argument can be used to only get the songs of a particular artist or list of artists.'''
        if artists == []:
            return LibraryView(Song, self, self._song_list, self._albums.get(album, []))
        else:
            if isinstance(artists, basestring):
                artists = [artists]
            songs = (Song(self._song_list[index], self) for index in self._albums.get(album, []))
            if artists != []:
                songs = (song for song in songs if song.artist in artists)
            return LibraryView(None, self, sorted(songs, _sort_album_songs))

    def album_artists(self, album):
        '''Returns a view over all artists listed on the album.'''
        artists = set()
        for song in self.album_songs(album):
            artists.update(song.artist.all())
        return LibraryView(Artist, self, sorted(artists, locale.strcoll))

    def album_genres(self, album):
        '''Returns a view over all genres listed in songs on the given album.'''
        genres = set()
        for song in self.album_songs(album):
            genres.update(song.genre.all())
        return LibraryView(Genre, self, sorted(genres, locale.strcoll))

    def genre_songs(self, genre):
        '''Returns a view over all songs in the given genre.'''
        return LibraryView(Song, self, self._song_list, self._genres.get(genre, []))

    def genre_artists(self, genre):
        '''Returns a view over all artists in the given genre.'''
        artists = set()
        for song in self.genre_songs(genre):
            artists.update(song.artist.all())
        return LibraryView(Artist, self, sorted(artists, locale.strcoll))

    def genre_albums(self, genre):
        '''Returns a view over all albums in the given genre.'''
        albums = set()
        for song in self.genre_songs(genre):
            albums.update(song.album.all())
        return LibraryView(Album, self, sorted(albums, locale.strcoll))

    def ls(self, path):
        '''Returns a view over the songs and directories contained in the given path.'''
        if path.startswith('/'):
            path = path[1:]
        fslist = self._fsNode(path)
        results = []
        for key, value in sorted(fslist.items()):
            if isinstance(value, int):
                results.append(File(self._song_list[value]['file'], self))
            else:
                results.append(Dir(path + '/' + key, self))
        return LibraryView(None, self, sorted(results, locale.strcoll))

    def _fsNode(self, path):
        fslist = self._filesystem
        for part in (x for x in path.split('/') if x):
            fslist = fslist.get(part)
        return fslist

def _sort_album_songs(x, y):
    # Sorting album songs by disc number, then by track number
    return cmp(int(DiscNumber(x.get('disc'))), int(DiscNumber(y.get('disc')))) \
            or cmp(int(Track(x.get('track'))), int(Track(y.get('track'))))


class LibraryIndex(dict):
    '''A dictionary for storing the library data.'''
    def __init__(self, values=[]):
        dict.__init__(self, values)
        self._order = []

    def __setitem__(self, key, value):
        if isinstance(key, list):
            for k in key:
                self.__setitem__(k, value)
        else:
            if key in self:
                part = self[key]
                if not value in part:
                    part.append(value)
            else:
                self._order.append(key)
                dict.__setitem__(self, key, array.array('H', [value]))

    def __iter__(self):
        return self._order.__iter__()

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._order[key]
        return dict.__getitem__(self, key)


class LibraryView(collections.Sequence):
    def __init__(self, cls, library, store, mapping=None):
        if cls is None:
            self._cls = lambda value, lib: value
        else:
            self._cls = cls
        self._library = library
        self._store = store
        self._mapping = mapping

    def __iter__(self):
        if not self._mapping is None:
            return (self._cls(self._store[index], self._library) for index in self._mapping)
        else:
            return (self._cls(value, self._library) for value in self._store)

    def __getitem__(self, index):
        if not self._mapping is None:
            index = self._mapping[index]
        return self._cls(self._store[index], self._library)

    def __len__(self):
        if not self._mapping is None:
            return len(self._mapping)
        else:
            return len(self._store)


class LibraryObject(object):
    def __new__(cls, value, library=None):
        if not isinstance(value, cls) and isinstance(value, (list, tuple)):
            value = value[0]
        base = super(LibraryObject, cls)
        if base.__new__.__self__ is object:
            return base.__new__(cls)
        else:
            return base.__new__(cls, value)

    def __init__(self, value, library=None):
        self._library = library
        if not isinstance(value, self.__class__.__base__) and isinstance(value, (list, tuple)):
            value = tuple(x for x in value if isinstance(x, basestring))
        if not value:
            value = self
        self._value = value

    def all(self):
        if isinstance(self._value, basestring):
            return [self.__class__(self._value, self._library)]
        else:
            return [self.__class__(value, self._library) for value in self._value]


class Text(LibraryObject, unicode):
    pass

class Artist(LibraryObject, unicode):
    @property
    def songs(self):
        return self._library.artist_songs(self)

    @property
    def albums(self):
        return self._library.artist_albums(self)

    @property
    def genres(self):
        return self._library.artist_genres(self)

class Album(LibraryObject, unicode):
    @property
    def songs(self):
        return self._library.album_songs(self)

    @property
    def artists(self):
        return self._library.album_artists(self)

    @property
    def genres(self):
        return self._library.album_genres(self)

class Genre(LibraryObject, unicode):
    @property
    def songs(self):
        return self._library.genre_songs(self)

    @property
    def artists(self):
        return self._library.genre_artists(self)

    @property
    def albums(self):
        return self._library.genre_albums(self)

class Time(LibraryObject, int):
    @property
    def hours(self):
        return self / 3600

    @property
    def minutes(self):
        return self / 60

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


class Song(LibraryObject):
    def __init__(self, song, library=None):
        self._value = song
        self._library = library

    def __getattr__(self, attr):
        try:
            return self.__getitem__(attr)
        except KeyError:
            return LibraryObject.__getattribute__(self, attr)

    def get(self, key, default=None):
        try:
            return self.__getitem__(key)
        except KeyError:
            return default

    def __contains__(self, key):
        try:
            self.__getitem__(key)
            return True
        except KeyError:
            return False

    def __getitem__(self, item):
        if item == 'artist':
            return Artist(self._get_value('artist', 'performer', 'composer') or 'Unknown',
                    self._library)
        elif item == 'title':
            return Text(self._get_value('title', 'name', 'file'),
                    self._library)
        elif item == 'album':
            return Album(self._get_value('album') or 'None',
                    self._library)
        elif item == 'genre':
            return Genre(self._get_value('genre'),
                    self._library)
        elif item == 'file':
            return File(self._get_value('file'),
                    self._library)
        elif item == 'time':
            return Time(self._get_value('time') or 0,
                    self._library)
        elif item == 'track':
            return Track(self._get_value('track') or '',
                    self._library)
        elif item == 'disc':
            return DiscNumber(self._get_value('disc') or '',
                    self._library)
        elif item == 'station':
            # Only applicable when the Song object
            # is created from a play queue item.
            if self.isStream:
                return Text(self._get_value('name', 'file'),
                    self._library)
            else:
                return Text('', self._library)
        elif item == 'isStream':
            return self._value.get('file', '').startswith('http://')
        else:
            value = self._get_value(item)
            if value is None:
                raise KeyError
            return Text(value, self._library)

    def _get_value(self, *attrs):
        '''Returns the value for the first key in attrs that exists.'''
        value = None
        if ('artist' in attrs or 'title' in attrs) and self.isStream:
            # mpd puts stream metadata in the title attribute as "{artist} - {song}"
            value = self._value.get('title', None)
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
                if attr in self._value:
                    value = self._value[attr]
                    break
        return value.strip() if isinstance(value, basestring) else value

    def __eq__(self, other):
        left = self._value
        try:
            right = other._value
        except AttributeError:
            if isinstance(other, dict):
                right = other
            else:
                return False
        for item in ('title', 'artist', 'file'):
            try:
                left_item = left[item]
            except KeyError:
                left_item = None
            try:
                right_item = right[item]
                if left_item != right_item:
                    return False
            except KeyError:
                if not left_item is None:
                    return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

class Path(LibraryObject, unicode):
    @property
    def absolute(self):
        return self._value

    @property
    def parent(self):
        return Dir('/'.join(self._value.split('/')[:-1]), self._library)

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
        return (item for item in self._library.ls(self._value))

    def __getitem__(self, index):
        if not hasattr(self, 'node'):
            self.node = sorted(self._library._fsNode(self._value).items())
        key, value = self.node[index]
        if isinstance(value, int):
            return File(self._library._song_list[value]['file'], self._library)
        else:
            return Dir(self._value + '/' + key, self._library)

    def index(self, item):
        item = unicode(item)
        if not hasattr(self, 'node'):
            self.node = sorted(self._library._fsNode(self._value).items())
        for index, (path, subNode) in enumerate(self.node):
            if path == item:
                return index

