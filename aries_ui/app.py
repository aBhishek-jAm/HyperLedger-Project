import json
import requests
import time
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "skit_secret_key"

import os

# --- CONFIGURATION ---
STUDENT_AGENT = os.environ.get("STUDENT_AGENT", "http://localhost:8022")
COLLEGE_AGENT = os.environ.get("COLLEGE_AGENT", "http://localhost:8024")
COMPANY_AGENT = os.environ.get("COMPANY_AGENT", "http://localhost:8026")

# ⚠️ ENSURE THESE MATCH YOUR setup_ledger.py OUTPUT ⚠️
SCHEMA_ID = "GHiehWQfcT89c7di62WriQ:2:skit_student_id_6075:1.0"
CRED_DEF_ID = "GHiehWQfcT89c7di62WriQ:3:CL:19:default"

# --- HELPER FUNCTIONS ---
def agent_get(agent_url, endpoint):
    try:
        response = requests.get(f"{agent_url}/{endpoint}")
        return response.json()
    except:
        return {}

def agent_post(agent_url, endpoint, data=None):
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(f"{agent_url}/{endpoint}", json=data, headers=headers)
        try:
            return response.json()
        except:
            return {}
    except Exception as e:
        return {"error": str(e)}

# --- MAIN DASHBOARD ---
@app.route('/')
def dashboard():
    print("\n--- 🔄 DASHBOARD REFRESH ---")

    # 1. GET DATA
    college_conns = agent_get(COLLEGE_AGENT, "connections").get('results', [])
    student_conns = agent_get(STUDENT_AGENT, "connections").get('results', [])
    company_conns = agent_get(COMPANY_AGENT, "connections").get('results', [])

    # 2. AUTOMATION LOGIC
    # Student Auto-Accept
    for conn in student_conns:
        if conn['state'] == 'invitation':
            agent_post(STUDENT_AGENT, f"connections/{conn['connection_id']}/accept-invitation", {})
        elif conn['state'] in ['response', 'response-received']:
            agent_post(STUDENT_AGENT, f"connections/{conn['connection_id']}/send-ping", {"comment": "auto-finalize"})

    # College Auto-Accept
    for conn in college_conns:
        if conn['state'] in ['request', 'request-received']:
            agent_post(COLLEGE_AGENT, f"connections/{conn['connection_id']}/accept-request", {})
            
    # Company Auto-Accept
    for conn in company_conns:
        if conn['state'] in ['request', 'request-received']:
            agent_post(COMPANY_AGENT, f"connections/{conn['connection_id']}/accept-request", {})

    # College Auto-Issue
    college_creds = agent_get(COLLEGE_AGENT, "issue-credential/records").get('results', [])
    for record in college_creds:
        if record['state'] == 'request_received':
            agent_post(COLLEGE_AGENT, f"issue-credential/records/{record['credential_exchange_id']}/issue", {})

    # 3. RE-FETCH DATA
    student_conns = agent_get(STUDENT_AGENT, "connections")
    college_conns = agent_get(COLLEGE_AGENT, "connections")
    company_conns = agent_get(COMPANY_AGENT, "connections")
    
    student_creds = agent_get(STUDENT_AGENT, "credentials")
    student_issue_records = agent_get(STUDENT_AGENT, "issue-credential/records")
    
    college_proofs = agent_get(COLLEGE_AGENT, "present-proof/records")
    company_proofs = agent_get(COMPANY_AGENT, "present-proof/records")
    student_proofs = agent_get(STUDENT_AGENT, "present-proof/records")

    return render_template('dashboard.html', 
                           student_conns=student_conns.get('results', []),
                           college_conns=college_conns.get('results', []),
                           company_conns=company_conns.get('results', []),
                           student_creds=student_creds.get('results', []),
                           student_issue_records=student_issue_records.get('results', []),
                           college_proofs=college_proofs.get('results', []),
                           company_proofs=company_proofs.get('results', []),
                           student_proofs=student_proofs.get('results', []),
                           cred_def_id=CRED_DEF_ID)

# --- ROUTES ---

# 1. CONNECTION ROUTES
@app.route('/create_invite_college', methods=['POST'])
def create_invite_college():
    resp = agent_post(COLLEGE_AGENT, "connections/create-invitation?alias=Student_Connection")
    return render_template('dashboard.html', invitation_json=json.dumps(resp.get('invitation'), indent=2))

@app.route('/create_invite_company', methods=['POST'])
def create_invite_company():
    resp = agent_post(COMPANY_AGENT, "connections/create-invitation?alias=Student_Connection")
    return render_template('dashboard.html', invitation_json=json.dumps(resp.get('invitation'), indent=2))

@app.route('/accept_invite', methods=['POST'])
def accept_invite():
    try:
        invite_json = json.loads(request.form['invite_json'])
        label = invite_json.get('label', 'Unknown')
        alias = "College_Connection" if "College" in label else "Company_Connection"
        agent_post(STUDENT_AGENT, f"connections/receive-invitation?alias={alias}", invite_json)
        flash(f"Invitation Accepted from {label}!")
    except Exception as e:
        flash(f"Error: {e}")
    return redirect(url_for('dashboard'))

# 2. ISSUANCE ROUTES (College Only)
@app.route('/issue_credential', methods=['POST'])
def issue_credential():
    conn_id = request.form['connection_id']
    attributes = [
        {"name": "name", "value": request.form['name']},
        {"name": "usn", "value": request.form['usn']},
        {"name": "branch", "value": request.form['branch']},
        {"name": "year", "value": request.form['year']}
    ]
    payload = {
        "connection_id": conn_id,
        "cred_def_id": CRED_DEF_ID,
        "credential_preview": {"@type": "https://didcomm.org/issue-credential/1.0/credential-preview", "attributes": attributes}
    }
    agent_post(COLLEGE_AGENT, "issue-credential/send-offer", payload)
    return redirect(url_for('dashboard'))

@app.route('/student_action_cred/<action>/<cred_ex_id>', methods=['POST'])
def student_action_cred(action, cred_ex_id):
    agent_post(STUDENT_AGENT, f"issue-credential/records/{cred_ex_id}/{action}", {})
    return redirect(url_for('dashboard'))

# 3. PROOF ROUTES (College OR Company)
@app.route('/request_proof', methods=['POST'])
def request_proof():
    conn_id = request.form['connection_id']
    # This tells us WHO is asking for the proof
    verifier_agent = request.form['verifier_agent'] # 'college' or 'company'
    
    url = COLLEGE_AGENT if verifier_agent == 'college' else COMPANY_AGENT
    
    payload = {
        "connection_id": conn_id,
        "proof_request": {
            "name": "Verify Student ID",
            "version": "1.0",
            "requested_attributes": {
                "0_name_uuid": {
                    "name": "name",
                    "restrictions": [{"cred_def_id": CRED_DEF_ID}]
                }
            },
            "requested_predicates": {}
        }
    }
    print(f"Requesting proof from {verifier_agent} at {url}")
    agent_post(url, "present-proof/send-request", payload)
    return redirect(url_for('dashboard'))

@app.route('/send_proof/<pres_ex_id>/<cred_id>', methods=['POST'])
def send_proof(pres_ex_id, cred_id):
    payload = {
        "requested_attributes": {"0_name_uuid": {"cred_id": cred_id, "revealed": True}},
        "requested_predicates": {},
        "self_attested_attributes": {},
    }
    agent_post(STUDENT_AGENT, f"present-proof/records/{pres_ex_id}/send-presentation", payload)
    return redirect(url_for('dashboard'))

@app.route('/verify_proof/<pres_ex_id>/<agent_type>', methods=['POST'])
def verify_proof(pres_ex_id, agent_type):
    # Logic to select the correct agent based on who is clicking "Verify"
    url = COLLEGE_AGENT if agent_type == 'college' else COMPANY_AGENT
    
    print(f"Verifying proof on {agent_type} agent ({url})...")
    resp = agent_post(url, f"present-proof/records/{pres_ex_id}/verify-presentation", {})
    
    # Debug print to see what happened
    print(f"Verification Response: {resp}")
    
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    print("🚀 Starting Flask UI on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
