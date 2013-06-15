# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'FileSystemForm.ui'
#
# Created: Sat Aug 11 18:48:04 2012
#      by: PyQt4 UI code generator 4.9.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_FileSystemForm(object):
    def setupUi(self, FileSystemForm):
        FileSystemForm.setObjectName(_fromUtf8("FileSystemForm"))
        FileSystemForm.resize(400, 300)
        self.horizontalLayout = QtGui.QHBoxLayout(FileSystemForm)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.filesystemTree = QtGui.QTreeView(FileSystemForm)
        self.filesystemTree.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.filesystemTree.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.filesystemTree.setDragEnabled(True)
        self.filesystemTree.setDragDropMode(QtGui.QAbstractItemView.DragOnly)
        self.filesystemTree.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.filesystemTree.setSelectionBehavior(QtGui.QAbstractItemView.SelectItems)
        self.filesystemTree.setIconSize(QtCore.QSize(16, 16))
        self.filesystemTree.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.filesystemTree.setUniformRowHeights(True)
        self.filesystemTree.setAnimated(True)
        self.filesystemTree.setObjectName(_fromUtf8("filesystemTree"))
        self.horizontalLayout.addWidget(self.filesystemTree)

        self.retranslateUi(FileSystemForm)
        QtCore.QMetaObject.connectSlotsByName(FileSystemForm)

    def retranslateUi(self, FileSystemForm):
        FileSystemForm.setWindowTitle(QtGui.QApplication.translate("FileSystemForm", "Form", None, QtGui.QApplication.UnicodeUTF8))

