from iqoptionapi.stable_api import IQ_Option
import time
import threading
import numpy as np
import datetime

class BotIQ:
    def __init__(self):
        self.api = None
        self.email = ""
        self.senha = ""
        self.conta_real = False
        self.valor_entrada = 2
        self.meta = 10
        self.stop = 3
        self.max_gale = 2
        self.martingale = False
        self.ativo = "EURUSD-OTC"
        self.parar = False
        self.vitorias = 0
        self.derrotas = 0
        self.lucro_total = 0
        self.ultima_ordem = ""

    def login(self, email, senha, real=False):
        self.api = IQ_Option(email, senha)
        conectado, _ = self.api.connect()
        if conectado:
            self.api.change_balance("REAL" if real else "PRACTICE")
            self.email = email
            self.senha = senha
            self.conta_real = real
            return True
        return False

    def estrategia_avancada(self, velas):
        closes = np.array([v['close'] for v in velas])
        ema_5 = np.mean(closes[-5:])
        ema_10 = np.mean(closes[-10:])
        delta = np.diff(closes)
        gain = np.mean([x for x in delta[-14:] if x > 0])
        loss = abs(np.mean([x for x in delta[-14:] if x < 0]))
        rs = gain / loss if loss != 0 else 0.01
        rsi = 100 - (100 / (1 + rs))

        candle = velas[-1]
        anterior = velas[-2]
        volatilidade = max([v['max'] for v in velas[-5:]]) - min([v['min'] for v in velas[-5:]])
        if volatilidade < 0.0005:
            return None

        if ema_5 > ema_10 and rsi < 70 and candle['close'] > candle['open'] and anterior['close'] < anterior['open']:
            return "call"
        elif ema_5 < ema_10 and rsi > 30 and candle['close'] < candle['open'] and anterior['close'] > anterior['open']:
            return "put"
        return None

    def executar_ordem(self, direcao):
        valor = self.valor_entrada
        for gale in range(self.max_gale + 1):
            status, op_id = self.api.buy(valor, self.ativo, direcao, 1)
            if status:
                self.ultima_ordem = f"{direcao.upper()} em {self.ativo} com R${valor:.2f}"
                resultado = self.api.check_win_v3(op_id)
                self.lucro_total += resultado
                if resultado > 0:
                    self.vitorias += 1
                    break
                else:
                    self.derrotas += 1
                    if not self.martingale:
                        break
                    valor *= 2  # Gale clássico
            else:
                break

    def monitorar(self):
        while not self.parar:
            if not self.api.check_connect():
                self.api.connect()
                if self.conta_real:
                    self.api.change_balance("REAL")
                else:
                    self.api.change_balance("PRACTICE")

            if self.lucro_total >= self.meta:
                break
            if self.derrotas >= self.stop:
                break

            velas = self.api.get_candles(self.ativo, 60, 20, time.time())
            if len(velas) < 15:
                time.sleep(2)
                continue

            direcao = self.estrategia_avancada(velas)
            if direcao:
                self.executar_ordem(direcao)

            time.sleep(5)

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
        thread = threading.Thread(target=self.monitorar)
        thread.start()

    def parar_bot(self):
        self.parar = True

    def status(self):
        return {
            "lucro": round(self.lucro_total, 2),
            "vitorias": self.vitorias,
            "derrotas": self.derrotas,
            "ativo": self.ativo,
            "ultima_ordem": self.ultima_ordem
        }
