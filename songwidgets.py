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
from PyQt4.QtGui import QListWidgetItem, QTreeWidgetItem, QBrush, QColor, QLabel\
        , QFontMetrics, QPainter, QLinearGradient, QPalette, QPen

import auxilia

# TODO: Don't show 'by' and 'from' in SongLabel if that part is missing.

#===============================================================================
# List and tree widget items formatted in various ways for the forms to display
# stuff with.
#===============================================================================

class FullTreeWidget(QListWidgetItem):
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
        self.setToolTip("Album:\t %s\nTime:\t %s\nFile:\t %s" % (song.get('album', ''), str(auxilia.songTime(song)) , song['file']))

    def setIcon(self, icon):
        self.icon = bool(icon)
        QListWidgetItem.setIcon(self, icon)

    def playing(self, playing):
        font = self.font()
        if playing:
            font.setWeight(75)
            brush = QBrush(QColor(0, 0, 0, 0), Qt.SolidPattern)
        else:
            font.setWeight(50)
            brush = QBrush(Qt.NoBrush)
        self.setFont(font)
        self.setBackground(brush)

class simpleWidget(QListWidgetItem):
    '''Simple for album in library view.'''
    def __init__(self, text, tooltip):
        QListWidgetItem.__init__(self)
        self.setText(text)
        self.setToolTip('\n'.join(tooltip))

class TrackWidget(QTreeWidgetItem):
    '''Track widget used in library track view.'''
    def __init__(self, song):
        QTreeWidgetItem.__init__(self)
        self.song = song
        self.setText(0,song.get('track', '#'))
        self.setText(1,auxilia.songTitle(song))
        self.setText(2,auxilia.songTime(song))
        self.setToolTip(1, "Artist:\t %s\nAlbum:\t %s\nFile:\t %s"\
                % (auxilia.songArtist(song), song.get('album', ''), song['file']))

class LongSongWidget(QTreeWidgetItem):
    '''Lays out a song in a three-column tree widget: artist, title, album.
    Used in PlaylistForm.'''
    def __init__(self, song, pos):
        QTreeWidgetItem.__init__(self)
        self.song = song
        self.pos = pos
        self.setText(0,song.get('artist','?'))
        self.setText(1,auxilia.songTitle(song))
        self.setText(2,song.get('album',''))

class SongLabel(QLabel):
    title = 'title'
    artist = 'artist'
    album = 'album'
    by = ' by '
    from_ = ' from '
    parts = ('title', 'by', 'artist', 'from_', 'album')
    def __init__(self):
        QLabel.__init__(self)
        self.byFont = self.font()
        self.from_Font = self.byFont
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
            text = getattr(self, part)+' '
            fm = QFontMetrics(font)
            textRect = fm.tightBoundingRect(text)
            painter = QPainter(self)
            painter.setFont(font)
            painter.setPen(gradient)
            painter.drawText(self.spaceLeft, Qt.AlignBottom, text)
            self.spaceLeft.setLeft(self.spaceLeft.left() + textRect.width()) # move the left edge to the end of what we just painted.
        if self.spaceLeft.width() <= 0:
            tooltip = '<b><big>%s</big></b> by <big>%s</big> from <i>%s</i>' % (self.title, self.artist, self.album)
            self.setToolTip(tooltip)
        else: self.setToolTip('')

    def __gradient(self):
        left = QPointF(self.contentsRect().topLeft())
        right = QPointF(self.contentsRect().topRight())
        gradient = QLinearGradient(left, right)
        gradient.setColorAt(0.9, self.palette().color(QPalette.WindowText))
        gradient.setColorAt(1.0, self.palette().color(QPalette.Window))
        pen = QPen()
        pen.setBrush(QBrush(gradient))
        return pen

