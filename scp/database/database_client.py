import sqlite3


class DatabaseClient:
    _connection: sqlite3.Connection

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection
        
    
    
    def execute(self, sql: str, parameters = ...) -> sqlite3.Cursor:
        return self._connection.execute(sql, parameters)
    