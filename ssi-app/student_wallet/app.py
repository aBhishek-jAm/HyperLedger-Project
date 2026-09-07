from flask import Flask, render_template
import requests

app = Flask(__name__)
WALLET_AGENT = "http://localhost:8022"

@app.route("/")
def home():
    creds = requests.get(f"{WALLET_AGENT}/credentials").json()
    return render_template("index.html", credentials=creds["results"])

if __name__ == "__main__":
    app.run(port=5003, debug=True)
