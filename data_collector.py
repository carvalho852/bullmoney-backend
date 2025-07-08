
import sqlite3
import pandas as pd

class DataCollector:
    def __init__(self, db_name='trading_data.db'):
        self.conn = sqlite3.connect(db_name)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS candles (
                timestamp INTEGER PRIMARY KEY,
                open REAL,
                close REAL,
                high REAL,
                low REAL,
                volume REAL,
                asset TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER,
                asset TEXT,
                direction TEXT,
                entry_price REAL,
                exit_price REAL,
                amount REAL,
                profit REAL,
                win INTEGER
            )
        ''')
        self.conn.commit()

    def save_candles(self, candles, asset):
        df = pd.DataFrame(candles)
        df['asset'] = asset
        df.to_sql('candles', self.conn, if_exists='append', index=False)

    def save_trade(self, timestamp, asset, direction, entry_price, exit_price, amount, profit, win):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO trades (timestamp, asset, direction, entry_price, exit_price, amount, profit, win)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (timestamp, asset, direction, entry_price, exit_price, amount, profit, win))
        self.conn.commit()

    def close(self):
        self.conn.close()


