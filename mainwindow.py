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

    model = None

    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi('mainwindow.ui', self)

        self.ui.pushButton.clicked.connect(self.slotTest)
        self.ui.tableView.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # self.ui.tableView.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.ui.tableView.clicked.connect(self.rowClicked)
        self.ui.exist.clicked.connect(self.albumHasSong)
        self.ui.notExist.clicked.connect(self.albumHasNoSong)

        # db buttons
        self.ui.button_search.clicked.connect(self.userSearch)
        self.ui.fuzzy.clicked.connect(self.fuzzySearch)
        self.ui.button_query.clicked.connect(self.userQuery)

        self.model = QSqlTableModel(self, self.db)

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

        # self.player.setMedia(QMediaContent(QUrl.fromLocalFile('/home/hmkrl/Music/南條愛乃 - サントロワ∴/10. 光のはじまり.flac')))
        self.slider.sliderMoved.connect(self.player.setPosition)

        # enable mainwindow drag and drop
        self.setAcceptDrops(True)

        # set targetSelect combobox
        self.ui.targetSelect.currentTextChanged.connect(self.updateColumnSelect)

        tables = self.db.tables()
        tables.remove('sqlite_sequence')
        self.ui.targetSelect.addItems(tables)

# Slots

    def slotTest(self):
        # model.setTable("Artist")
        # model.setQuery(QSqlQuery("SELECT MAX(Since) from Artist;"))
        qry = QSqlQuery()
        qry.exec("SELECT * from Artist where Name LIKE '%%';")
        # while qry.next():
            # print(qry.value(qry.record().indexOf("Name")))
        # qry.finish()

        # self.ui.tableView.show()
        # select = QFileDialog(self)
        # select.show()
        # select.filesSelected.connect(lambda str: (
            # self.player.setMedia(QMediaContent(QUrl.fromLocalFile(str[0]))),
            # self.player.play()))


    def updateColumnSelect(self, table):
        record = self.db.driver().record(table)
        self.ui.columnSelect.clear()
        self.ui.columnSelect.addItems([record.fieldName(i) for i in range (record.count())])

    def rowClicked(self, x):
        row = x.row()
        print(self.model.record(row).value(0))


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
        player.play()
        mutag = FLAC(filepath)
        for pic in mutag.pictures:
            pix = QPixmap()
            pix.loadFromData(pic.data)
            self.ui.albumart.setPixmap(pix.scaled(self.ui.albumart.size()))

    def albumHasSong(self):
        query = QSqlQuery('SELECT * FROM Album WHERE EXISTS(SELECT * FROM Song WHERE Song.ALBUM_ID = Album.ALBUM_ID);')
        self.model.setQuery(query)
        self.model.select()
        self.ui.tableView.setModel(self.model)

    def albumHasNoSong(self):
        query = QSqlQuery('SELECT * FROM Album WHERE NOT EXISTS(SELECT * FROM Song WHERE Song.ALBUM_ID = Album.ALBUM_ID);')
        self.model.setQuery(query)
        self.model.select()
        self.ui.tableView.setModel(self.model)


# Event handler

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Delete:
            for index in self.ui.tableView.selectedIndexes():
                ID = self.model.record(index.row()).value(0)
                table = self.ui.targetSelect.currentText()
                pk = self.db.driver().record(table).fieldName(0)
                qry = QSqlQuery(
                        "DELETE from {0} WHERE {1} = '{2}'".format(table, pk, ID)
                        )
                self.fuzzySearch()



# MainWindow drag & drop

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):
        for url in e.mimeData().urls():
            tag = FLAC(url.path())

            # insert Album if not exist
            qry = QSqlQuery(
                    "SELECT ALBUM_ID from Album "
                    "WHERE Title = '{0}'".format(tag['album'][0])
                    )

            size = 0    # qry.size not supported by SQLite
            while qry.next():
                size += 1

            if size == 0:
                qry = QSqlQuery(
                        "INSERT INTO ALBUM (Title, Year, ARTIST_ID) "
                        "VALUES ('{0}', {1}, (SELECT ARTIST_ID FROM Artist WHERE Name = '{2}'))".format(tag['album'][0], int(tag['date'][0]), tag['artist'][0])
                        )

            # Add song
            qry = QSqlQuery(
                    "SELECT SONG_ID FROM Song "
                    "WHERE filepath = '{0}'".format(url.path())
                    )

            size = 0    # qry.size not supported by SQLite
            while qry.next():
                size += 1

            if size == 0:
                qry = QSqlQuery(
                        "INSERT INTO Song (Title, ALBUM_ID, ARTIST_ID, Length, filepath) "
                        "VALUES ('{0}', (SELECT ALBUM_ID FROM Album WHERE Title = '{1}'), (SELECT ARTIST_ID FROM Artist WHERE Name = '{2}'), {3}, '{4}')".format(tag['title'][0], tag['album'][0], tag['artist'][0], int(tag.info.length), url.path())
                        )



# database operations

    def userSearch(self):
        searchTarget = self.ui.targetSelect.currentText()
        searchColumn = self.ui.columnSelect.currentText()
        searchText = self.ui.searchtext.text().split()

        in_cmd = 'IN'
        if self.ui.isReverse.isChecked():
            in_cmd = 'NOT IN'

        query = QSqlQuery("SELECT * from {0} where {1} {2} ('{3}');".format(searchTarget, searchColumn, in_cmd, '\',\''.join(searchText)))
        self.model.setQuery(query)
        self.model.select()

        if query.lastError().isValid():
            self.ui.statusbar.showMessage(query.lastError().driverText() + ', ' + query.lastError().databaseText())

        self.ui.tableView.setModel(self.model)

    def fuzzySearch(self):
        searchTarget = self.ui.targetSelect.currentText()
        searchColumn = self.ui.columnSelect.currentText()
        searchText = self.ui.searchtext.text()

        query = QSqlQuery("SELECT * from {0} where {1} LIKE '%{2}%';".format(searchTarget, searchColumn, searchText))
        self.model.setQuery(query)
        self.model.select()

        if query.lastError().isValid():
            self.ui.statusbar.showMessage(query.lastError().driverText() + ', ' + query.lastError().databaseText())

        self.ui.tableView.setModel(self.model)

    def userQuery(self):
        sql_cmd = self.ui.querycmd.text()
        query = QSqlQuery(sql_cmd)
        self.model.setQuery(query)
        self.model.select()

        if query.lastError().isValid():
            self.ui.statusbar.showMessage(query.lastError().driverText() + ', ' + query.lastError().databaseText())

        self.ui.tableView.setModel(self.model)

