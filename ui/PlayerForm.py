# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'PlayerForm.ui'
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

class Ui_PlayerForm(object):
    def setupUi(self, PlayerForm):
        PlayerForm.setObjectName(_fromUtf8("PlayerForm"))
        PlayerForm.resize(463, 96)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(PlayerForm.sizePolicy().hasHeightForWidth())
        PlayerForm.setSizePolicy(sizePolicy)
        self.gridLayout_2 = QtGui.QGridLayout(PlayerForm)
        self.gridLayout_2.setMargin(0)
        self.gridLayout_2.setVerticalSpacing(0)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.buttonsLayout = QtGui.QHBoxLayout()
        self.buttonsLayout.setSpacing(0)
        self.buttonsLayout.setContentsMargins(-1, 3, -1, -1)
        self.buttonsLayout.setObjectName(_fromUtf8("buttonsLayout"))
        self.back = QtGui.QToolButton(PlayerForm)
        self.back.setIconSize(QtCore.QSize(48, 48))
        self.back.setAutoRaise(True)
        self.back.setObjectName(_fromUtf8("back"))
        self.buttonsLayout.addWidget(self.back)
        self.play = QtGui.QToolButton(PlayerForm)
        self.play.setIconSize(QtCore.QSize(48, 48))
        self.play.setAutoRaise(True)
        self.play.setObjectName(_fromUtf8("play"))
        self.buttonsLayout.addWidget(self.play)
        self.stop = QtGui.QToolButton(PlayerForm)
        self.stop.setIconSize(QtCore.QSize(48, 48))
        self.stop.setAutoRaise(True)
        self.stop.setObjectName(_fromUtf8("stop"))
        self.buttonsLayout.addWidget(self.stop)
        self.forward = QtGui.QToolButton(PlayerForm)
        self.forward.setIconSize(QtCore.QSize(48, 48))
        self.forward.setCheckable(False)
        self.forward.setChecked(False)
        self.forward.setAutoRaise(True)
        self.forward.setObjectName(_fromUtf8("forward"))
        self.buttonsLayout.addWidget(self.forward)
        self.gridLayout_2.addLayout(self.buttonsLayout, 1, 0, 1, 1)
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setSizeConstraint(QtGui.QLayout.SetFixedSize)
        self.gridLayout.setContentsMargins(0, 2, -1, 3)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.titleLayout = QtGui.QVBoxLayout()
        self.titleLayout.setContentsMargins(4, 4, -1, -1)
        self.titleLayout.setObjectName(_fromUtf8("titleLayout"))
        self.gridLayout.addLayout(self.titleLayout, 0, 1, 1, 1)
        self.volume = QtGui.QSlider(PlayerForm)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.volume.sizePolicy().hasHeightForWidth())
        self.volume.setSizePolicy(sizePolicy)
        self.volume.setMaximum(100)
        self.volume.setPageStep(10)
        self.volume.setOrientation(QtCore.Qt.Vertical)
        self.volume.setObjectName(_fromUtf8("volume"))
        self.gridLayout.addWidget(self.volume, 0, 2, 2, 1)
        self.progress = QtGui.QProgressBar(PlayerForm)
        self.progress.setAcceptDrops(True)
        self.progress.setMaximum(1000)
        self.progress.setFormat(_fromUtf8(""))
        self.progress.setObjectName(_fromUtf8("progress"))
        self.gridLayout.addWidget(self.progress, 1, 1, 1, 1)
        self.songIcon = QtGui.QLabel(PlayerForm)
        self.songIcon.setLineWidth(0)
        self.songIcon.setText(_fromUtf8(""))
        self.songIcon.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft)
        self.songIcon.setObjectName(_fromUtf8("songIcon"))
        self.gridLayout.addWidget(self.songIcon, 0, 0, 2, 1)
        self.gridLayout_2.addLayout(self.gridLayout, 0, 1, 2, 1)
        self.toolBarLayout = QtGui.QHBoxLayout()
        self.toolBarLayout.setSpacing(1)
        self.toolBarLayout.setSizeConstraint(QtGui.QLayout.SetMinimumSize)
        self.toolBarLayout.setContentsMargins(-1, 0, -1, -1)
        self.toolBarLayout.setObjectName(_fromUtf8("toolBarLayout"))
        self.gridLayout_2.addLayout(self.toolBarLayout, 0, 0, 1, 1)
        self.gridLayout_2.setColumnStretch(1, 1)

        self.retranslateUi(PlayerForm)
        QtCore.QMetaObject.connectSlotsByName(PlayerForm)

    def retranslateUi(self, PlayerForm):
        PlayerForm.setWindowTitle(_translate("PlayerForm", "Form", None))
        self.songIcon.setToolTip(_translate("PlayerForm", "Click to enlarge", None))

