#!/usr/bin/env python

import os
from PyQt4 import uic

uiList = []
for item in os.listdir('.'):
    if not item.startswith('_') and '.ui' in item:
        uiList.append(item)

for ui in uiList:
    if ui.endswith('.Qt'):
        out = ui[:-6]+'_Qt.py'
    else:
        out = ui[:-3]+'.py'
    with open(ui, 'rb') as ui_file:
        with open('../'+out, 'wb') as out_file:
            uic.compileUi(ui_file, out_file)
