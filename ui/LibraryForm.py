# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'LibraryForm.ui'
#
# Created: Mon Apr  2 21:30:45 2012
#      by: PyQt4 UI code generator 4.8.5
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_LibraryForm(object):
    def setupUi(self, LibraryForm):
        LibraryForm.setObjectName(_fromUtf8("LibraryForm"))
        LibraryForm.resize(570, 512)
        LibraryForm.setWindowTitle(QtGui.QApplication.translate("LibraryForm", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.horizontalLayout = QtGui.QHBoxLayout(LibraryForm)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.libSplitter_1 = QtGui.QSplitter(LibraryForm)
        self.libSplitter_1.setOrientation(QtCore.Qt.Vertical)
        self.libSplitter_1.setObjectName(_fromUtf8("libSplitter_1"))
        self.libSplitter_2 = QtGui.QSplitter(self.libSplitter_1)
        self.libSplitter_2.setOrientation(QtCore.Qt.Horizontal)
        self.libSplitter_2.setObjectName(_fromUtf8("libSplitter_2"))
        self.widget = QtGui.QWidget(self.libSplitter_2)
        self.widget.setObjectName(_fromUtf8("widget"))
        self.gridLayout = QtGui.QGridLayout(self.widget)
        self.gridLayout.setMargin(0)
        self.gridLayout.setSpacing(0)
        self.gridLayout.setMargin(0)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.label = QtGui.QLabel(self.widget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setText(QtGui.QApplication.translate("LibraryForm", "Artist", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setMargin(2)
        self.label.setIndent(2)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.artistSearchField = KLineEdit(self.widget)
        self.artistSearchField.setProperty("trapEnterKeyEvent", True)
        self.artistSearchField.setProperty("showClearButton", True)
        self.artistSearchField.setObjectName(_fromUtf8("artistSearchField"))
        self.gridLayout.addWidget(self.artistSearchField, 0, 1, 1, 2)
        self.artistView = QtGui.QListView(self.widget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(2)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.artistView.sizePolicy().hasHeightForWidth())
        self.artistView.setSizePolicy(sizePolicy)
        self.artistView.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.artistView.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.artistView.setDragEnabled(True)
        self.artistView.setDragDropMode(QtGui.QAbstractItemView.DragOnly)
        self.artistView.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.artistView.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.artistView.setHorizontalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.artistView.setObjectName(_fromUtf8("artistView"))
        self.gridLayout.addWidget(self.artistView, 1, 0, 2, 3)
        self.widget_3 = QtGui.QWidget(self.libSplitter_2)
        self.widget_3.setObjectName(_fromUtf8("widget_3"))
        self.gridLayout_3 = QtGui.QGridLayout(self.widget_3)
        self.gridLayout_3.setMargin(0)
        self.gridLayout_3.setSpacing(0)
        self.gridLayout_3.setMargin(0)
        self.gridLayout_3.setObjectName(_fromUtf8("gridLayout_3"))
        self.albumSearchField = KLineEdit(self.widget_3)
        self.albumSearchField.setProperty("trapEnterKeyEvent", True)
        self.albumSearchField.setProperty("showClearButton", True)
        self.albumSearchField.setObjectName(_fromUtf8("albumSearchField"))
        self.gridLayout_3.addWidget(self.albumSearchField, 0, 1, 1, 1)
        self.label_3 = QtGui.QLabel(self.widget_3)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_3.sizePolicy().hasHeightForWidth())
        self.label_3.setSizePolicy(sizePolicy)
        self.label_3.setText(QtGui.QApplication.translate("LibraryForm", "Album", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setMargin(2)
        self.label_3.setIndent(2)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.gridLayout_3.addWidget(self.label_3, 0, 0, 1, 1)
        self.albumView = QtGui.QListView(self.widget_3)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(3)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.albumView.sizePolicy().hasHeightForWidth())
        self.albumView.setSizePolicy(sizePolicy)
        self.albumView.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.albumView.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.albumView.setDragEnabled(True)
        self.albumView.setDragDropMode(QtGui.QAbstractItemView.DragOnly)
        self.albumView.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.albumView.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.albumView.setHorizontalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.albumView.setObjectName(_fromUtf8("albumView"))
        self.gridLayout_3.addWidget(self.albumView, 1, 0, 1, 3)
        self.showAllAlbums = QtGui.QPushButton(self.widget_3)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.showAllAlbums.sizePolicy().hasHeightForWidth())
        self.showAllAlbums.setSizePolicy(sizePolicy)
        self.showAllAlbums.setToolTip(QtGui.QApplication.translate("LibraryForm", "Resets the album list to show all your albums again.", None, QtGui.QApplication.UnicodeUTF8))
        self.showAllAlbums.setText(QtGui.QApplication.translate("LibraryForm", "Show All", None, QtGui.QApplication.UnicodeUTF8))
        self.showAllAlbums.setObjectName(_fromUtf8("showAllAlbums"))
        self.gridLayout_3.addWidget(self.showAllAlbums, 0, 2, 1, 1)
        self.widget_4 = QtGui.QWidget(self.libSplitter_1)
        self.widget_4.setObjectName(_fromUtf8("widget_4"))
        self.gridLayout_9 = QtGui.QGridLayout(self.widget_4)
        self.gridLayout_9.setMargin(0)
        self.gridLayout_9.setSpacing(0)
        self.gridLayout_9.setMargin(0)
        self.gridLayout_9.setObjectName(_fromUtf8("gridLayout_9"))
        self.label_2 = QtGui.QLabel(self.widget_4)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy)
        self.label_2.setText(QtGui.QApplication.translate("LibraryForm", "Tracks", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setMargin(2)
        self.label_2.setIndent(2)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.gridLayout_9.addWidget(self.label_2, 0, 0, 1, 1)
        self.trackSearchField = KLineEdit(self.widget_4)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.trackSearchField.sizePolicy().hasHeightForWidth())
        self.trackSearchField.setSizePolicy(sizePolicy)
        self.trackSearchField.setProperty("trapEnterKeyEvent", True)
        self.trackSearchField.setProperty("showClearButton", True)
        self.trackSearchField.setObjectName(_fromUtf8("trackSearchField"))
        self.gridLayout_9.addWidget(self.trackSearchField, 0, 1, 1, 1)
        self.trackView = QtGui.QTableView(self.widget_4)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.trackView.sizePolicy().hasHeightForWidth())
        self.trackView.setSizePolicy(sizePolicy)
        self.trackView.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.trackView.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.trackView.setTabKeyNavigation(True)
        self.trackView.setDragEnabled(True)
        self.trackView.setDragDropMode(QtGui.QAbstractItemView.DragOnly)
        self.trackView.setAlternatingRowColors(True)
        self.trackView.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.trackView.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.trackView.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.trackView.setHorizontalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.trackView.setShowGrid(False)
        self.trackView.setCornerButtonEnabled(False)
        self.trackView.setObjectName(_fromUtf8("trackView"))
        self.trackView.horizontalHeader().setDefaultSectionSize(50)
        self.trackView.horizontalHeader().setHighlightSections(False)
        self.trackView.horizontalHeader().setMinimumSectionSize(32)
        self.trackView.horizontalHeader().setStretchLastSection(False)
        self.trackView.verticalHeader().setVisible(False)
        self.trackView.verticalHeader().setDefaultSectionSize(16)
        self.trackView.verticalHeader().setMinimumSectionSize(16)
        self.gridLayout_9.addWidget(self.trackView, 1, 0, 1, 3)
        self.showAllTracks = QtGui.QPushButton(self.widget_4)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.showAllTracks.sizePolicy().hasHeightForWidth())
        self.showAllTracks.setSizePolicy(sizePolicy)
        self.showAllTracks.setToolTip(QtGui.QApplication.translate("LibraryForm", "Resets the track list to show all your songs again.", None, QtGui.QApplication.UnicodeUTF8))
        self.showAllTracks.setText(QtGui.QApplication.translate("LibraryForm", "Show All", None, QtGui.QApplication.UnicodeUTF8))
        self.showAllTracks.setObjectName(_fromUtf8("showAllTracks"))
        self.gridLayout_9.addWidget(self.showAllTracks, 0, 2, 1, 1)
        self.horizontalLayout.addWidget(self.libSplitter_1)
        self.label.setBuddy(self.artistSearchField)
        self.label_3.setBuddy(self.albumSearchField)
        self.label_2.setBuddy(self.trackSearchField)

        self.retranslateUi(LibraryForm)
        QtCore.QMetaObject.connectSlotsByName(LibraryForm)
        LibraryForm.setTabOrder(self.artistSearchField, self.artistView)
        LibraryForm.setTabOrder(self.artistView, self.albumSearchField)
        LibraryForm.setTabOrder(self.albumSearchField, self.showAllAlbums)
        LibraryForm.setTabOrder(self.showAllAlbums, self.albumView)
        LibraryForm.setTabOrder(self.albumView, self.trackSearchField)
        LibraryForm.setTabOrder(self.trackSearchField, self.showAllTracks)
        LibraryForm.setTabOrder(self.showAllTracks, self.trackView)

    def retranslateUi(self, LibraryForm):
        pass

from PyKDE4.kdeui import KLineEdit