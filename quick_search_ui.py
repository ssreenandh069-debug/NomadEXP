# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'NomadUI.ui'
##
## Created by: Qt User Interface Compiler version 6.11.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QDialog, QFrame, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QPushButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

class Ui_quick_search(object):
    def setupUi(self, quick_search):
        if not quick_search.objectName():
            quick_search.setObjectName(u"quick_search")
        quick_search.resize(709, 508)
        quick_search.setStyleSheet(u"#quick_search_frame {\n"
"    background-color: #1e1e1e;\n"
"    border: 1px solid #4f5a61; \n"
"    border-radius: 12px;       \n"
"}\n"
"\n"
"QLineEdit {\n"
"    background: transparent;\n"
"    font-size: 20px;\n"
"    color: #FFFFFF;\n"
"}\n"
"\n"
"#filter_bar {\n"
"	background:#121212;\n"
"	border-radius:5px;\n"
"}\n"
"\n"
"#filter_bar QPushButton {\n"
"    background-color: transparent;\n"
"    border: 1px solid transparent;\n"
"    border-radius: 12px; \n"
"    padding: 6px 14px;\n"
"    color: #A0A0A0;\n"
"    font-size: 13px;\n"
"    font-weight: bold;\n"
"}\n"
"\n"
"#filter_bar QPushButton:hover {\n"
"    background-color: #2A2A2A;\n"
"    color: #FFFFFF;\n"
"	border: 1px solid transparent;\n"
"	border-radius: 15px;\n"
"}\n"
"\n"
"#filter_bar QPushButton:checked {\n"
"    background-color: #0078d4; \n"
"    color: #FFFFFF;\n"
"	border: 1px solid #0078D4;\n"
"	border-radius: 15px;\n"
"}\n"
"QFrame[frameShape=\"4\"] {  /*horizontal Lines*/\n"
"    border:none;\n"
"	border-top: 1px solid #4f5a61;\n"
"  "
                        "  background-color: #4f5a61; \n"
"    min-height: 1px;\n"
"    max-height: 1px;\n"
"}\n"
"QFrame[frameShape=\"5\"] { /*vertical Lines*/\n"
"    border: none;\n"
"	border-left: 1px solid #4f5a61;\n"
"    background-color: #4f5a61;\n"
"    min-width: 1px;\n"
"    max-width: 1px;\n"
"}\n"
"#search_bar QPushButton{\n"
"	background:transparent;\n"
"}\n"
"#search_bar QPushButton:hover{\n"
"	background:#313131;\n"
"}\n"
"\n"
"#open_file {\n"
"    background-color: #0078D4;\n"
"    color: white;\n"
"    border-radius: 6px;\n"
"    padding: 10px;\n"
"    font-size: 13px;\n"
"    font-weight: bold;\n"
"}\n"
"#open_file:hover {\n"
"    background-color: #108AE6;\n"
"}\n"
"\n"
"#open_file_location {\n"
"    background-color: transparent;\n"
"    color: #FFFFFF;\n"
"    border: 1px solid #555555;\n"
"    border-radius: 6px;\n"
"    padding: 10px;\n"
"    font-size: 13px;\n"
"}\n"
"\n"
"#open_file_location:hover {\n"
"    background-color: #2A2A2A;\n"
"}\n"
"\n"
"#metadata QLabel {\n"
"    color: #CCCCCC;\n"
"}\n"
"\n"
"#re"
                        "sult_list {\n"
"    background: transparent;\n"
"    border: none;\n"
"    outline: none;\n"
"}\n"
"\n"
"#result_list::item {\n"
"    color: #E0E0E0;\n"
"    padding: 8px 12px; \n"
"    border-radius: 6px; \n"
"    margin: 2px 5px; \n"
"}\n"
"\n"
"#result_list::item:hover {\n"
"    background-color: #2A2A2A;\n"
"}\n"
"\n"
"#result_list::item:selected {\n"
"    background-color: #333333;\n"
"    border-left: 3px solid #0078D4;\n"
"}")
        self.verticalLayout = QVBoxLayout(quick_search)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.quick_search_frame = QFrame(quick_search)
        self.quick_search_frame.setObjectName(u"quick_search_frame")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.quick_search_frame.sizePolicy().hasHeightForWidth())
        self.quick_search_frame.setSizePolicy(sizePolicy)
        self.quick_search_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.quick_search_frame.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_2 = QVBoxLayout(self.quick_search_frame)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(-1, 0, -1, -1)
        self.search_bar = QWidget(self.quick_search_frame)
        self.search_bar.setObjectName(u"search_bar")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.search_bar.sizePolicy().hasHeightForWidth())
        self.search_bar.setSizePolicy(sizePolicy1)
        self.horizontalLayout = QHBoxLayout(self.search_bar)
        self.horizontalLayout.setSpacing(20)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(15, 8, 15, 15)
        self.search_icon = QLabel(self.search_bar)
        self.search_icon.setObjectName(u"search_icon")

        self.horizontalLayout.addWidget(self.search_icon)

        self.search_bar_2 = QLineEdit(self.search_bar)
        self.search_bar_2.setObjectName(u"search_bar_2")
        font = QFont()
        font.setBold(False)
        self.search_bar_2.setFont(font)
        self.search_bar_2.setFrame(False)
        self.search_bar_2.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout.addWidget(self.search_bar_2)

        self.exit_program = QPushButton(self.search_bar)
        self.exit_program.setObjectName(u"exit_program")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.exit_program.sizePolicy().hasHeightForWidth())
        self.exit_program.setSizePolicy(sizePolicy2)
        self.exit_program.setMaximumSize(QSize(30, 30))
        self.exit_program.setFlat(True)

        self.horizontalLayout.addWidget(self.exit_program)


        self.verticalLayout_2.addWidget(self.search_bar)

        self.line = QFrame(self.quick_search_frame)
        self.line.setObjectName(u"line")
        self.line.setFrameShadow(QFrame.Shadow.Plain)
        self.line.setFrameShape(QFrame.Shape.HLine)

        self.verticalLayout_2.addWidget(self.line)

        self.filter_bar = QWidget(self.quick_search_frame)
        self.filter_bar.setObjectName(u"filter_bar")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.filter_bar.sizePolicy().hasHeightForWidth())
        self.filter_bar.setSizePolicy(sizePolicy3)
        self.filter_bar.setStyleSheet(u"")
        self.horizontalLayout_2 = QHBoxLayout(self.filter_bar)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.All = QPushButton(self.filter_bar)
        self.All.setObjectName(u"All")
        self.All.setCheckable(True)
        self.All.setChecked(True)
        self.All.setAutoExclusive(True)

        self.horizontalLayout_2.addWidget(self.All)

        self.Apps = QPushButton(self.filter_bar)
        self.Apps.setObjectName(u"Apps")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.Apps.sizePolicy().hasHeightForWidth())
        self.Apps.setSizePolicy(sizePolicy4)
        font1 = QFont()
        font1.setBold(True)
        self.Apps.setFont(font1)
        self.Apps.setCheckable(True)
        self.Apps.setChecked(False)
        self.Apps.setAutoExclusive(True)

        self.horizontalLayout_2.addWidget(self.Apps)

        self.pdfs = QPushButton(self.filter_bar)
        self.pdfs.setObjectName(u"pdfs")
        sizePolicy4.setHeightForWidth(self.pdfs.sizePolicy().hasHeightForWidth())
        self.pdfs.setSizePolicy(sizePolicy4)
        self.pdfs.setCheckable(True)
        self.pdfs.setChecked(False)
        self.pdfs.setAutoExclusive(True)

        self.horizontalLayout_2.addWidget(self.pdfs)

        self.docs = QPushButton(self.filter_bar)
        self.docs.setObjectName(u"docs")
        sizePolicy4.setHeightForWidth(self.docs.sizePolicy().hasHeightForWidth())
        self.docs.setSizePolicy(sizePolicy4)
        self.docs.setCheckable(True)
        self.docs.setAutoExclusive(True)

        self.horizontalLayout_2.addWidget(self.docs)

        self.Images = QPushButton(self.filter_bar)
        self.Images.setObjectName(u"Images")
        sizePolicy4.setHeightForWidth(self.Images.sizePolicy().hasHeightForWidth())
        self.Images.setSizePolicy(sizePolicy4)
        self.Images.setCheckable(True)
        self.Images.setAutoExclusive(True)

        self.horizontalLayout_2.addWidget(self.Images)

        self.Folders = QPushButton(self.filter_bar)
        self.Folders.setObjectName(u"Folders")
        sizePolicy4.setHeightForWidth(self.Folders.sizePolicy().hasHeightForWidth())
        self.Folders.setSizePolicy(sizePolicy4)
        self.Folders.setCheckable(True)
        self.Folders.setAutoExclusive(True)

        self.horizontalLayout_2.addWidget(self.Folders)

        self.horizontalSpacer = QSpacerItem(150, 10, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)


        self.verticalLayout_2.addWidget(self.filter_bar)

        self.line_2 = QFrame(self.quick_search_frame)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.Shape.HLine)
        self.line_2.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_2.addWidget(self.line_2)

        self.bottom_split = QWidget(self.quick_search_frame)
        self.bottom_split.setObjectName(u"bottom_split")
        self.horizontalLayout_3 = QHBoxLayout(self.bottom_split)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.left_panel = QWidget(self.bottom_split)
        self.left_panel.setObjectName(u"left_panel")
        self.verticalLayout_4 = QVBoxLayout(self.left_panel)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.best_match = QLabel(self.left_panel)
        self.best_match.setObjectName(u"best_match")
        font2 = QFont()
        font2.setPointSize(10)
        font2.setBold(True)
        self.best_match.setFont(font2)

        self.verticalLayout_4.addWidget(self.best_match)

        self.result_list = QListWidget(self.left_panel)
        self.result_list.setObjectName(u"result_list")
        sizePolicy5 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.result_list.sizePolicy().hasHeightForWidth())
        self.result_list.setSizePolicy(sizePolicy5)

        self.verticalLayout_4.addWidget(self.result_list)


        self.horizontalLayout_3.addWidget(self.left_panel)

        self.line_4 = QFrame(self.bottom_split)
        self.line_4.setObjectName(u"line_4")
        self.line_4.setFrameShape(QFrame.Shape.VLine)
        self.line_4.setFrameShadow(QFrame.Shadow.Sunken)

        self.horizontalLayout_3.addWidget(self.line_4)

        self.right_panel = QWidget(self.bottom_split)
        self.right_panel.setObjectName(u"right_panel")
        self.right_panel.setMaximumSize(QSize(200, 16777215))
        self.verticalLayout_3 = QVBoxLayout(self.right_panel)
        self.verticalLayout_3.setSpacing(8)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(15, 15, 15, 15)
        self.verticalSpacer = QSpacerItem(10, 15, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.verticalLayout_3.addItem(self.verticalSpacer)

        self.icon = QLabel(self.right_panel)
        self.icon.setObjectName(u"icon")
        font3 = QFont()
        font3.setPointSize(12)
        self.icon.setFont(font3)
        self.icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_3.addWidget(self.icon)

        self.title = QLabel(self.right_panel)
        self.title.setObjectName(u"title")
        self.title.setFont(font3)
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_3.addWidget(self.title)

        self.verticalSpacer_2 = QSpacerItem(1, 15, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.verticalLayout_3.addItem(self.verticalSpacer_2)

        self.open_file = QPushButton(self.right_panel)
        self.open_file.setObjectName(u"open_file")
        self.open_file.setFlat(True)

        self.verticalLayout_3.addWidget(self.open_file)

        self.open_file_location = QPushButton(self.right_panel)
        self.open_file_location.setObjectName(u"open_file_location")
        self.open_file_location.setFlat(True)

        self.verticalLayout_3.addWidget(self.open_file_location)

        self.line_3 = QFrame(self.right_panel)
        self.line_3.setObjectName(u"line_3")
        self.line_3.setFrameShape(QFrame.Shape.HLine)
        self.line_3.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_3.addWidget(self.line_3)

        self.metadata = QWidget(self.right_panel)
        self.metadata.setObjectName(u"metadata")
        self.gridLayout = QGridLayout(self.metadata)
        self.gridLayout.setObjectName(u"gridLayout")
        self.size = QLabel(self.metadata)
        self.size.setObjectName(u"size")

        self.gridLayout.addWidget(self.size, 2, 0, 1, 1)

        self.location = QLabel(self.metadata)
        self.location.setObjectName(u"location")

        self.gridLayout.addWidget(self.location, 0, 0, 1, 1)

        self.location_value = QLabel(self.metadata)
        self.location_value.setObjectName(u"location_value")

        self.gridLayout.addWidget(self.location_value, 0, 1, 1, 1)

        self.size_value = QLabel(self.metadata)
        self.size_value.setObjectName(u"size_value")

        self.gridLayout.addWidget(self.size_value, 2, 1, 1, 1)

        self.date_modified = QLabel(self.metadata)
        self.date_modified.setObjectName(u"date_modified")

        self.gridLayout.addWidget(self.date_modified, 1, 0, 1, 1)

        self.date_modified_value = QLabel(self.metadata)
        self.date_modified_value.setObjectName(u"date_modified_value")

        self.gridLayout.addWidget(self.date_modified_value, 1, 1, 1, 1)


        self.verticalLayout_3.addWidget(self.metadata)


        self.horizontalLayout_3.addWidget(self.right_panel)


        self.verticalLayout_2.addWidget(self.bottom_split)


        self.verticalLayout.addWidget(self.quick_search_frame)


        self.retranslateUi(quick_search)

        QMetaObject.connectSlotsByName(quick_search)
    # setupUi

    def retranslateUi(self, quick_search):
        quick_search.setWindowTitle(QCoreApplication.translate("quick_search", u"Quick Search", None))
        self.search_icon.setText(QCoreApplication.translate("quick_search", u"Icon", None))
        self.search_bar_2.setPlaceholderText(QCoreApplication.translate("quick_search", u"Search", None))
#if QT_CONFIG(tooltip)
        self.exit_program.setToolTip(QCoreApplication.translate("quick_search", u"Close Search", None))
#endif // QT_CONFIG(tooltip)
        self.exit_program.setText(QCoreApplication.translate("quick_search", u"X", None))
        self.All.setText(QCoreApplication.translate("quick_search", u"All", None))
        self.Apps.setText(QCoreApplication.translate("quick_search", u"Apps", None))
        self.pdfs.setText(QCoreApplication.translate("quick_search", u"PDFs", None))
        self.docs.setText(QCoreApplication.translate("quick_search", u"DOCs", None))
        self.Images.setText(QCoreApplication.translate("quick_search", u"Images", None))
        self.Folders.setText(QCoreApplication.translate("quick_search", u"Folders", None))
        self.best_match.setText(QCoreApplication.translate("quick_search", u"Best Match", None))
        self.icon.setText(QCoreApplication.translate("quick_search", u"App Icon here", None))
        self.title.setText(QCoreApplication.translate("quick_search", u"Application name here", None))
        self.open_file.setText(QCoreApplication.translate("quick_search", u"Open ", None))
        self.open_file_location.setText(QCoreApplication.translate("quick_search", u"Open File Location", None))
        self.size.setText(QCoreApplication.translate("quick_search", u"Size", None))
        self.location.setText(QCoreApplication.translate("quick_search", u"Location", None))
        self.location_value.setText(QCoreApplication.translate("quick_search", u"Location pops up here", None))
        self.size_value.setText(QCoreApplication.translate("quick_search", u"size shown here", None))
        self.date_modified.setText(QCoreApplication.translate("quick_search", u"Date Modified", None))
        self.date_modified_value.setText(QCoreApplication.translate("quick_search", u"Date goes here", None))
    # retranslateUi

