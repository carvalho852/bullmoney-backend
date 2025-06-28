from flask import Flask, request, jsonify
from flask_cors import CORS
from bullmoney import BotIQ

app = Flask(__name__)
CORS(app)

bot = BotIQ()

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    senha = data.get("senha")
    real = data.get("real", False)
    sucesso = bot.login(email, senha, real)

    if sucesso:
        return jsonify({"status": "conectado"})
    return jsonify({"status": "erro"}), 401

@app.route("/start", methods=["POST"])
def start():
    data = request.get_json()
    bot.iniciar(
        valor_entrada=data.get("valor", 2),
        meta=data.get("meta", 10),
        stop=data.get("derrotas", 3),
        max_gale=data.get("max_mg", 1),
        martingale=data.get("martingale", False)
    )
    return jsonify({"status": "iniciado"})

@app.route("/stop", methods=["POST"])
def stop():
    bot.parar_bot()
    return jsonify({"status": "parado"})

@app.route("/status", methods=["GET"])
def status():
    st = bot.status()
    return jsonify({
        "lucro": st.get("lucro", 0),              # ✅ Corrigido aqui
        "vitorias": st.get("vitorias", 0),
        "derrotas": st.get("derrotas", 0),
        "ultima_ordem": st.get("ultima_ordem", "")
    })

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
