from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtSql import *
from PyQt5.QtWidgets import *
from PyQt5.QtMultimedia import *
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

        self.model.dataChanged.connect(self.dataUpdated)

        # set player and control icon
        self.ui.play_pause.setIcon(qta.icon('fa.play'))
        self.ui.next.setIcon(qta.icon('fa.step-forward'))
        self.ui.prev.setIcon(qta.icon('fa.step-backward'))

        self.ui.play_pause.clicked.connect(self.toggleMusic)
        self.ui.next.clicked.connect(lambda: self.player.setPosition(self.player.position() + 10000))
        self.ui.prev.clicked.connect(lambda: self.player.setPosition(self.player.position() - 10000))

        self.pushed.connect(self.ui.slider.setValue)

        self.player = QMediaPlayer(self)

        self.player.durationChanged.connect(lambda: self.ui.slider.setRange(0, self.player.duration()))
        self.player.positionChanged.connect(self.slider.setSliderPosition)
        self.player.positionChanged.connect(self.updateTimeText)
        self.player.currentMediaChanged.connect(self.songChanged)
        self.player.stateChanged.connect(self.togglePlayPauseIcon)

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
        self.ui.searchtext.clear()
        self.fuzzySearch()

    def rowClicked(self, x):
        table = self.ui.targetSelect.currentText()
        if table == 'Song':
            row = x.row()
            qry = QSqlQuery(
                    "SELECT filepath FROM Song WHERE SONG_ID = {0};".format(self.model.record(row).value(0))
                    )

            qry.next()
            self.player.setMedia(QMediaContent(QUrl.fromLocalFile(qry.value(0))))

    def dataUpdated(self, index):
        table = self.ui.targetSelect.currentText()
        column = self.model.record(index.row()).fieldName(index.column())
        value = self.model.record(index.row()).value(index.column())
        pk = self.model.record(index.row()).fieldName(0)
        ID = self.model.record(index.row()).value(0)
        qry = QSqlQuery(
                "UPDATE {0} SET {1} = '{2}' WHERE {3} = '{4}'".format(table, column, value, pk, ID)
                )
        self.model.clear()
        self.fuzzySearch()

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

    def songChanged(self, media):
        # filepath = self.player.media().canonicalUrl().path()
        filepath = media.canonicalUrl().path()

        tag = FLAC(filepath)
        for pic in tag.pictures:
            pix = QPixmap()
            pix.loadFromData(pic.data)
            self.ui.albumart.setPixmap(pix.scaled(100, 100, Qt.KeepAspectRatio))
            self.ui.statusbar.showMessage('Now playing: ' + tag['title'][0] + ' by ' + tag['artist'][0])

        self.player.play()

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
                if table == 'Album':
                    qry = QSqlQuery(
                            "DELETE from Song WHERE ALBUM_ID = '{0}'".format(ID)
                            )

                self.fuzzySearch()

    def mouseReleaseEvent(self, e):
        x = e.pos().x() - self.ui.albumart.pos().x()
        y = e.pos().y() - self.ui.albumart.pos().y()

        if (x > 0 and x < 100) and (y > 0 and y < 100):
            w = QMainWindow(self)
            w.setGeometry(0, 0, 512, 512)
            w.setWindowTitle('Albumart')
            l = QLabel(w)
            l.setGeometry(0, 0, 512, 512)

            filepath = self.player.media().canonicalUrl().path()
            tag = FLAC(filepath)
            for pic in tag.pictures:
                pix = QPixmap()
                pix.loadFromData(pic.data)
                l.setPixmap(pix.scaled(l.width(), l.height(), Qt.KeepAspectRatio));

            w.show()


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

        self.fuzzySearch()


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

        if searchTarget == 'Song':
            query = QSqlQuery("SELECT COUNT(SONG_ID) from Song where {1} LIKE '%{2}%';".format(searchTarget, searchColumn, searchText))
            query.next()
            song_cnt = query.value(0)

            query = QSqlQuery("SELECT SUM(length) from Song where {1} LIKE '%{2}%';".format(searchTarget, searchColumn, searchText))
            query.next()
            total_time = query.value(0)

            query = QSqlQuery("SELECT MIN(length) from Song where {1} LIKE '%{2}%';".format(searchTarget, searchColumn, searchText))
            query.next()
            min_time = query.value(0)

            query = QSqlQuery("SELECT MAX(length) from Song where {1} LIKE '%{2}%';".format(searchTarget, searchColumn, searchText))
            query.next()
            max_time = query.value(0)

            query = QSqlQuery("SELECT COUNT(SONG_ID) from Song where {1} LIKE '%{2}%' GROUP BY ALBUM_ID HAVING COUNT(SONG_ID) > 5;".format(searchTarget, searchColumn, searchText))

            big_album = 0;
            while query.next():
                big_album += 1

            print(song_cnt, total_time, min_time, max_time, big_album)
            self.ui.statusbar.showMessage('{0} songs, total {1}sec, min {2}sec, max {3}sec, {4} large albums'.format(song_cnt, total_time, min_time, max_time, big_album))


    def userQuery(self):
        sql_cmd = self.ui.querycmd.text()
        query = QSqlQuery(sql_cmd)
        self.model.setQuery(query)
        self.model.select()

        if query.lastError().isValid():
            self.ui.statusbar.showMessage(query.lastError().driverText() + ', ' + query.lastError().databaseText())

        self.ui.tableView.setModel(self.model)

