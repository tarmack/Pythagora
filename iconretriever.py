# -*- coding: utf-8 -*
#-------------------------------------------------------------------------------{{{
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
#-------------------------------------------------------------------------------}}}
import os
import urllib
from glob import glob
from sys import getrefcount
import threading
import time

import auxilia

APPNAME = 'pythagora'
NOCOVER = 'icons/audio-x-generic.png'
APIKEY = 'c01e19f763d7bd5adc905bd7456cf80d'
SECONDS_BETWEEN_REQUESTS = 0.2

class Retriever:#{{{1
    def __init__(self, musicPath):
        self.lastContact = time.time()
        self.unavailebleAlbums = []
        self.unavailebleArtists = []
        self.path = musicPath
        musicPath = os.path.expanduser(unicode(musicPath))
        if not os.path.isdir(musicPath):
            print 'debug: Music dir does not exist, bad config.'
            self.coverPath = None
            self.musicPath = None
        else:
            self.musicPath = musicPath
            self.coverPath = os.path.join(musicPath, 'covers')
            if not os.path.isdir(self.coverPath):
                try:
                    os.mkdir(self.coverPath)
                except Exception, e:
                    print 'error: ', e
                    self.coverPath = None
        if not self.coverPath:
            print 'debug: No cover dir in music dir, falling back to private cache.'
            self.coverPath = checkDir(os.path.expanduser('~/.config'))
            if self.coverPath:
                self.coverPath = checkDir(os.path.join(self.coverPath, APPNAME))
        print 'debug: coverPath = ', self.coverPath

    def songIcon(self, song):#{{{2
        '''Try to get a cover image from folder.jpg, if that fails. Get an album
        cover from the interwebs. If it can't find an album cover it tries to get
        a picture of the artist.'''
        # comment out the next line to disable icon fetching.
        #return NOCOVER
        cover = None
        cover = self.getFolderImage(song)
        if not cover:
            #print 'debug: no folder.jpg'
            if not self.coverPath:
                return NOCOVER
            try:
                artist = auxilia.songArtist(song)
                album = song.get('album','')
                if artist != '?':
                    if album:
                        cover = self.getAlbumImage(artist,album)
                    if not cover:
                        cover = self.getArtistImage(artist)
            except Exception, e:
                print 'error: in iconretriever', e
            # Stil no picture? I give up.
        if cover:
            return cover
        return NOCOVER

    def getFolderImage(self, song):#{{{2
        if not self.musicPath:
            return None
        x = song['file'].rfind('/')
        dir = song['file'][:x]
        iconname = os.path.expanduser(self.musicPath) + '/' + dir + '/folder.jpg'
        if os.path.exists(iconname):
            return iconname
        else:
            return None

    def getAlbumImage(self, artist, album):#{{{2
        '''Get a album cover, return None on failure.'''
        coverFile = os.path.join(self.coverPath, auxilia.fileName(artist)+'-'+auxilia.fileName(album))
        # find cached version of the cover.
        cover = self._coverGlob(coverFile)
        if cover:
            return cover
        if album in self.unavailebleAlbums:
            return None
        # We don't have it in cache, get it from the web.
        # get the address of the cover file from last.fm.
        try:
            #print 'debug: Try to get an album cover from last.fm.'
            address = 'http://ws.audioscrobbler.com/2.0/?method=album.getinfo&api_key=%s&artist=%s&album=%s'
            handle = urllib.urlopen(address %
                    (APIKEY, urllib.quote_plus(artist.encode('utf-8')), urllib.quote_plus(album.encode('utf-8'))))
            cover = self._cacheImage(handle, coverFile)
        except Exception, e:
            print 'error: ', e,'\n', 'error: ', repr(urllib.quote_plus(artist.encode('utf-8'))),'\n', 'error: ', repr(urllib.quote_plus(album.encode('utf-8')))
            return None
        if not cover:
            self.unavailebleAlbums.append(album)
        return cover

    def getArtistImage(self, artist):#{{{2
        '''Get a picture of artist, return None on failure.'''
        coverFile = os.path.join(self.coverPath, auxilia.fileName(artist))
        # find cached version of the picture.
        cover = self._coverGlob(coverFile)
        if cover:
            return cover
        if artist in self.unavailebleArtists:
            return None
        # We don't have it in cache, get it from the web.
        # get the address of the picture from last.fm.
        try:
            #print 'debug: No album cover, a picture of the artist perhaps?.'
            address = 'http://ws.audioscrobbler.com/2.0/?method=artist.getinfo&artist=%s&api_key=%s'
            handle = urllib.urlopen(address % (urllib.quote_plus(artist.encode('utf-8')),APIKEY))
            cover = self._cacheImage(handle,coverFile)
        except Exception, e:
            print 'error: ', e,'\n', 'error: ', repr(urllib.quote_plus(artist.encode('utf-8')))
            return None
        if not cover:
            self.unavailebleArtists.append(artist)
        return cover

    def _cacheImage(self, handle, coverFile):#{{{2
        '''Download the image and save it in coverPath.'''
        imagePath = None
        for line in handle.read().decode('utf-8').split('\n'):
            line = line.strip()
            if line[:6] == '<error':
                # We got an error let's bail.
                return None
            if line[:19] == u'<image size="large"':
                # We got an image, move on.
                imagePath = line[20:-8]
                handle.close()
                break
        if imagePath:
            # we got an address lets cache the file.
            coverFile = coverFile+imagePath[-4:]
            urllib.urlretrieve(imagePath,coverFile)
            return coverFile
        # We got no image info from last.fm, well to bad.
        return None

    def _coverGlob(self, coverPath):#{{{2
        """
        Check if the cover file is in the cache. If it's not make sure we have
        some time between requests to the web services.
        """
        covers = glob(coverPath+'.*')
        if covers != [] and os.path.isfile(covers[0]):
            return covers[0]
        timeSinceLast = time.time() - self.lastContact
        if timeSinceLast <= SECONDS_BETWEEN_REQUESTS:
            time.sleep(SECONDS_BETWEEN_REQUESTS - timeSinceLast)
        self.lastContact = time.time()
        return None

