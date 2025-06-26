from flask import Flask, request, jsonify
from flask_cors import CORS
from bullmoney import BotIQ
import os

app = Flask(__name__)
CORS(app)
bot = BotIQ()

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if bot.login(data["email"], data["senha"], data.get("real", False)):
        return jsonify({"status": "conectado"})
    return jsonify({"status": "erro"}), 401

@app.route("/start", methods=["POST"])
def start():
    d = request.get_json()
    bot.iniciar(
        d["valor"],
        d.get("meta", 0),
        d.get("derrotas", 0),
        d.get("max_mg", 0),
        d.get("martingale", False)
    )
    return jsonify({"status": "iniciado"})

@app.route("/stop", methods=["POST"])
def stop():
    bot.parar_bot()
    return jsonify({"status": "parado"})

@app.route("/status", methods=["GET"])
def status():
    return jsonify(bot.status())

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

