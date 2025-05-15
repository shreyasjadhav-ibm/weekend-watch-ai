from flask import Flask, jsonify
import time

app = Flask(__name__)

LOG_FILE = "../logs/application.log"

def read_logs():
    with open(LOG_FILE, "r") as f:
        return f.readlines()

@app.route("/api/logs")
def get_logs():
    return jsonify(read_logs())

if __name__ == "__main__":
    app.run(port=5000)


    