# -*- coding: utf-8 -*
#-------------------------------------------------------------------------------
# Copyright 2009 E. A. Graham Jr. <txcrackers@gmail.com>.
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
from PyQt4.QtCore import Qt, QPointF
from PyQt4.QtGui import QListWidgetItem, QTreeWidgetItem, QBrush, QLabel\
        , QFontMetrics, QPainter, QLinearGradient, QPalette, QPen

import auxilia
import shoutcast
import os

# TODO: Don't show 'by' and 'from' in SongLabel if that part is missing.

#===============================================================================
# List and tree widget items formatted in various ways for the forms to display
# stuff with.
#===============================================================================

class CurrentListWidget(QListWidgetItem):
    '''Song, album, cover in a tree widget item'''
    # Used in CurrentPlaylistForm
    def __init__(self, song, oneLine=False):
        QListWidgetItem.__init__(self)
        self.icon = False
        self.song = song
        if oneLine:
            self.setText(auxilia.songArtist(song) + ' - ' + auxilia.songTitle(song))
        else:
            self.setText(auxilia.songTitle(song) + '\n' + auxilia.songArtist(song))
        self.setToolTip("Album:\t %s\nTime:\t %s\nFile:\t %s" % (auxilia.songAlbum(song), str(auxilia.songTime(song)) , song['file']))

    def setIcon(self, icon):
        self.icon = bool(icon)
        QListWidgetItem.setIcon(self, icon)

    def playing(self, playing):
        font = self.font()
        if playing:
            font.setWeight(75)
        else:
            font.setWeight(50)
        self.setFont(font)

    def getDrag(self, mpdclient):
        return [self.song]

class AlbumWidget(QListWidgetItem):
    '''Simple for album in library view.'''
    def __init__(self, text, tooltip):
        QListWidgetItem.__init__(self)
        self.setText(text)
        self.setToolTip('\n'.join(tooltip))

    def getDrag(self, mpdclient):
        return mpdclient.find('album', self.text())

class ArtistWidget(QListWidgetItem):
    '''Simple widget for artists in library view.'''
    def __init__(self, text):
        QListWidgetItem.__init__(self)
        self.setText(text)

    def getDrag(self, mpdclient):
        return mpdclient.find('artist', self.text())

class TrackWidget(QTreeWidgetItem):
    '''Track widget used in library track view.'''
    def __init__(self, song):
        QTreeWidgetItem.__init__(self)
        self.song = song
        self.setText(0,auxilia.songTrack(song))
        self.setText(1,auxilia.songTitle(song))
        self.setText(2,auxilia.songTime(song))
        self.setToolTip(1, "Artist:\t %s\nAlbum:\t %s\nFile:\t %s"\
                % (auxilia.songArtist(song), auxilia.songAlbum(song), song['file']))

    def getDrag(self, mpdclient):
        return [self.song]

class FilesystemWidget(QTreeWidgetItem):
    '''Widget used in the filesystem tree.'''
    def __init__(self, text, icon):
        self.icons = {
                'file': auxilia.PIcon('audio-x-generic'),
                'directory': auxilia.PIcon('folder-sound')
                }
        QTreeWidgetItem.__init__(self)
        self.setText(0, text)
        self.setIcon(0, self.icons[icon])

    def getDrag(self, mpdclient, path=''):
        text = unicode(self.text(0))
        if path == '':
            path = text
        else:
            path = os.path.join(text, path)
        parent = self.parent()
        if parent:
            return parent.getDrag(mpdclient, path)
        else:
            return [song for song in mpdclient.listall(path) if 'file' in song]

class PlaylistWidget(QListWidgetItem):
    '''Widget used in the stored playlist list.'''
    def __init__(self, text):
        QListWidgetItem.__init__(self)
        self.setText(text)

    def getDrag(self, mpdclient):
        return mpdclient.listplaylistinfo(self.text())

class LongSongWidget(QTreeWidgetItem):
    '''Lays out a song in a three-column tree widget: artist, title, album.
    Used in PlaylistForm.'''
    def __init__(self, song, pos):
        QTreeWidgetItem.__init__(self)
        self.song = song
        self.pos = pos
        self.setText(0,auxilia.songArtist(song))
        self.setText(1,auxilia.songTitle(song))
        self.setText(2,auxilia.songAlbum(song))

    def getDrag(self, mpdclient):
        return [self.song]

class ShoutCastStationWidget(QTreeWidgetItem):
    '''Gives us in item storage of the station information this is needed to tune in to the station.'''
    def __init__(self, station):
        QTreeWidgetItem.__init__(self)
        self.station = station
        self.setText(0, station['name'])

    def text(self):
        return self.station['name']

    def getDrag(self, mpdclient):
        client = shoutcast.ShoutcastClient()
        item = self.station['id']
        urls = client.getStation(item)
        return [{'file': url} for url in urls]

class ShoutCastBookmarkWidget(QListWidgetItem):
    '''Gives us in item storage of the station information this is needed to tune in to the station.'''
    def __init__(self, station):
        QListWidgetItem.__init__(self)
        self.station = station
        self.setText(station['name'])

    def getDrag(self, mpdclient):
        return [{'file': url} for url in self.urls]

class SongLabel(QLabel):
    title = 'title'
    artist = 'artist'
    album = 'album'
    parts = ('title', 'artist', 'album')
    prepends = {
            'artist': 'by',
            'album': 'from'
            }
    def __init__(self):
        QLabel.__init__(self)
        self.setAlignment(Qt.AlignBottom)
        self.titleFont = self.font()
        self.titleFont.setPointSize(self.font().pointSize()+2)
        self.titleFont.setBold(True)
        self.artistFont = self.font()
        self.artistFont.setPointSize(self.font().pointSize()+2)
        self.albumFont = self.font()
        self.albumFont.setItalic(True)

    def setText(self, title='', artist='', album=''):
        self.title = title
        self.artist = artist
        self.album = album
        self.repaint()

    def paintEvent(self, event):
        gradient = self.__gradient()
        self.spaceLeft = self.contentsRect()
        for part in self.parts:
            font = getattr(self, '%sFont' % part)
            text = getattr(self, part)
            if text:
                self.__write(self.prepends.get(part, ''), self.font(), gradient)
            self.__write(text, font, gradient)
        if self.spaceLeft.width() <= 0:
            if self.title:
                title = '<b><big>%s</big></b>' % self.title
            if self.artist:
                artist = 'by <big>%s</big>' % self.artist
            if self.album:
                album = 'from <i>%s</i>' % self.album
            tooltip = '<br>'.join((item for item in (title, artist, album) if item))
            self.setToolTip(tooltip)
        else: self.setToolTip('')

    def __write(self, text, font, pen):
        if self.spaceLeft != self.contentsRect():
            text = ' '+text
        fm = QFontMetrics(font)
        textRect = fm.tightBoundingRect(text)
        painter = QPainter(self)
        painter.setFont(font)
        painter.setPen(pen)
        painter.drawText(self.spaceLeft, Qt.AlignBottom, text)
        self.spaceLeft.setLeft(self.spaceLeft.left() + textRect.width()) # move the left edge to the end of what we just painted.

    def __gradient(self):
        left = QPointF(self.contentsRect().topLeft())
        right = QPointF(self.contentsRect().topRight())
        gradient = QLinearGradient(left, right)
        gradient.setColorAt(0.9, self.palette().color(QPalette.WindowText))
        gradient.setColorAt(1.0, self.palette().color(QPalette.Window))
        pen = QPen()
        pen.setBrush(QBrush(gradient))
        return pen