class RetrieverThread(threading.Thread, Retriever):#{{{1
    def __init__(self, musicPath):
        threading.Thread.__init__(self)
        Retriever.__init__(self, musicPath)
        self.event = threading.Event()
        self.daemon = True
        self.toFetch = []
        self.icons = []
        self.running = True

    def run(self):
        while self.running:
            if self.toFetch:
                item = self.toFetch.pop(0)
                try:
                    # if we are the only one holding on to the item, get rid of it.
                    if getrefcount(item) > 2:
                        icon = self.songIcon(item.song)
                        self.icons.append((item, icon,))
                    else: print 'debug: '+unicode(item.text())
                except:
                    print 'debug: error while fetching icon'
                    raise
            else:
                self.event.wait()
                self.event.clear()
        print 'debug: exit iconfetcher'

    def exit(self):
        self.running = False
        self.event.set()
        self.join()

class ThreadedRetriever:#{{{1
    def __init__(self, musicPath):
        self.retriever = RetrieverThread(musicPath)
        self.icons = self.retriever.icons
        self.retriever.start()

    def fetchIcon(self, item, musicPath):
        if musicPath != self.retriever.path:
            self.retriever.exit()
        if not self.retriever.isAlive():
            self.retriever = RetrieverThread(musicPath)
            self.icons = self.retriever.icons
            self.retriever.start()
        self.retriever.toFetch.append(item)
        self.retriever.event.set()

    def killRetriever(self):
        self.retriever.exit()

def checkDir(path):
    if not os.path.exists(path):
        try:
            os.mkdir(path)
        except OSError, e:
            print 'error: ', e
            # We can't create the dir, let's bail.
            return None
    return path

