import sqlite3


class DatabaseClient:
    _connection: sqlite3.Connection

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection
        
    
    
    def execute(self, sql: str, parameters = None) -> list:
        if not parameters:
            return self._connection.execute(sql).fetchall()
        
        return self._connection.execute(sql, parameters).fetchall()
    