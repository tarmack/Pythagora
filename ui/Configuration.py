# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Configuration.ui'
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

class Ui_Configuration(object):
    def setupUi(self, Configuration):
        Configuration.setObjectName(_fromUtf8("Configuration"))
        Configuration.resize(563, 255)
        self.verticalLayout = QtGui.QVBoxLayout(Configuration)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.tabs = QtGui.QTabWidget(Configuration)
        self.tabs.setObjectName(_fromUtf8("tabs"))
        self.mainTab = QtGui.QWidget()
        self.mainTab.setObjectName(_fromUtf8("mainTab"))
        self.gridLayout = QtGui.QGridLayout(self.mainTab)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.coverPath = QtGui.QLineEdit(self.mainTab)
        self.coverPath.setObjectName(_fromUtf8("coverPath"))
        self.gridLayout.addWidget(self.coverPath, 4, 1, 1, 1)
        self.coverDirButton = QtGui.QPushButton(self.mainTab)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8("ui/icons/document-open-folder.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.coverDirButton.setIcon(icon)
        self.coverDirButton.setObjectName(_fromUtf8("coverDirButton"))
        self.gridLayout.addWidget(self.coverDirButton, 4, 2, 1, 2)
        self.showNotificationWidget = QtGui.QWidget(self.mainTab)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.showNotificationWidget.sizePolicy().hasHeightForWidth())
        self.showNotificationWidget.setSizePolicy(sizePolicy)
        self.showNotificationWidget.setObjectName(_fromUtf8("showNotificationWidget"))
        self.horizontalLayout = QtGui.QHBoxLayout(self.showNotificationWidget)
        self.horizontalLayout.setMargin(0)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.showNotification = QtGui.QCheckBox(self.showNotificationWidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.showNotification.sizePolicy().hasHeightForWidth())
        self.showNotification.setSizePolicy(sizePolicy)
        self.showNotification.setObjectName(_fromUtf8("showNotification"))
        self.horizontalLayout.addWidget(self.showNotification)
        self.notificationTimeout = QtGui.QSpinBox(self.showNotificationWidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.notificationTimeout.sizePolicy().hasHeightForWidth())
        self.notificationTimeout.setSizePolicy(sizePolicy)
        self.notificationTimeout.setMaximumSize(QtCore.QSize(48, 16777215))
        self.notificationTimeout.setObjectName(_fromUtf8("notificationTimeout"))
        self.horizontalLayout.addWidget(self.notificationTimeout)
        self.label_3 = QtGui.QLabel(self.showNotificationWidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_3.sizePolicy().hasHeightForWidth())
        self.label_3.setSizePolicy(sizePolicy)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.horizontalLayout.addWidget(self.label_3)
        self.gridLayout.addWidget(self.showNotificationWidget, 0, 1, 1, 3)
        self.label = QtGui.QLabel(self.mainTab)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 4, 0, 1, 1)
        self.tabs.addTab(self.mainTab, _fromUtf8(""))
        self.serverTab = QtGui.QWidget()
        self.serverTab.setObjectName(_fromUtf8("serverTab"))
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.serverTab)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.serverTable = QtGui.QTableWidget(self.serverTab)
        self.serverTable.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        self.serverTable.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.serverTable.setShowGrid(True)
        self.serverTable.setObjectName(_fromUtf8("serverTable"))
        item = QtGui.QTableWidgetItem()
        self.serverTable.setHorizontalHeaderItem(0, item)
        item = QtGui.QTableWidgetItem()
        self.serverTable.setHorizontalHeaderItem(1, item)
        item = QtGui.QTableWidgetItem()
        self.serverTable.setHorizontalHeaderItem(2, item)
        item = QtGui.QTableWidgetItem()
        self.serverTable.setHorizontalHeaderItem(3, item)
        self.serverTable.horizontalHeader().setStretchLastSection(True)
        self.serverTable.verticalHeader().setVisible(False)
        self.verticalLayout_2.addWidget(self.serverTable)
        self.tabs.addTab(self.serverTab, _fromUtf8(""))
        self.verticalLayout.addWidget(self.tabs)
        self.buttonBox = QtGui.QDialogButtonBox(Configuration)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout.addWidget(self.buttonBox)
        self.label.setBuddy(self.coverPath)

        self.retranslateUi(Configuration)
        self.tabs.setCurrentIndex(0)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), Configuration.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), Configuration.reject)
        QtCore.QMetaObject.connectSlotsByName(Configuration)
        Configuration.setTabOrder(self.tabs, self.coverPath)
        Configuration.setTabOrder(self.coverPath, self.coverDirButton)
        Configuration.setTabOrder(self.coverDirButton, self.serverTable)
        Configuration.setTabOrder(self.serverTable, self.buttonBox)

    def retranslateUi(self, Configuration):
        Configuration.setWindowTitle(_translate("Configuration", "Dialog", None))
        self.coverPath.setToolTip(_translate("Configuration", "Path to the mpd library root to use folder.jpg\'s as cover art.\n"
"If no folder.jpg can be found the cover art will be downloaded and cached in the \'covers\' subdirectory.", None))
        self.coverDirButton.setToolTip(_translate("Configuration", "Browse for the directory.", None))
        self.coverDirButton.setText(_translate("Configuration", "Browse", None))
        self.showNotification.setText(_translate("Configuration", "Show notifications on song change for ", None))
        self.label_3.setText(_translate("Configuration", "seconds", None))
        self.label.setToolTip(_translate("Configuration", "Path to the mpd library root to use folder.jpg\'s as cover art.\n"
"If no folder.jpg can be found the cover art will be downloaded and cached in the \'covers\' subdirectory.", None))
        self.label.setText(_translate("Configuration", "Cover directory:", None))
        self.tabs.setTabText(self.tabs.indexOf(self.mainTab), _translate("Configuration", "Main", None))
        item = self.serverTable.horizontalHeaderItem(0)
        item.setText(_translate("Configuration", "Name", None))
        item = self.serverTable.horizontalHeaderItem(1)
        item.setText(_translate("Configuration", "Address", None))
        item = self.serverTable.horizontalHeaderItem(2)
        item.setText(_translate("Configuration", "Port", None))
        item = self.serverTable.horizontalHeaderItem(3)
        item.setText(_translate("Configuration", "Password", None))
        self.tabs.setTabText(self.tabs.indexOf(self.serverTab), _translate("Configuration", "Servers", None))

