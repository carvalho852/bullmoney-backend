from flask import Flask, request, jsonify
from flask_cors import CORS
from bullmoney import BotIQ  # seu bot operacional

app = Flask(__name__)
CORS(app)

bot = BotIQ()

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if bot.login(data.get("email"), data.get("senha"), data.get("real", False)):
        return jsonify({"status": "conectado"})
    return jsonify({"status": "erro"}), 401

@app.route("/start", methods=["POST"])
def start():
    d = request.get_json()
    # Forçando EURUSD-OTC (se quiser fixo)
    bot.iniciar(
        valor_entrada=d.get("valor", 2),
        meta=d.get("meta", 10),
        stop=d.get("derrotas", 3),
        max_gale=d.get("max_mg", 1),
        martingale=d.get("martingale", False)
    )
    return jsonify({"status": "iniciado"})

@app.route("/stop", methods=["POST"])
def stop():
    bot.parar_bot()
    return jsonify({"status": "parado"})

@app.route("/status", methods=["GET"])
def status():
    return jsonify(bot.status())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
