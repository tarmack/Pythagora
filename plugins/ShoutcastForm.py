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
from PyQt4.QtCore import SIGNAL, QUrl, QDateTime, QEvent
from PyQt4.QtGui import QVBoxLayout
from PyQt4.QtWebKit import QWebView, QWebPage
from PyQt4.QtNetwork import QNetworkCookie, QNetworkCookieJar
import httplib

import PluginBase
import streamTools

HOMEURL = "http://www.shoutcast.com/radio/top"
TUNEIN = "yp.shoutcast.com"
TUNEINFORMAT = "/sbin/tunein-station.pls?id=%s"

class ShoutCastForm(PluginBase.PluginBase):
    '''Grab Shoutcast streams and save them as "bookmarks" - and play them on
       the currently selected server.

       General shoutcast information is not preserved between runs. Also, the
       shoutcast server/API is pretty lame so timeouts actually occur quite
       frequently.
    '''
    moduleName = '&Shoutcast'
    moduleIcon = "network-workgroup"

    def load(self):
        pass

    def event(self, event):
        if event.type() == QEvent.Paint:
            if not hasattr(self, 'webView'):
                self._load()
                self.event = super(ShoutCastForm, self).event
        return False

    def _load(self):
        self.cookie = QNetworkCookie('Settings', 'Player~others|Bandwidth~ALL|Codec~ALL')
        self.cookie.setDomain('.shoutcast.com')
        self.cookie.setExpirationDate(QDateTime())
        self.cookie.setPath('/')

        self.webView = QWebView(self)
        self.webPage = self.webView.page()
        self.cookiejar = QNetworkCookieJar()
        self.cookiejar.setAllCookies([self.cookie])
        self.webPage.networkAccessManager().setCookieJar(self.cookiejar)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.webView)
        self.webView.load(QUrl(HOMEURL))
        self.webPage.setLinkDelegationPolicy(QWebPage.DelegateExternalLinks)
        self.connect(self.webPage, SIGNAL('linkClicked(const QUrl&)'), self._processLink)

    def _processLink(self, url):
        if url.host() == TUNEIN:
            self._playStation(url.toString())
        else:
            self.webView.load(url)
            self.webView.show()

    def _playStation(self, url):
        data = self._retreivePLS(url)
        if data:
            try:
                adrlist = streamTools._parsePLS(data)
            except streamTools.ParseError:
                return
            self.mpdclient.send('command_list_ok_begin')
            try:
                for address in adrlist:
                    self.mpdclient.send('add', (address,))
            finally:
                self.mpdclient.send('command_list_end')

    def _retreivePLS(self, url):
        conn = httplib.HTTPConnection(TUNEIN)
        conn.request("GET", TUNEINFORMAT % url.split('=')[-1])
        resp = conn.getresponse()
        if resp.status == 200:
            return resp.read()
        else:
            raise httplib.HTTPException('Got bad status code.')


def getWidget(modelManager, view, mpdclient, config, library):
    return ShoutCastForm(modelManager, view, mpdclient, config, library)
