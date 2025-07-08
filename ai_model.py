
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib
from feature_engineer import FeatureEngineer

class AIModel:
    def __init__(self, db_name=\'trading_data.db\'):
        self.feature_engineer = FeatureEngineer(db_name)
        self.model = None

    def train_model(self, asset=\'EURUSD-OTC\'):
        df = self.feature_engineer.process_data(asset)
        if df.empty:
            print("Não há dados suficientes para treinar o modelo.")
            return

        # Features (X) and Target (y)
        # Excluir colunas que não são features ou são o target
        features = [col for col in df.columns if col not in [\'open\', \'close\', \'high\', \'low\', \'volume\', \'asset\', \'future_close\', \'target\']]
        X = df[features]
        y = df[\'target\

        # Dividir dados em treino e teste
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Treinar o modelo RandomForestClassifier
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.model.fit(X_train, y_train)

        # Avaliar o modelo
        y_pred = self.model.predict(X_test)
        print("Acurácia do modelo:", accuracy_score(y_test, y_pred))
        print("\nRelatório de Classificação:\n", classification_report(y_test, y_pred))

        # Salvar o modelo treinado
        joblib.dump(self.model, \'trading_model.pkl\')
        print("Modelo treinado e salvo como trading_model.pkl")

    def predict(self, data):
        if self.model is None:
            try:
                self.model = joblib.load(\'trading_model.pkl\')
            except FileNotFoundError:
                print("Modelo não encontrado. Treine o modelo primeiro.")
                return None
        
        # Garantir que os dados de entrada tenham as mesmas features usadas no treinamento
        # Isso é um placeholder. Em um cenário real, \'data\' seria um DataFrame com as features calculadas
        # e as colunas seriam alinhadas com as features usadas no treinamento.
        # Por simplicidade, vamos assumir que \'data\' já é um DataFrame com as colunas corretas.
        # features = [col for col in data.columns if col not in [\'open\', \'close\', \'high\', \'low\', \'volume\', \'asset\', \'future_close\', \'target\']]
        # return self.model.predict(data[features])
        return self.model.predict(data)

    def close(self):
        self.feature_engineer.close()

# Exemplo de uso (para testes internos)
if __name__ == \'__main__\':
    # Para testar, você precisaria ter alguns dados no seu trading_data.db
    # Execute o bullmoney.py por um tempo para coletar dados.
    ai_model = AIModel()
    ai_model.train_model()
    ai_model.close()


