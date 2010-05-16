# -*- coding: utf-8 -*
#-------------------------------------------------------------------------------{{{
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
#-------------------------------------------------------------------------------}}}
from PyQt4.QtCore import SIGNAL, Qt
from PyQt4.QtGui import QMessageBox, QTreeWidgetItem, QKeySequence, QListWidget

from xml.etree import ElementTree as ET
import os

import shoutcast
from auxilia import Actions

class ShoutcastForm(Actions):#{{{1
    '''Grab Shoutcast streams and save them as "bookmarks" - and play them on
       the currently selected server.

       General shoutcast information is not preserved between runs. Also, the
       shoutcast server/API is pretty lame so timeouts actually occur quite
       frequently.
    '''
    stations = {}

    def __init__(self, view, app, mpdclient, bookmarkFile):#{{{2
        self.view = view
        self.adding = False
        self.search = False
        self.stationTree = StationTree(view)

        self.bookmarkList = BookmarkList(view, os.path.expanduser(bookmarkFile))
        self.bookmarkList.reload()

        self.client = shoutcast.ShoutcastClient()
        self.mpd = mpdclient

        # connect to the lists and buttons
        view.connect(self.view.reloadGenres, SIGNAL('clicked()'), self.__loadGenres)
        view.connect(self.view.scSearch, SIGNAL('returnPressed(QString)'), self.__loadSearch)

        view.connect(self.view.genreList, SIGNAL('itemSelectionChanged()'), self.__treeSelect)
        view.connect(self.view.genreList, SIGNAL('itemDoubleClicked(QTreeWidgetItem*,int)'), self.__previewStation)
        view.connect(self.view.bookmarkList, SIGNAL('itemDoubleClicked(QListWidgetItem*)'), self.__play)
        #self.connect(self.view.playStation, SIGNAL('clicked()'), self.__previewStation)
        view.connect(self.view.saveStation, SIGNAL('clicked()'), self.__saveStation)
        #self.connect(self.bookmarkList.play,SIGNAL('clicked()'),self.__play)

        # Add conext menu's
        self.actionPreview(self.view.genreList, self.__previewStation)
        self.actionBookmark(self.view.genreList, self.__saveStation)
        self.actionScReload(self.view.genreList, self.__loadGenres)
        self.actionPlayBM(self.view.bookmarkList, self.__play)
        self.actionRemove(self.view.bookmarkList, self.bookmarkList.delete)

        self.view.bookmarkList.dropEvent = self.dropEvent

    def dropEvent(self, event):#{{{2
        event.setDropAction(Qt.CopyAction)
        source = event.source()
        if source == self.view.genreList:
            event.accept()
            self.__saveStation()

    def reload(self):#{{{2
        self.bookmarkList.reload()
        #self.__loadGenres()

    def __loadGenres(self):#{{{2
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
            self.adding = False
            self.view.setCursor(Qt.ArrowCursor)

    def __loadSearch(self, patern):#{{{2
        print 'debug: loading search results.'
        patern = unicode(patern)
        if patern == '':
            self.stationTree.search = False
            self.reload()
            return
        self.stationTree.search = True
        self.view.setCursor(Qt.WaitCursor)
        try:
            (tuneinBase,stationlist) = self.client.getSearch(patern)
            # cache it, then add to the tree
            self.stationTree.stations['search'] = (tuneinBase,stationlist)
            self.view.genreList.clear()
            self.stationTree.loadStations(stationlist)
        except Exception,e:
            print 'error: ', str(e)
            #QMessageBox(QMessageBox.Critical,'Shoutcast Error',str(e),QMessageBox.Ok,self).exec_()
        finally:
            self.view.setCursor(Qt.ArrowCursor)

    def __treeSelect(self):#{{{2
        '''Figure out what to do when something's selected in the list'''
        current = self.view.genreList.currentItem()
        # child node - it's a station
        if current.parent() != None and not self.stationTree.search:
            return

        genre = str(current.text(0))

        # not already loaded
        if not genre in self.stationTree.stations.keys():
            self.view.setCursor(Qt.WaitCursor)
            try:
                (tuneinBase,stationlist) = self.client.getStationsForGenre(genre)
                # cache it, then add to the tree
                self.stationTree.stations[genre] = (tuneinBase,stationlist)
                self.stationTree.loadStations(stationlist)
            except Exception,e:
                print 'error: ', str(e)
                #QMessageBox(QMessageBox.Critical,'Shoutcast Error',str(e),QMessageBox.Ok,self).exec_()
                current.setSelected(False)
            finally:
                self.view.setCursor(Qt.ArrowCursor)

    def __previewStation(self, item=None):#{{{2
        '''Play the currently selected station.'''
        (tuneinBase,station) = self.stationTree.currentStation()
        #try:
        urls = self.client.getStation(tuneinBase,station['id'])
        station['urls'] = urls
        self.mpd.stop()
        self.mpd.clear()
        for url in urls:
            self.mpd.add(url)
        self.mpd.play()
        #except Exception,e:
        #    QMessageBox(QMessageBox.Critical,'Shoutcast Error',str(e),QMessageBox.Ok,self).exec_()

    def __play(self, item=None):#{{{2
        '''Play the currently selected bookmarked station.'''
        #try:
        self.mpd.stop()
        self.mpd.clear()
        for url in self.bookmarkList.getStationFiles():
            self.mpd.add(url)
        self.mpd.play()
        #except Exception,e:
        #    QMessageBox(QMessageBox.Critical,'Shoutcast Error',str(e),QMessageBox.Ok,self).exec_()

    def __saveStation(self):#{{{2
        '''Bookmark the currently selected station.'''
        (tuneinBase,station) = self.stationTree.currentStation()
        #try:
        if station.get('urls',None) == None:
            urls = self.client.getStation(tuneinBase,station['id'])
            station['urls'] = urls
        self.bookmarkList.addStation(station)
        #except Exception,e:
        #    print 'error: ', e
            #QMessageBox(QMessageBox.Critical,'Shoutcast Error',str(e),QMessageBox.Ok,self).exec_()

