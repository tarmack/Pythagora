#!/usr/bin/env python

import os
from PyQt4 import uic
import re

def main():
    uiList = []
    for item in os.listdir('.'):
        if not item.startswith('_') and (
                item.endswith('.ui') or item.endswith('.ui.Qt')):
            uiList.append(item)

    for ui in uiList:
        if ui.endswith('.Qt'):
            out = ui[:-6]+'_Qt.py'
        else:
            out = ui[:-3]+'.py'
        print "Building python code for %s." % ui
        with open(ui, 'rb') as ui_file:
            with output_stream('../'+out, 'wb') as out_file:
                uic.compileUi(ui_file, out_file)


class output_stream(file):
    _buffer = ''

    def write(self, line):
        #print "###\n", line, "###\n",
        if re.match('\s*icon(\d*) = QtGui.QIcon()', line):
            self._buffer += line
        elif self._buffer and re.match('\s*icon.addPixmap\(QtGui.QPixmap\(_fromUtf8\("ui/icons/(.*\.png")', line):
            print "###", line
        file.write(self, line)

#       icon = QtGui.QIcon().fromTheme('edit-clear-list',
#       QtGui.QIcon(QtGui.QPixmap(_fromUtf8("ui/icons/edit-clear-list.png"))))
#
#       icon = QtGui.QIcon()
#       icon.addPixmap(QtGui.QPixmap(_fromUtf8("ui/icons/edit-clear-list.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)


if __name__ == '__main__':
    main()
