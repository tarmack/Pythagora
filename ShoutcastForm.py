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
from PyQt4.QtCore import SIGNAL, Qt
from PyQt4.QtGui import QWidget, QMessageBox, QTreeWidgetItem, QKeySequence, QListWidget, QListWidgetItem
from PyQt4 import uic

from xml.etree import ElementTree as ET
import os

import shoutcast
import auxilia

DATA_DIR = ''

class ShoutcastForm(QWidget, auxilia.Actions):
    '''Grab Shoutcast streams and save them as "bookmarks" - and play them on
       the currently selected server.

       General shoutcast information is not preserved between runs. Also, the
       shoutcast server/API is pretty lame so timeouts actually occur quite
       frequently.
    '''
    moduleName = '&Shoutcast'
    moduleIcon = "network-workgroup"
    stations = {}

    def __init__(self, view, app, mpdclient, config):
        QWidget.__init__(self)
        self.view = view
        self.config = config
        if self.view.KDE:
            uic.loadUi(DATA_DIR+'ui/ShoutCastForm.ui', self)
        else:
            uic.loadUi(DATA_DIR+'ui/ShoutCastForm.ui.Qt', self)
        self.scSplitter.setSizes(config.mgrScSplit)
        self.adding = False
        self.search = False
        self.stationTree = StationTree(self)

        self.bookMarkList = BookmarkList(self, os.path.expanduser(config.scBookmarkFile))
        self.bookMarkList.reload()

        self.client = shoutcast.ShoutcastClient()
        self.mpdclient = mpdclient

        # connect to the lists and buttons
        self.connect(self.reloadGenres, SIGNAL('clicked()'), self.__loadGenres)
        self.connect(self.scSearch, SIGNAL('returnPressed(QString)'), self.__loadSearch)

        self.connect(self.genreList, SIGNAL('itemSelectionChanged()'), self.__treeSelect)
        self.connect(self.genreList, SIGNAL('itemDoubleClicked(QTreeWidgetItem*,int)'), self.__previewStation)
        self.connect(self.bookmarkList, SIGNAL('itemDoubleClicked(QListWidgetItem*)'), self.__play)
        self.connect(self.saveStation, SIGNAL('clicked()'), self.__saveStation)
        self.connect(self.previewStation, SIGNAL('clicked()'), self.__previewStation)
        self.connect(self.scSplitter, SIGNAL('splitterMoved(int, int)'), self.__storeSplitter)

        # Add context menu's
        self.actionPreview(self.genreList, self.__previewStation)
        self.actionBookmark(self.genreList, self.__saveStation)
        self.actionScReload(self.genreList, self.__loadGenres)
        self.actionPlayBM(self.bookmarkList, self.__play)
        self.actionRemove(self.bookmarkList, self.bookMarkList.delete)

        self.bookmarkList.dropEvent = self.dropEvent
        self.bookmarkList.dragEnterEvent = self.dragEnterEvent

    def dragEnterEvent(self, event):
        source = event.source()
        if source == self.genreList:
            if isinstance(source.selectedItems()[0], ShoutCastStationWidget):
                event.accept()

    def dropEvent(self, event):
        event.setDropAction(Qt.CopyAction)
        source = event.source()
        if source == self.genreList:
            event.accept()
            self.__saveStation()

    def reload(self):
        self.bookMarkList.reload()

    def __loadGenres(self):
        '''Retrieve the genres.'''
        if not self.adding:
            self.adding = True
            self.view.setCursor(Qt.WaitCursor)
            try:
                genrelist = self.client.getGenereList()
                # populate tree and clear saved stations
                self.stationTree.loadTree(genrelist)
                self.stationTree.stations = {}
            except Exception,e:
                QMessageBox(QMessageBox.Critical,'Shoutcast Error',str(e),QMessageBox.Ok,self.view).exec_()
                raise
            self.adding = False
            self.view.setCursor(Qt.ArrowCursor)

    def __loadSearch(self, patern):
        print 'debug: loading search results.'
        patern = unicode(patern)
        if patern == '':
            self.stationTree.search = False
            self.__loadGenres()
            return
        self.stationTree.search = True
        self.view.setCursor(Qt.WaitCursor)
        try:
            stationlist = self.client.getSearch(patern)
            # cache it, then add to the tree
            self.genreList.clear()
            self.stationTree.loadStations(stationlist)
        except Exception,e:
            print 'error: ', str(e)
        finally:
            self.view.setCursor(Qt.ArrowCursor)

    def __treeSelect(self):
        '''Figure out what to do when something's selected in the list'''
        current = self.genreList.currentItem()
        # child node - it's a station
        if current.parent() != None or self.stationTree.search:
            return

        genre = str(current.text(0))

        # not already loaded
        if current.childCount() <= 0:
            self.view.setCursor(Qt.WaitCursor)
            try:
                stationlist = self.client.getStationsForGenre(genre)
                self.stationTree.loadStations(stationlist)
            except Exception,e:
                print 'error: ', str(e)
                current.setSelected(False)
            finally:
                self.view.setCursor(Qt.ArrowCursor)

    def __previewStation(self, item=None):
        '''Play the currently selected station.'''
        station = self.stationTree.currentStation()
        urls = self.client.getStation(station['id'])
        station['urls'] = urls
        self.mpdclient.send('stop')
        self.mpdclient.send('clear')
        for url in urls:
            self.mpdclient.send('add', (url,))
        self.mpdclient.send('play')

    def __play(self, item=None):
        '''Play the currently selected bookmarked station.'''
        self.mpdclient.send('stop')
        self.mpdclient.send('clear')
        for url in self.bookMarkList.getStationFiles():
            self.mpdclient.send('add', (url,))
        self.mpdclient.send('play')

    def __saveStation(self):
        '''Bookmark the currently selected station.'''
        station = self.stationTree.currentStation()
        if station.get('urls',None) == None:
            urls = self.client.getStation(station['id'])
            station['urls'] = urls
        self.bookMarkList.addStation(station)

    def __storeSplitter(self):
        self.config.mgrScSplit = self.scSplitter.sizes()


