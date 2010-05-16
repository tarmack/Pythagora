#!/usr/bin/python
from PyQt4.QtCore import QSettings
from PyQt4.QtGui import QApplication
import signal
import sys

settings = QSettings('foo', 'bar')

def main():
    signal.signal(signal.SIGINT, keyboardInterrupt)
    app = QApplication([])
    app.exec_()

def doSetting(settings):
    value = int(settings.value('something').toInt()[1])
    settings.setValue('something', value+1)

def keyboardInterrupt(self, signum, frame):#{{{2
    print 'KeyboardInterrupt'
    try:
        self.app.quit()
    except:
        sys.exit(1)

if __name__ == "__main__":
    main()
