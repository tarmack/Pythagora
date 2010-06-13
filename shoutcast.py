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
from xml.etree import ElementTree as ET
import httplib
import urllib

#===============================================================================
class ShoutcastError(Exception):#{{{1
    '''Exception to encapsulate an error with the Shoutcast server.

This exception will actually occur quite a bit because the Shoutcast server is
a piece of shit.
'''
    def __init__(self,message,code):#{{{2
        self.msg = message
        self.code = code

    def __str__(self):#{{{2
        return "Error (%d): %s" % (self.code,self.msg)

#===============================================================================
class ShoutcastClient():#{{{1
    '''VERY Simple client for accessing Shoutcast streams.'''
    BASEURL = '207.200.98.25'

    #---------------------------------------------------------------------------
    def getGenereList(self):#{{{2
        '''Get list of genres'''
        data = self.__send__('/sbin/newxml.phtml')
        genrelist = []
        xml = ET.XML(data)
        for element in xml:
            genrelist.append(element.attrib['name'])
        genrelist.sort()
        return genrelist

    #---------------------------------------------------------------------------
    def getStationsForGenre(self,genre):#{{{2
        '''Get the list of stations for a genre.

Returns: tuneinBase - the base url to retrieve the stations' HTTP urls from
         stationlist - the list of stations for this genre

A station is a dictionary containing the following attributes:
    br,ct,genre,id,lc,mt,name

'name' is more useful for displays, whereas 'id' is used in conjunction with
'tuneinBase' from above to get the HTTP urls
'''
        data = self.__send__('/sbin/newxml.phtml?genre=' + genre)
        stationlist = []
        xml = ET.XML(data)
        for element in xml:
            station = {}
            if element.tag == 'tunein':
                tuneinBase = element.attrib['base']
            else:
                for n in ('br','ct','genre','id','lc','mt','name'):
                    station[n] = element.attrib[n]
                stationlist.append(station)
        stationlist.sort(key=lambda item:item['name'], reverse=False)
        return (tuneinBase,stationlist)

    #---------------------------------------------------------------------------
    def getStation(self,tuneinBase,stationId):#{{{2
        '''Get the HTTP URLs for the given station.

Arguments: tuneinBase = the base URL to use
           stationId = the ID of the station

Returns:    list of HTTP URLs for the station
'''
        data = self.__send__(tuneinBase + '?id=' + stationId)
        rtn = []
        for line in data.split('\n'):
            if line[:4] == 'File':
                rtn.append(line.split('=')[1])
        return rtn

    #---------------------------------------------------------------------------
    def getSearch(self, patern):#{{{2
        data = self.__send__('/sbin/newxml.phtml?search=' + patern)
        stationlist = []
        xml = ET.XML(data)
        for element in xml:
            station = {}
            if element.tag == 'tunein':
                tuneinBase = element.attrib['base']
            else:
                for n in ('br','ct','genre','id','lc','mt','name'):
                    station[n] = element.attrib[n]
                stationlist.append(station)
        stationlist.sort(key=lambda item:item['name'], reverse=False)
        return (tuneinBase,stationlist)


    #---------------------------------------------------------------------------
    def getCurrentTrack(self,stationName):#{{{2
        '''Extract the current track information for the given station name.'''
        params = {'search':stationName}
        url = '/sbin/newxml.phtml?' + urllib.urlencode(params)
        data = self.__send__(url,2)
        xml = ET.XML(data)
        for element in xml:
            if element.tag == 'station':
                return element.attrib['ct']

    #---------------------------------------------------------------------------
    def __send__(self,request,timeout=20):#{{{2
        conn = httplib.HTTPConnection(self.BASEURL, timeout=timeout)
        conn.request('GET',request)
        response = conn.getresponse()
        if response.status > 202:
            raise ShoutcastError('HTTP returned ' + response.reason,response.status)
        #print response.status, response.reason
        # And here we deal with the status response and reason
        # e.g. throw Exception
        data = response.read()
        conn.close()
        return data


# vim: set expandtab shiftwidth=4 softtabstop=4:
