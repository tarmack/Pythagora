# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Pythagora.ui'
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

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        MainWindow.resize(599, 683)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        MainWindow.setToolButtonStyle(QtCore.Qt.ToolButtonFollowStyle)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.verticalLayout = QtGui.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setContentsMargins(-1, 0, -1, 0)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.topLayout = QtGui.QHBoxLayout()
        self.topLayout.setObjectName(_fromUtf8("topLayout"))
        self.verticalLayout.addLayout(self.topLayout)
        self.MainLayout = QtGui.QHBoxLayout()
        self.MainLayout.setSizeConstraint(QtGui.QLayout.SetNoConstraint)
        self.MainLayout.setObjectName(_fromUtf8("MainLayout"))
        self.splitter = QtGui.QSplitter(self.centralwidget)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName(_fromUtf8("splitter"))
        self.tabs = QtGui.QTabWidget(self.splitter)
        self.tabs.setAcceptDrops(True)
        self.tabs.setTabPosition(QtGui.QTabWidget.West)
        self.tabs.setMovable(True)
        self.tabs.setObjectName(_fromUtf8("tabs"))
        self.verticalLayoutWidget = QtGui.QWidget(self.splitter)
        self.verticalLayoutWidget.setObjectName(_fromUtf8("verticalLayoutWidget"))
        self.currentListLayout = QtGui.QVBoxLayout(self.verticalLayoutWidget)
        self.currentListLayout.setMargin(0)
        self.currentListLayout.setObjectName(_fromUtf8("currentListLayout"))
        self.MainLayout.addWidget(self.splitter)
        self.verticalLayout.addLayout(self.MainLayout)
        self.verticalLayout.setStretch(1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        self.tabs.setCurrentIndex(-1)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow", None))

