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
'''
This module contains tools for stream handling.
'''
try:
    from lxml import etree
except ImportError:
    import xml.etree.ElementTree as etree
import StringIO
import httplib

class ParseError(Exception):
    pass

def getStreamList(url):
    if url.endswith('.pls'):
        data = _retreiveURL(url)
        if data:
            adrlist = parsePLS(data)
    elif url.endswith('.m3u'):
        data = _retreiveURL(url)
        if data:
            adrlist = parseM3U(data)
    elif url.endswith('.xspf'):
        data = _retreiveURL(url)
        if data:
            adrlist = parseXSPF(data)
    else:
        adrlist = [url]
    return adrlist

def parsePLS(data):
    ''' Parse a PLS playlist. Returns a list with stream addresses.'''
    adrlist = []
    state = ''
    data = data.split('\n')
    while data:
        line = data.pop(0)
        if state == '' and line == '[playlist]':
            state = 'playlist'
        elif state == 'playlist':
            if '=' in line:
                key, value = line.split('=', 1)
                if key.startswith('File'):
                    adrlist.append(value)
        else:
            raise ParseError('Encountered error during parsing of the playlist.')
    return adrlist

def parseXSPF(data):
    ''' Parse a XSPF playlist. Returns a list with stream addresses.
        XSPF spec: http://www.xspf.org/xspf-v1.html
        Currently we only want the location URLs, so that
        is all we parse for.
    '''
    xml = etree.parse(StringIO.StringIO(data))
    root = xml.getroot()
    locations = root.findall('.//{http://xspf.org/ns/0/}location')
    adrlist = [adr.text.strip() for adr in locations 
               if adr.text.startswith('http://')]
    if not adrlist:
         raise ParseError('Encountered error during '
                                     'parsing of the playlist.')
    return adrlist

def parseM3U(data):
    ''' Parse a M3U playlist. Returns a list with stream addresses.'''
    adrlist = []
    data = data.split('\n')
    while data:
        line = data.pop(0)
        if line.startswith('http://'):
            adrlist.append(line.strip())
    if not adrlist:
         raise ParseError('Encountered error during parsing of the playlist.')
    return adrlist

def _retreiveURL(url):
    if url.startswith('http://'):
        url = url[7:]
    server, path = url.split('/', 1)
    conn = httplib.HTTPConnection(server)
    conn.request("GET", '/'+path)
    resp = conn.getresponse()
    if resp.status == 200:
        return resp.read()
    else:
        raise httplib.HTTPException('Got bad status code.')

