import requests
import os
import time

# In full-stack, webserver is at http://webserver:8000
LEDGER_URL = os.getenv("LEDGER_URL", "http://webserver:8000")

SEEDS = [
    {"role": "TRUST_ANCHOR", "seed": "Student0000000000000000000000001", "alias": "Student"},
    {"role": "TRUST_ANCHOR", "seed": "College0000000000000000000000001", "alias": "College"},
    {"role": "TRUST_ANCHOR", "seed": "Company0000000000000000000000001", "alias": "Company"}
]

def register_dids():
    print(f"🚀 Connecting to Ledger at {LEDGER_URL}...")
    
    # Wait for ledger to be ready
    for i in range(10):
        try:
            r = requests.get(f"{LEDGER_URL}/genesis")
            if r.status_code == 200:
                print("✅ Ledger is reachable.")
                break
        except:
            print(f"⏳ Waiting for ledger... ({i+1}/10)")
            time.sleep(2)
    else:
        print("❌ Ledger not reachable. Exiting.")
        return

    for agent in SEEDS:
        print(f"🔹 Registering {agent['alias']}...")
        payload = {"role": agent["role"], "alias": agent["alias"], "seed": agent["seed"]}
        try:
            resp = requests.post(f"{LEDGER_URL}/register", json=payload)
            if resp.status_code == 200:
                data = resp.json()
                print(f"✅ Registered {agent['alias']}: DID={data['did']}")
            else:
                print(f"⚠️ Failed to register {agent['alias']}: {resp.text}")
        except Exception as e:
            print(f"❌ Exception registering {agent['alias']}: {e}")

if __name__ == "__main__":
    register_dids()
