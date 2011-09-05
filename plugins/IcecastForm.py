# -*- coding: utf-8 -*
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
from PyQt4.QtCore import SIGNAL, QUrl, QEvent
from PyQt4.QtGui import QVBoxLayout
from PyQt4.QtWebKit import QWebView, QWebPage
try:
    from lxml import etree
except ImportError:
    import xml.etree.ElementTree as etree
import StringIO

import re
import httplib

import PluginBase

HOMEURL = "http://dir.xiph.org/"
TUNEIN = "dir.xiph.org"
TUNEINFORMAT = re.compile(r'/listen/\d+/listen\.(m3u|xspf)$')

class IcecastForm(PluginBase.PluginBase):
    ''' Embeds the xiph.org Icecast yellow pages, and loads the 
        streams from the m3u and XSPF playlist files.
    '''
    moduleName = 'I&cecast'
    moduleIcon = "network-workgroup"

    def load(self):
        pass

    def event(self, event):
        if event.type() == QEvent.Paint:
            if not hasattr(self, 'webView'):
                self._load()
                self.event = super(IcecastForm, self).event
        return False

    def _load(self):
        self.webView = QWebView(self)
        self.webPage = self.webView.page()

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.webView)
        self.webView.load(QUrl(HOMEURL))
        self.webPage.setLinkDelegationPolicy(QWebPage.DelegateExternalLinks)
        self.connect(self.webPage, SIGNAL('linkClicked(const QUrl&)'), self._processLink)

    def _processLink(self, url):
        urlString = unicode(url.toString())
        urlMatch = TUNEINFORMAT.search(urlString)
        if urlMatch is not None:
            self._playStation(urlString, urlMatch)
        else:
            self.webView.load(url)
            self.webView.show()

    def _playStation(self, url, match):
        path = match.group(0)
        format = match.group(1)
        data = self._retreivePlaylist(path)
        if format == 'xspf':
            adrlist = self._parseXSPF(data)
        else:
            adrlist = self._parseM3U(data)
        self.mpdclient.send('command_list_ok_begin')
        try:
            for address in adrlist:
                self.mpdclient.send('add', (address,))
        finally:
            self.mpdclient.send('command_list_end')

    def _retreivePlaylist(self, path):
        conn = httplib.HTTPConnection(TUNEIN)
        conn.request("GET", path)
        resp = conn.getresponse()
        if resp.status == 200:
            return resp.read()
        else:
            raise httplib.HTTPException('Got bad status code.')

    def _parseXSPF(self, data):
        ''' XSPF spec: http://www.xspf.org/xspf-v1.html
            Currently we only want the location URLs, so that
            is all we parse for.
        '''
        xml = etree.parse(StringIO.StringIO(data))
        root = xml.getroot()
        locations = root.findall('.//{http://xspf.org/ns/0/}location')
        adrlist = [adr.text.strip() for adr in locations 
                   if adr.text.startswith('http://')]
        if not adrlist:
             raise httplib.HTTPException('Encountered error during '
                                         'parsing of the playlist.')
        return adrlist
    
    def _parseM3U(self, data):
        adrlist = []
        data = data.split('\n')
        while data:
            line = data.pop(0)
            if line.startswith('http://'):
                adrlist.append(line.strip())
        if not adrlist:
             raise httplib.HTTPException('Encountered error during parsing of the playlist.')
        return adrlist


def getWidget(view, mpdclient, config, library):
    return IcecastForm(view, mpdclient, config, library)
