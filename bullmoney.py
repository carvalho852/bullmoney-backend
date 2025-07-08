from iqoptionapi.stable_api import IQ_Option
import threading
import time
import numpy as np
from data_collector import DataCollector
from feature_engineer import FeatureEngineer
from ai_model import AIModel
import pandas as pd
import os
import json

class BotIQ:
    def __init__(self):
        self.api = None
        self.email = None
        self.senha = None
        self.conta_real = False
        self.valor_entrada = 0
        self.meta = 0
        self.stop = 0
        self.max_gale = 0
        self.martingale = False
        self.conectado = False
        self.parar = False
        self.lucro_total = 0
        self.vitorias = 0
        self.derrotas = 0
        self.ultima_ordem = ""
        self.ativo = "EURUSD-OTC"
        self.data_collector = DataCollector() # Inicializa o coletor de dados
        self.feature_engineer = FeatureEngineer() # Inicializa o engenheiro de features
        self.ai_model = AIModel() # Inicializa o modelo de IA

    def login(self, email, senha, conta_real):
        self.api = IQ_Option(email, senha)
        self.api.connect()
        if self.api.check_connect():
            self.api.change_balance("REAL" if conta_real else "PRACTICE")
            self.email = email
            self.senha = senha
            self.conta_real = conta_real
            self.conectado = True
            print("[✅] Login realizado com sucesso.")
            return True
        else:
            print("[❌] Falha ao conectar na IQ Option.")
            return False

    def iniciar(self, valor_entrada, meta, stop, max_gale, martingale):
        self.valor_entrada = float(valor_entrada)
        self.meta = float(meta)
        self.stop = int(stop)
        self.max_gale = int(max_gale)
        self.martingale = martingale
        self.lucro_total = 0
        self.vitorias = 0
        self.derrotas = 0
        self.parar = False

        # Treinar o modelo de IA antes de iniciar as operações
        print("[🧠] Treinando o modelo de IA... Isso pode levar um tempo.")
        self.ai_model.train_model(asset=self.ativo)
        print("[🧠] Modelo de IA treinado com sucesso!")

        thread = threading.Thread(target=self.monitorar)
        thread.start()

    def estrategia_avancada(self, velas):
        # Converte as velas para um DataFrame pandas
        df_velas = pd.DataFrame(velas)
        df_velas["timestamp"] = pd.to_datetime(df_velas["from"], unit="s") # Usar \'from\' para timestamp da vela
        df_velas = df_velas.set_index("timestamp")

        # Calcula as features usando o FeatureEngineer
        # Apenas as últimas velas são necessárias para prever a próxima
        # Certifique-se de que o DataFrame tem as colunas esperadas pelo FeatureEngineer
        # (open, close, high, low, volume)
        
        # Para evitar problemas com dados insuficientes para o cálculo de indicadores
        # vamos garantir que temos pelo menos o número de velas necessárias para o maior período de indicador (26 para MACD)
        if len(df_velas) < 26:
            return None # Não há velas suficientes para calcular os indicadores

        # Calcula as features para a última vela
        processed_data = self.feature_engineer.calculate_ema(df_velas.copy())
        processed_data = self.feature_engineer.calculate_rsi(processed_data)
        processed_data = self.feature_engineer.calculate_macd(processed_data)
        processed_data = self.feature_engineer.calculate_bollinger_bands(processed_data)
        processed_data = self.feature_engineer.calculate_atr(processed_data)
        
        # Pega a última linha (features da vela mais recente) e remove NaNs
        features_for_prediction = processed_data.iloc[-1].drop([col for col in processed_data.columns if col in ["open", "close", "high", "low", "volume", "asset", "future_close", "target"] or pd.isna(processed_data.iloc[-1][col])])
        
        # Converte para DataFrame com uma única linha para a previsão
        features_for_prediction = pd.DataFrame([features_for_prediction])

        # Faz a previsão usando o modelo de IA
        prediction = self.ai_model.predict(features_for_prediction)

        if prediction is not None:
            if prediction[0] == 1: # 1 para \'call\'
                return "call"
            elif prediction[0] == 0: # 0 para \'put\'
                return "put"
        return None

    def monitorar(self):
        while not self.parar:
            if not self.api.check_connect():
                print("[⚠️] Reconectando...")
                self.api.connect()
                continue

            # Obter mais velas para garantir dados suficientes para features
            velas = self.api.get_candles(self.ativo, 60, 60, time.time()) # Pega 60 velas de 60 segundos
            self.data_collector.save_candles(velas, self.ativo) # Salva as velas

            direcao = self.estrategia_avancada(velas)

            if direcao:
                print(f"[📊] Sinal detectado: {direcao.upper()} em {self.ativo}")
                valor = self.valor_entrada
                for i in range(self.max_gale + 1):
                    status, id = self.api.buy(valor, self.ativo, direcao, 1)
                    if status:
                        resultado = self.api.check_win_v3(id)
                        self.lucro_total += resultado
                        
                        # Coleta de dados da operação
                        timestamp_trade = int(time.time())
                        entry_price = velas[-1][\'close\'] # Preço de entrada pode ser o fechamento da última vela
                        exit_price = entry_price + resultado # Simplificado, precisa ser mais preciso
                        win = 1 if resultado > 0 else 0
                        self.data_collector.save_trade(timestamp_trade, self.ativo, direcao, entry_price, exit_price, valor, resultado, win)

                        if resultado > 0:
                            self.vitorias += 1
                            self.ultima_ordem = f"Vitória: +{resultado}"
                            print(f"[✅] Vitória: +{resultado}")
                            break
                        else:
                            self.derrotas += 1
                            self.ultima_ordem = f"Derrota: {resultado}"
                            print(f"[❌] Derrota: {resultado}")
                            if not self.martingale:
                                break
                            valor *= 2
                    else:
                        print("[⚠️] Ordem não executada.")
                        break

                if self.lucro_total >= self.meta or self.derrotas >= self.stop:
                    print("[🏁] Meta ou Stop atingido. Parando operações.")
                    self.parar = True

            time.sleep(5)

    def parar_bot(self):
        self.parar = True
        self.data_collector.close() # Fecha a conexão com o banco de dados
        self.feature_engineer.close()

    def status(self):
        return {
            "lucro_total": round(self.lucro_total, 2),
            "vitorias": self.vitorias,
            "derrotas": self.derrotas,
            "ultima_ordem": self.ultima_ordem
        }


def save_config(config):
    with open(\'config.json\', \'w\') as f:
        json.dump(config, f, indent=4)

def load_config():
    if os.path.exists(\'config.json\'):
        with open(\'config.json\', \'r\') as f:
            return json.load(f)
    return None

if __name__ == "__main__":
    config = load_config()
    if config:
        email = config[\'email\']
        senha = config[\'senha\']
        conta_real = config[\'conta_real\']
        valor_entrada = config[\'valor_entrada\']
        meta = config[\'meta\']
        stop = config[\'stop\']
        max_gale = config[\'max_gale\']
        martingale = config[\'martingale\']
        print("[⚙️] Configurações carregadas do arquivo config.json.")
    else:
        print("\n[👋] Bem-vindo ao Robô Trader Autônomo com IA!")
        email = input("Digite seu email da IQ Option: ")
        senha = input("Digite sua senha da IQ Option: ")
        conta_real_str = input("Usar conta REAL? (s/n): ").lower()
        conta_real = True if conta_real_str == \'s\' else False
        valor_entrada = float(input("Digite o valor de entrada por operação: "))
        meta = float(input("Digite sua meta de lucro: "))
        stop = int(input("Digite seu stop de derrotas consecutivas: "))
        max_gale = int(input("Digite o número máximo de Martingales: "))
        martingale_str = input("Usar Martingale? (s/n): ").lower()
        martingale = True if martingale_str == \'s\' else False

        save_config({
            \'email\': email,
            \'senha\': senha,
            \'conta_real\': conta_real,
            \'valor_entrada\': valor_entrada,
            \'meta\': meta,
            \'stop\': stop,
            \'max_gale\': max_gale,
            \'martingale\': martingale
        })
        print("[⚙️] Configurações salvas em config.json.")

    bot = BotIQ()
    if bot.login(email, senha, conta_real):
        bot.iniciar(valor_entrada, meta, stop, max_gale, martingale)
        try:
            while True:
                time.sleep(1)
                current_status = bot.status()
                os.system(\'cls\' if os.name == \'nt\' else \'clear\') # Limpa o console
                print(f"[📊] Lucro Total: R$ {current_status[\'lucro_total\']:.2f}")
                print(f"[✅] Vitórias: {current_status[\'vitorias\']}")
                print(f"[❌] Derrotas: {current_status[\'derrotas\']}")
                print(f"[💬] Última Ordem: {current_status[\'ultima_ordem\']}")
                print("\n[🤖] Robô em operação. Pressione Ctrl+C para parar.")
                
        except KeyboardInterrupt:
            print("\n[🛑] Parando o robô...")
            bot.parar_bot()
            print("[✅] Robô parado.")
    else:
        print("[❌] Não foi possível iniciar o robô devido a falha de login.")


