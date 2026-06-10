from flask import Flask, request, jsonify

app = Flask(__name__)


@app.route("/ping")
def ping():
    return {"status": "ok"}


@app.route("/command", methods=["POST"])
def command():
    data = request.json
    return jsonify({"received": data})


def start_server():
    app.run(port=5000)