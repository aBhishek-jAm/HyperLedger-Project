from flask import Flask, render_template, request, redirect
import requests
import qrcode
from io import BytesIO
import base64
import os

app = Flask(__name__)

# Configuration
ACA_URL = "http://localhost:8024"   # College Agent URL

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/connections")
def connections():
    try:
        res = requests.get(f"{ACA_URL}/connections")
        return render_template("connections.html", connections=res.json()['results'])
    except requests.exceptions.RequestException as e:
        return f"Error connecting to Agent: {e}", 500

@app.route("/create-invitation")
def create_invitation():
    # 1. Create the invitation via the Agent
    res = requests.post(f"{ACA_URL}/connections/create-invitation", json={}).json()

    # 2. Convert invitation URL to QR Code (Base64 encoded)
    # This method is preferred over saving to disk (static/qr.png) to avoid concurrency issues.
    qr = qrcode.make(res["invitation_url"])
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    qr_b64 = base64.b64encode(buffer.getvalue()).decode()

    # 3. Pass the full response and the QR image string to the template
    return render_template("scan.html", invitation=res, qr_b64=qr_b64, invitation_url=res["invitation_url"])

@app.route("/issue", methods=["GET", "POST"])
def issue():
    if request.method == "POST":
        data = request.form
        connection_id = data["connection_id"]

        cred_data = {
            "connection_id": connection_id,
            "comment": "Issuing student ID",
            "credential_preview": {
                "@type": "issue-credential/1.0/credential-preview",
                "attributes": [
                    {"name": "name", "value": data["name"]},
                    {"name": "usn", "value": data["usn"]},
                    {"name": "branch", "value": data["branch"]},
                    {"name": "year", "value": data["year"]}
                ]
            },
            "cred_def_id": data.get("cred_def_id") # Ensure this field exists in your HTML form
        }

        requests.post(f"{ACA_URL}/issue-credential/send", json=cred_data)
        return redirect("/")

    # Load connections for the dropdown
    conns = requests.get(f"{ACA_URL}/connections").json()["results"]
    return render_template("issue.html", connections=conns)

if __name__ == "__main__":
    app.run(port=5001, debug=True)