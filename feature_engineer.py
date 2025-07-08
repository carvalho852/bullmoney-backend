
import pandas as pd
import numpy as np
import sqlite3

class FeatureEngineer:
    def __init__(self, db_name=\'trading_data.db\'):
        self.conn = sqlite3.connect(db_name)

    def load_candles(self, asset=\'EURUSD-OTC\'):
        query = f\'SELECT * FROM candles WHERE asset = \'{asset}\' ORDER BY timestamp ASC\' 
        df = pd.read_sql_query(query, self.conn)
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit=\'s\')
        df = df.set_index("timestamp")
        return df

    def calculate_ema(self, df, column=\'close\', periods=[5, 10, 20]):
        for period in periods:
            df[f\'EMA_{period}\'] = df[column].ewm(span=period, adjust=False).mean()
        return df

    def calculate_rsi(self, df, column=\'close\', period=14):
        delta = df[column].diff()
        gain = (delta.where(delta > 0, 0)).ewm(span=period, adjust=False).mean()
        loss = (-delta.where(delta < 0, 0)).ewm(span=period, adjust=False).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        df[f\'RSI_{period}\'] = rsi
        return df

    def calculate_macd(self, df, column=\'close\', fast_period=12, slow_period=26, signal_period=9):
        exp1 = df[column].ewm(span=fast_period, adjust=False).mean()
        exp2 = df[column].ewm(span=slow_period, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=signal_period, adjust=False).mean()
        df[\'MACD\'] = macd
        df[\'MACD_Signal\'] = signal
        df[\'MACD_Hist\'] = macd - signal
        return df

    def calculate_bollinger_bands(self, df, column=\'close\', period=20, num_std_dev=2):
        df[\'BB_Middle\'] = df[column].rolling(window=period).mean()
        df[\'BB_Upper\'] = df[\'BB_Middle\'] + (df[column].rolling(window=period).std() * num_std_dev)
        df[\'BB_Lower\'] = df[\'BB_Middle\'] - (df[column].rolling(window=period).std() * num_std_dev)
        return df

    def calculate_atr(self, df, period=14):
        high_low = df[\'high\'] - df[\'low\']
        high_close = np.abs(df[\'high\'] - df[\'close\'].shift())
        low_close = np.abs(df[\'low\'] - df[\'close\'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.ewm(span=period, adjust=False).mean()
        df[f\'ATR_{period}\'] = atr
        return df

    def add_target_variable(self, df, future_candles=1):
        # Shift the \'close\' price to get the future closing price
        df[\'future_close\'] = df[\'close\'].shift(-future_candles)
        # Define target: 1 for 'call' (price goes up), 0 for 'put' (price goes down)
        df[\'target\'] = (df[\'future_close\'] > df[\'close\']).astype(int)
        return df

    def process_data(self, asset=\'EURUSD-OTC\'):
        df = self.load_candles(asset)
        if df.empty:
            print("Nenhum dado de vela encontrado para processamento.")
            return pd.DataFrame()

        df = self.calculate_ema(df)
        df = self.calculate_rsi(df)
        df = self.calculate_macd(df)
        df = self.calculate_bollinger_bands(df)
        df = self.calculate_atr(df)
        df = self.add_target_variable(df)

        # Remove rows with NaN values created by indicator calculations
        df = df.dropna()
        return df

    def close(self):
        self.conn.close()

# Exemplo de uso (para testes internos)
if __name__ == \'__main__\':
    fe = FeatureEngineer()
    processed_df = fe.process_data()
    if not processed_df.empty:
        print(processed_df.head())
        print(processed_df.columns)
    fe.close()


