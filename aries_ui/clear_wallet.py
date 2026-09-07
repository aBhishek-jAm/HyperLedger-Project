import requests

# Student Agent URL
STUDENT_AGENT = "http://localhost:8022"

def clear_wallet():
    print("🧹 Cleaning Student Wallet...")
    
    # 1. Get all credentials
    try:
        response = requests.get(f"{STUDENT_AGENT}/credentials")
        creds = response.json().get('results', [])
    except:
        print("❌ Could not connect to Student Agent.")
        return

    if not creds:
        print("✅ Wallet is already empty.")
        return

    print(f"found {len(creds)} old credentials. Deleting...")

    # 2. Delete them one by one
    for cred in creds:
        referent = cred['referent']
        # The API endpoint to remove a credential from the wallet
        requests.delete(f"{STUDENT_AGENT}/credential/{referent}")
        print(f"   - Deleted: {cred['attrs']['name']} (ID: {referent})")

    print("✨ Wallet is now clean! You can Issue a fresh ID now.")

if __name__ == "__main__":
    clear_wallet()