#!/usr/bin/python
# -*- coding: utf-8 -*-

import mpdlibrary

library = None # shut up PyFlakes.

test_list = [
        {
            'title':    u'Love generation',
            'artist':   u'Bob Sinclar',
            'genre':    u'Top 40',
            'file':     u'Bob Sinclar - Love Generation.mp3',
            'time':     u'206',
        },
        {
            'file':     u'Mirrors Edge - Menu Theme.ogg',
            'time':     u'111'
        },
        {
            'album':    [u"What a Long Strange Trip It's Been (1 of 2)", u"What a Long Strange Trip It's Been (1 of 2)"],
            'title':    [u'Cosmic Charlie', u'Cosmic Charlie'],
            'track':    [u'2/1', u'2/1'],
            'artist':   u'Grateful Dead',
            'file':     u'02 - Cosmic Charlie.mp3',
            'time':     u'333'
        },
        {
            'album':    u'Deepest Purple: The Very Best of Deep Purple',
            'title':    u"Demon's Eye",
            'track':    u'11/12',
            'artist':   u'Deep Purple',
            'genre':    u'Rock',
            'albumartist': u'Deep Purple',
            'file':     u"Deep Purple/Deepest Purple_ The Very Best of Deep Purple/11 - Demon's Eye.mp3",
            'time':     u'3923',
            'date':     u'1980',
        },
        {
            'album':    u'Escape Into The Twilight',
            'title':    u'20,000 Winks',
            'track':    u'2',
            'artist':   u'Escape Into The Twilight',
            'genre':    [u'Electronic', u'Electronic'],
            'file':     u'Escape Into The Twilight/Escape Into The Twilight/Content/Escape Into The Twilight/Escape Into The Twilight - 02 - 20000 Winks.mp3',
            'time':     u'261',
            'date':     u'2009'
        },
        {
            'album':    u'Final Fantasy X: Original Soundtrack (disc 2)',
            'title':    u"Rikku's Theme",
            'track':    u'22/23',
            'artist':   u'植松伸夫',
            'file':     u"Soundtracks/Nobuo Uematsu - Final Fantasy X OST/Disc II/22 Rikku's Theme.mp3",
            'time':     u'243',
            'date':     u'2001-08-01'
        },
        {
            'file':     u'http://83.223.213.13:8080'
        },
    ]

run_slow = False
if run_slow:
    import mpdunicode
    client = mpdunicode.MPDClient()
    client.connect('127.0.0.1', 6600)
    test_list = client.listallinfo()


def setup_function(function):
    """ setup any state tied to the execution of the given function.
    Invoked for every test function in the module.
    """
    global library
    library = mpdlibrary.Library(test_list)

def teardown_function(function):
    """ teardown any state that was previously setup with a setup_function
    call.
    """
    global library
    del library

def test_song_list():
    song_list = list(library.songs())
    for song in song_list:
        assert song._value in test_list
    for item in test_list:
        assert item in [song._value for song in song_list]

def test_artist_list():
    expect = _get_expected_values('artist', 'Unknown')
    got = sorted(unicode(artist) for artist in library.artists())
    assert got == expect

def test_album_list():
    expect = _get_expected_values('album', 'None')
    got = sorted(library.albums())
    assert got == expect

def test_genre_list():
    expect = _get_expected_values('genre')
    got = sorted(library.genres())
    assert got == expect

def _get_expected_values(item, default=None):
    expect = []
    for value in [song.get(item, default) for song in test_list]:
        if not value is None:
            if isinstance(value, list):
                for item in set(value):
                    print value
                    expect.append(item)
            else:
                expect.append(value)
    return sorted(set(expect))


def test_song_attrs():
    for item in test_list:
        song = mpdlibrary.Song(item, library)
        _test_song_attrs(song, item)

def _test_song_attrs(song, item):
    for attr in ('artist', 'title', 'album', 'genre', 'file', 'time', 'track', 'disc', 'station', 'isStream'):
        # Make sure the dict like and attribute interfaces present the same data.
        assert eval("song.%s == song['%s']" % (attr, attr))
        # Make sure that data conforms to the data that was put in.
        assert eval("song.%s or None == item.get('%s')" % (attr, attr))


def test_artist():
    for item in test_list:
        if 'artist' in item:
            _test_artist(item['artist'])

def _test_artist(_name):
    name = _deduplicate(_name)
    artist = mpdlibrary.Artist(name, library)
    assert artist == name
    expect = sorted(mpdlibrary.Song(song, library) for song in test_list if song.get('artist') == _name)
    assert sorted(artist.songs) == expect
    expect = sorted(mpdlibrary.Album(song.get('album', 'None'), library)
            for song in test_list if song.get('artist') == _name)
    assert sorted(artist.albums) == expect
    expect = sorted(mpdlibrary.Genre(song.get('genre'), library)
            for song in test_list if song.get('artist') == _name)
    assert sorted(artist.genres) == expect


def test_album():
    for item in test_list:
        if 'album' in item:
            _test_album(item['album'])

def _test_album(_name):
    name = _deduplicate(_name)
    album = mpdlibrary.Album(name, library)
    assert album == name
    expect = sorted(mpdlibrary.Song(song, library) for song in test_list if song.get('album') == _name)
    assert sorted(album.songs) == expect
    expect = sorted(mpdlibrary.Artist(song.get('artist', 'Unknown'), library)
            for song in test_list if song.get('album') == _name)
    assert sorted(album.artists) == expect
    expect = sorted(mpdlibrary.Genre(song.get('genre'), library)
            for song in test_list if song.get('album') == _name)
    assert sorted(album.genres) == expect

def _deduplicate(name):
    if isinstance(name, list):
        name = list(set(name))
        if len(name) == 1:
            name = name[0]
    return name


def test_genre_single():
    genre = mpdlibrary.Genre('Rock', library)
    assert genre == 'Rock'
    expect = sorted(mpdlibrary.Song(song, library) for song in test_list if song.get('genre') == 'Rock')
    assert sorted(genre.songs) == expect
    expect = sorted(mpdlibrary.Artist(song.get('artist', 'None'), library)
            for song in test_list if song.get('genre') == 'Rock')
    assert sorted(genre.artists) == expect
    expect = sorted(mpdlibrary.Album(song.get('album', 'None'), library)
            for song in test_list if song.get('genre') == 'Rock')
    assert sorted(genre.albums) == expect

def test_genre_multiple():
    genre = mpdlibrary.Genre(['Electronic', 'Electronic'], library)
    assert genre == 'Electronic'
    expect = sorted(mpdlibrary.Song(song, library) for song in test_list if 'Electronic' in song.get('genre', []))
    assert sorted(genre.songs) == expect
    expect = sorted(mpdlibrary.Artist(song.get('artist', 'None'), library)
            for song in test_list if 'Electronic' in song.get('genre', []))
    assert sorted(genre.artists) == expect
    expect = sorted(mpdlibrary.Album(song.get('album', 'None'), library)
            for song in test_list if 'Electronic' in song.get('genre', []))
    assert sorted(genre.albums) == expect

def test_time():
    time = mpdlibrary.Time('6234', library)
    assert time == int('6234')
    assert time.human == "1:43:54"
    assert time.hours == 1
    assert time.minutes == 103


#        elif attr == 'isStream':
#            assert song_obj.isStream == False
#        elif attr == 'station':
#            assert song_obj.station == ''
#    if attr == 'track':
#        assert int(song_obj.track) == 11
#
#print 'Song attributes:\t\tpassed'