#===============================================================================
class StationTree():#{{{1
    '''The main shoutcast tree: genres and stations.'''
    def __init__(self, view):#{{{2
        # top - tree
        self.search = False
        self.view = view
        view.connect(self.view.genreList, SIGNAL('itemClicked(QTreeWidgetItem*,int)'), self.__treeClick)

    def __treeClick(self):#{{{2
        '''Enable/disable buttons based on what's selected'''
        current = self.view.genreList.currentItem()
        if current.isExpanded():
            current.setExpanded(False)
        else:
            current.setExpanded(True)
        # child node - it's a station
        #self.play.setEnabled(current.parent() != None)
        #self.save.setEnabled(current.parent() != None)

    def loadTree(self, genrelist):#{{{2
        '''Reload the tree from the given list of genres.'''
        self.view.genreList.clear()
        for genre in genrelist:
            gw = QTreeWidgetItem([genre])
            self.view.genreList.addTopLevelItem(gw)

    def loadStations(self,stationlist):#{{{2
        '''Append the stations to the currently selected genre.'''
        current = self.view.genreList.currentItem()
        if current == None:
            current = self.view.genreList.invisibleRootItem()
        for station in stationlist:
            current.addChild(QTreeWidgetItem([station['name']]))

    def currentStation(self):#{{{2
        '''Figure out and return the current station and the base URL for it.'''
        current = self.view.genreList.currentItem()
        # parent node - genre, bleah
        if current.parent() == None and not self.search:
            return None
        name = str(current.text(0))
        if self.search:
            genre = 'search'
        else:
            genre = str(current.parent().text(0))
        (tuneinBase,stationlist) = self.stations[genre]
        for station in stationlist:
            if station['name'] == name:
                return (tuneinBase,station)
        return None

#===============================================================================
class BookmarkList():#{{{1
    '''The list of bookmarked stations.'''
    def __init__(self, view, bookmarkFile):#{{{2
        self.view = view
        self.bookmarkFile = os.path.expanduser(bookmarkFile)
        self.view.bookmarkList.keyPressEvent = self.keyPressEvent

    def reload(self):#{{{2
        # read in and hang on to the bookmarks
        if os.path.isfile(self.bookmarkFile):
            self.xml = ET.parse(self.bookmarkFile)
            for element in self.xml.getiterator('station'):
                self.view.bookmarkList.addItem(element.attrib['name'])
        # start it ourselves
        else:
            try:
                root = ET.Element('bookmarks')
                root.append(ET.Element('stations'))
                self.xml = ET.ElementTree(root)
                self.xml.write(self.bookmarkFile,'UTF-8')
            except Exception, e:
                print 'error: ', e

    def __getStation(self,name):#{{{2
        '''Find a station by name.'''
        stations = self.xml.findall('//station')
        for station in stations:
            if station.attrib['name'] == name:
                return station
        return None

    def getStationFiles(self):#{{{2
        '''Get the URLs for the currently selected station.'''
        name = str(self.view.bookmarkList.currentItem().text())
        station = self.__getStation(name)
        rtn = []
        for url in station.getiterator('url'):
            rtn.append(url.text)
        return rtn

    def addStation(self,station):#{{{2
        '''Create a new bookmark.'''
        # see if we already have it
        element = self.__getStation(station['name'])
        # nope - make new one and add to list
        if element == None:
            element = ET.Element('station')
            stations = self.xml.find('stations')
            stations.append(element)
            self.view.bookmarkList.addItem(station['name'])
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

    def delete(self):#{{{2
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

    def keyPressEvent(self, event):#{{{2
        if event.matches(QKeySequence.Delete):
            self.delete()
        else:
            QListWidget.keyPressEvent(self.view.bookmarkList, event)


# vim: set expandtab shiftwidth=4 softtabstop=4:
