from flask import Flask, render_template, request, redirect
import requests
import qrcode
from io import BytesIO
import base64
import json

app = Flask(__name__)

# Configuration
VERIFIER_URL = "http://localhost:8023"

@app.route("/")
def index():
    return render_template("index.html")

# --- FLOW 1: Verification via Existing Connection ---
@app.route("/verify", methods=["GET", "POST"])
def verify():
    if request.method == "POST":
        connection_id = request.form["connection_id"]

        # Define what data we want to verify (e.g., USN)
        proof_request = {
            "connection_id": connection_id,
            "proof_request": {
                "name": "Student Credential Check",
                "version": "1.0",
                "requested_attributes": {
                    "attr1_referent": {
                        "name": "usn",
                        "restrictions": []
                    }
                },
                "requested_predicates": {}
            }
        }

        # Send the proof request to the specific connection
        res = requests.post(f"{VERIFIER_URL}/present-proof/send-request", json=proof_request).json()
        
        # Determine the thread/pres_ex_id to track the result
        pres_ex_id = res.get("presentation_exchange_id")
        return render_template("verification_result.html", message="Request Sent", id=pres_ex_id)

    # GET: Fetch existing connections to populate the dropdown
    try:
        cons = requests.get(f"{VERIFIER_URL}/connections").json()
        return render_template("verify.html", connections=cons.get("results", []))
    except requests.exceptions.RequestException as e:
        return f"Error connecting to Verifier Agent: {e}", 500


# --- FLOW 2: Connection-less Verification (QR Code) ---
@app.route("/scan-proof")
def scan_proof():
    # Create a proof request not tied to a connection ID
    req_body = {
        "proof_request": {
            "name": "Proof of Student",
            "version": "1.0",
            "requested_attributes": {
                "attr1_referent": {"name": "usn"}
            },
            "requested_predicates": {}
        }
    }
    
    # Use 'create-request' for connection-less (Out-of-Band) proofs
    res = requests.post(f"{VERIFIER_URL}/present-proof/create-request", json=req_body).json()
    
    # Extract the request dictionary to encode in the QR
    request_dict = res.get("presentation_request_dict") or res
    
    # Generate QR Code in memory (Base64)
    # We dump the dict to a string so the mobile wallet can parse it
    qr = qrcode.make(json.dumps(request_dict)) 
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    qr_b64 = base64.b64encode(buffer.getvalue()).decode()

    return render_template("scan_verify.html", qr_b64=qr_b64, request_data=res)


# --- RESULTS DASHBOARD ---
@app.route("/result")
def result():
    # View all proof presentations (accepted, verified, etc.)
    try:
        proofs = requests.get(f"{VERIFIER_URL}/present-proof/records").json()
        return render_template("result.html", proofs=proofs.get("results", []))
    except Exception as e:
        return f"Error fetching records: {e}"

if __name__ == "__main__":
    app.run(port=5002, debug=True)