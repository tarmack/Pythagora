# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'PlaylistsForm.ui'
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

class Ui_PlaylistsForm(object):
    def setupUi(self, PlaylistsForm):
        PlaylistsForm.setObjectName(_fromUtf8("PlaylistsForm"))
        PlaylistsForm.resize(400, 300)
        self.horizontalLayout = QtGui.QHBoxLayout(PlaylistsForm)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.playlistSplitter = QtGui.QSplitter(PlaylistsForm)
        self.playlistSplitter.setOrientation(QtCore.Qt.Vertical)
        self.playlistSplitter.setObjectName(_fromUtf8("playlistSplitter"))
        self.widget_5 = QtGui.QWidget(self.playlistSplitter)
        self.widget_5.setObjectName(_fromUtf8("widget_5"))
        self.gridLayout_5 = QtGui.QGridLayout(self.widget_5)
        self.gridLayout_5.setMargin(0)
        self.gridLayout_5.setObjectName(_fromUtf8("gridLayout_5"))
        self.widget_6 = QtGui.QWidget(self.widget_5)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget_6.sizePolicy().hasHeightForWidth())
        self.widget_6.setSizePolicy(sizePolicy)
        self.widget_6.setObjectName(_fromUtf8("widget_6"))
        self.gridLayout_4 = QtGui.QGridLayout(self.widget_6)
        self.gridLayout_4.setMargin(0)
        self.gridLayout_4.setObjectName(_fromUtf8("gridLayout_4"))
        self.newButton = QtGui.QPushButton(self.widget_6)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.newButton.sizePolicy().hasHeightForWidth())
        self.newButton.setSizePolicy(sizePolicy)
        self.newButton.setMaximumSize(QtCore.QSize(120, 16777215))
        self.newButton.setAcceptDrops(True)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8("ui/icons/document-new.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.newButton.setIcon(icon)
        self.newButton.setObjectName(_fromUtf8("newButton"))
        self.gridLayout_4.addWidget(self.newButton, 0, 0, 1, 1)
        self.deleteButton = QtGui.QPushButton(self.widget_6)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.deleteButton.sizePolicy().hasHeightForWidth())
        self.deleteButton.setSizePolicy(sizePolicy)
        self.deleteButton.setMaximumSize(QtCore.QSize(120, 16777215))
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(_fromUtf8("ui/icons/edit-delete.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.deleteButton.setIcon(icon1)
        self.deleteButton.setObjectName(_fromUtf8("deleteButton"))
        self.gridLayout_4.addWidget(self.deleteButton, 1, 0, 1, 1)
        self.loadButton = QtGui.QPushButton(self.widget_6)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.loadButton.sizePolicy().hasHeightForWidth())
        self.loadButton.setSizePolicy(sizePolicy)
        self.loadButton.setMaximumSize(QtCore.QSize(120, 16777215))
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(_fromUtf8("ui/icons/text-frame-link.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.loadButton.setIcon(icon2)
        self.loadButton.setObjectName(_fromUtf8("loadButton"))
        self.gridLayout_4.addWidget(self.loadButton, 2, 0, 1, 1)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout_4.addItem(spacerItem, 3, 0, 1, 1)
        self.gridLayout_5.addWidget(self.widget_6, 0, 2, 4, 1)
        self.playlistList = QtGui.QListView(self.widget_5)
        self.playlistList.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.playlistList.setAcceptDrops(True)
        self.playlistList.setDragEnabled(True)
        self.playlistList.setDragDropMode(QtGui.QAbstractItemView.DragDrop)
        self.playlistList.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.playlistList.setHorizontalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.playlistList.setUniformItemSizes(True)
        self.playlistList.setObjectName(_fromUtf8("playlistList"))
        self.gridLayout_5.addWidget(self.playlistList, 0, 0, 4, 2)
        self.songList = QtGui.QTableView(self.playlistSplitter)
        self.songList.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.songList.setAcceptDrops(True)
        self.songList.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.songList.setDragEnabled(True)
        self.songList.setDragDropMode(QtGui.QAbstractItemView.DragDrop)
        self.songList.setAlternatingRowColors(True)
        self.songList.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.songList.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.songList.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.songList.setHorizontalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.songList.setShowGrid(False)
        self.songList.setWordWrap(False)
        self.songList.setCornerButtonEnabled(False)
        self.songList.setObjectName(_fromUtf8("songList"))
        self.songList.horizontalHeader().setDefaultSectionSize(180)
        self.songList.horizontalHeader().setHighlightSections(False)
        self.songList.verticalHeader().setVisible(False)
        self.songList.verticalHeader().setDefaultSectionSize(20)
        self.horizontalLayout.addWidget(self.playlistSplitter)

        self.retranslateUi(PlaylistsForm)
        QtCore.QMetaObject.connectSlotsByName(PlaylistsForm)

    def retranslateUi(self, PlaylistsForm):
        PlaylistsForm.setWindowTitle(_translate("PlaylistsForm", "Form", None))
        self.newButton.setText(_translate("PlaylistsForm", "New", None))
        self.deleteButton.setText(_translate("PlaylistsForm", "Delete", None))
        self.loadButton.setText(_translate("PlaylistsForm", "Load", None))

