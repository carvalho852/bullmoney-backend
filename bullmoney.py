from iqoptionapi.stable_api import IQ_Option
import threading
import time
import numpy as np

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

        thread = threading.Thread(target=self.monitorar)
        thread.start()

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

    def monitorar(self):
        while not self.parar:
            if not self.api.check_connect():
                print("[⚠️] Reconectando...")
                self.api.connect()
                continue

            velas = self.api.get_candles(self.ativo, 60, 15, time.time())
            direcao = self.estrategia_avancada(velas)

            if direcao:
                print(f"[📊] Sinal detectado: {direcao.upper()} em {self.ativo}")
                valor = self.valor_entrada
                for i in range(self.max_gale + 1):
                    status, id = self.api.buy(valor, self.ativo, direcao, 1)
                    if status:
                        resultado = self.api.check_win_v3(id)
                        if resultado > 0:
                            self.lucro_total += resultado
                            self.vitorias += 1
                            self.ultima_ordem = f"Vitória: +{resultado}"
                            print(f"[✅] Vitória: +{resultado}")
                            break
                        else:
                            self.lucro_total += resultado
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

    def status(self):
        return {
            "lucro_total": round(self.lucro_total, 2),
            "vitorias": self.vitorias,
            "derrotas": self.derrotas,
            "ultima_ordem": self.ultima_ordem
        }
