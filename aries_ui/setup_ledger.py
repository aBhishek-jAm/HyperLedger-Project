import requests
import json
import random
import time

# College Agent URL
AGENT_URL = "http://localhost:8024"

def register_schema_and_creddef():
    print("🚀 Registering Schema and Cred Def on Ledger...")

    # 1. GENERATE UNIQUE SCHEMA NAME
    # This prevents "Already Exists" errors if you restart the agent but not the ledger
    random_id = random.randint(1000, 9999)
    schema_name = f"skit_student_id_{random_id}"
    
    schema_payload = {
        "schema_name": schema_name,
        "schema_version": "1.0",
        "attributes": ["name", "usn", "branch", "year"]
    }
    
    print(f"🔹 Creating Schema: {schema_name}...")
    response = requests.post(f"{AGENT_URL}/schemas", json=schema_payload)
    
    if response.status_code != 200:
        print(f"❌ Schema Error ({response.status_code}): {response.text}")
        return
    
    schema_id = response.json()["schema_id"]
    print(f"✅ Schema ID: {schema_id}")

    # 2. CREATE CREDENTIAL DEFINITION
    # We loop briefly to ensure the schema is written before we use it
    time.sleep(2) 
    
    cred_def_payload = {
        "schema_id": schema_id,
        "tag": "default"
    }
    
    print(f"🔹 Creating Credential Definition...")
    response = requests.post(f"{AGENT_URL}/credential-definitions", json=cred_def_payload)
    
    if response.status_code != 200:
        print(f"❌ CredDef Error ({response.status_code}): {response.text}")
        return

    cred_def_id = response.json()["credential_definition_id"]
    print(f"✅ Cred Def ID: {cred_def_id}")

    print("\n--- ⚠️ COPY THESE NEW IDs INTO app.py ⚠️ ---")
    print(f'SCHEMA_ID = "{schema_id}"')
    print(f'CRED_DEF_ID = "{cred_def_id}"')

if __name__ == "__main__":
    register_schema_and_creddef()