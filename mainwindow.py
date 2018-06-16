from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtSql import *
from PyQt5.QtWidgets import *
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from mutagen.flac import FLAC, Picture

import os
import qtawesome as qta

class MainWindow(QMainWindow):

    step = 0
    ui = None
    player = None
    pushed = pyqtSignal(int)

    db = QSqlDatabase.addDatabase('QSQLITE')
    db.setDatabaseName('./db.sqlite')
    db.open()

    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi('mainwindow.ui', self)

        self.ui.pushButton.clicked.connect(self.slotTest)
        self.ui.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # self.ui.tableView.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.ui.tableView.clicked.connect(lambda x: print(x.row()))

        # db buttons
        self.ui.button_search.clicked.connect(self.userSearch)
        self.ui.button_query.clicked.connect(self.userQuery)

        # set player and control icon
        self.ui.play_pause.setIcon(qta.icon('fa.play'))
        self.ui.next.setIcon(qta.icon('fa.step-forward'))
        self.ui.prev.setIcon(qta.icon('fa.step-backward'))

        self.ui.play_pause.clicked.connect(self.toggleMusic)

        self.pushed.connect(self.ui.slider.setValue)

        self.player = QMediaPlayer(self)

        self.player.durationChanged.connect(lambda: self.ui.slider.setRange(0, self.player.duration()))
        self.player.positionChanged.connect(self.slider.setSliderPosition)
        self.player.positionChanged.connect(self.updateTimeText)
        self.player.currentMediaChanged.connect(self.songChanged)
        self.player.stateChanged.connect(self.togglePlayPauseIcon)

        self.player.setMedia(QMediaContent(QUrl.fromLocalFile('/home/hmkrl/Music/南條愛乃 - サントロワ∴/10. 光のはじまり.flac')))
        self.slider.sliderMoved.connect(self.player.setPosition)

        # enable mainwindow drag and drop
        self.setAcceptDrops(True)

# Event handler
    def keyPressEvent(self, e):
        if e.key() == Qt.Key_A:
            print('A pressed')

# Slots
    def slotTest(self):
        model = QSqlTableModel(self, self.db)
        # model.setTable("Artist")
        # model.setQuery(QSqlQuery("SELECT MAX(Since) from Artist;"))
        qry = QSqlQuery()
        qry.exec("SELECT * from Artist where Name LIKE '%%';")
        # while qry.next():
            # print(qry.value(qry.record().indexOf("Name")))
        # qry.finish()
        model.select()

        self.ui.tableView.setModel(model)
        # self.ui.tableView.show()
        # select = QFileDialog(self)
        # select.show()
        # select.filesSelected.connect(lambda str: (
            # self.player.setMedia(QMediaContent(QUrl.fromLocalFile(str[0]))),
            # self.player.play()))


# Music playing control

    def updateTimeText(self, pos):
        self.ui.play_time.setText('{:0>2}:{:0>2} / {:0>2}:{:0>2}'.format(int(pos/ 1000 / 60), int(pos / 1000 % 60), int(self.player.duration() / 1000 / 60), int(self.player.duration() / 1000 % 60)))

    def toggleMusic(self):
        if self.player.state() == QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def togglePlayPauseIcon(self, state):
        if state == QMediaPlayer.PlayingState:
            self.ui.play_pause.setIcon(qta.icon('fa.pause'))
        else:
            self.ui.play_pause.setIcon(qta.icon('fa.play'))

    def songChanged(self):
        filepath = self.player.media().canonicalUrl().path()
        mutag = FLAC(filepath)
        for pic in mutag.pictures:
            pix = QPixmap()
            pix.loadFromData(pic.data)
            self.ui.albumart.setPixmap(pix.scaled(self.ui.albumart.size()))


# MainWindow drag & drop

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):
        for url in e.mimeData().urls():
            tag = FLAC(url.path())
            print(tag['title'][0], tag['artist'][0])

# database operations

    def userSearch(self):
        model = QSqlTableModel(self, self.db)

        searchTarget = self.ui.targetSelect.currentText()
        searchColumn = self.ui.columnSelect.currentText()
        searchText = self.ui.searchtext.text()

        model.setQuery(QSqlQuery("SELECT * from {0} where {1} LIKE '%{2}%';".format(searchTarget, searchColumn, searchText)))
        model.select()

        self.ui.tableView.setModel(model)

    def userQuery(self):
        model = QSqlTableModel(self, self.db)

        sql_cmd = self.ui.querycmd.text()
        model.setQuery(QSqlQuery(sql_cmd))
        model.select()

        self.ui.tableView.setModel(model)

