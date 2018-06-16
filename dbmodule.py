from PyQt5.QtSql import QSqlDatabase, QSqlQuery

class dbModule(object):

    db = QSqlDatabase.addDatabase('QSQLITE')
    db.setDatabaseName('./db.sqlite')
    db.open()

    def __init__(self):
        query = QSqlQuery()

        result = query.exec('SELECT * FROM SONG;')
        if result:
            idCol = query.record().indexOf('Title')
            while query.next():
                print(query.value(idCol))
            pass
        pass

if __name__ == "__main__":
    db2 = dbModule()

