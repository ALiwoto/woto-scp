import sqlite3


class DatabaseClient:
    _connection: sqlite3.Connection

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection
        
    
    
    def execute(self, sql: str, parameters = None) -> sqlite3.Cursor:
        if not parameters:
            return self._connection.execute(sql)
        
        return self._connection.execute(sql, parameters)
    