# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'FileSystemForm.ui'
#
# Created: Wed Jul  2 23:15:57 2014
#      by: PyQt4 UI code generator 4.11
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

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
        FileSystemForm.setWindowTitle(_translate("FileSystemForm", "Form", None))