class StationTree():
    '''The main shoutcast tree: genres and stations.'''
    def __init__(self, view):
        # top - tree
        self.search = False
        self.view = view
        view.connect(self.view.genreList, SIGNAL('itemClicked(QTreeWidgetItem*,int)'), self.__treeClick)

    def __treeClick(self):
        current = self.view.genreList.currentItem()
        if current.isExpanded():
            current.setExpanded(False)
        else:
            current.setExpanded(True)

    def loadTree(self, genrelist):
        '''Reload the tree from the given list of genres.'''
        self.view.genreList.clear()
        for genre in genrelist:
            gw = QTreeWidgetItem([genre])
            self.view.genreList.addTopLevelItem(gw)

    def loadStations(self, stationlist):
        '''Append the stations to the currently selected genre.'''
        current = self.view.genreList.currentItem()
        if current == None:
            current = self.view.genreList.invisibleRootItem()
        for station in stationlist:
            current.addChild(ShoutCastStationWidget(station))

    def currentStation(self):
        '''Figure out and return the current station and the base URL for it.'''
        current = self.view.genreList.currentItem()
        # parent node - genre, bleah
        parent = current.parent()
        if parent == None:
            if not self.search:
                return None
            else:
                parent = self.view.genreList.invisibleRootItem()
        name = str(current.text())
        for i in xrange(parent.childCount()):
            station = parent.child(i).station
            if station['name'] == name:
                return station
        return None


class BookmarkList():
    '''The list of bookmarked stations.'''
    def __init__(self, view, bookmarkFile):
        self.view = view
        self.bookmarkFile = os.path.expanduser(bookmarkFile)
        self.view.bookmarkList.keyPressEvent = self.keyPressEvent

    def reload(self):
        # read in and hang on to the bookmarks
        if os.path.isfile(self.bookmarkFile):
            self.xml = ET.parse(self.bookmarkFile)
            for element in self.xml.getiterator('station'):
                widget = ShoutCastBookmarkWidget(element.attrib)
                widget.urls = self.getStationFiles(element.attrib['name'])
                self.view.bookmarkList.addItem(widget)
        # start it ourselves
        else:
            try:
                root = ET.Element('bookmarks')
                root.append(ET.Element('stations'))
                self.xml = ET.ElementTree(root)
                self.xml.write(self.bookmarkFile,'UTF-8')
            except Exception, e:
                print 'error: ', e

    def __getStation(self,name):
        '''Find a station by name.'''
        stations = self.xml.findall('//station')
        for station in stations:
            if station.attrib['name'] == name:
                return station
        return None

    def getStationFiles(self, name=None):
        '''Get the URLs for the currently selected station.'''
        if name == None:
            name = str(self.view.bookmarkList.currentItem().text())
        station = self.__getStation(name)
        rtn = []
        for url in station.getiterator('url'):
            rtn.append(url.text)
            print 'debug: ', url.text
        return rtn

    def addStation(self,station):
        '''Create a new bookmark.'''
        # see if we already have it
        element = self.__getStation(station['name'])
        # nope - make new one and add to list
        if element == None:
            element = ET.Element('station')
            stations = self.xml.find('stations')
            stations.append(element)
            self.view.bookmarkList.addItem(ShoutCastBookmarkWidget(station))
        # in both cases, set data and save
        for key in station.keys():
            if key != 'urls':
                element.set(key,station[key])
            else:
                urls = ET.Element('urls')
                element.append(urls)
                for url in station['urls']:
                    ue = ET.Element('url')
                    ue.text = url
                    urls.append(ue)

        self.xml.write(self.bookmarkFile,'UTF-8')

    def delete(self):
        '''Delete the current bookmark.'''
        row = self.view.bookmarkList.currentRow()
        current = self.view.bookmarkList.takeItem(row)
        name = str(current.text())
        # remove from list
        self.view.bookmarkList.removeItemWidget(current)
        # remove from data and save
        station = self.__getStation(name)
        stations = self.xml.find('stations')
        stations.remove(station)
        self.xml.write(self.bookmarkFile,'UTF-8')

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.Delete):
            self.delete()
        else:
            QListWidget.keyPressEvent(self.view.bookmarkList, event)

# Widget subclasses.
class ShoutCastStationWidget(QTreeWidgetItem):
    '''Gives us in item storage of the station information this is needed to tune in to the station.'''
    def __init__(self, station):
        QTreeWidgetItem.__init__(self)
        self.station = station
        self.setText(0, station['name'])

    def text(self):
        return self.station['name']

    def getDrag(self):
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

    def getDrag(self):
        return [{'file': url} for url in self.urls]

