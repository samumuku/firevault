from flask import Flask, request, jsonify
from flask_cors import CORS
from vault_core import FireVaultCore
import getpass

app = Flask(__name__)
# Allow the browser extension to talk to us
CORS(app) 

# Global vault variable
vault = None

@app.route('/get_credentials', methods=['GET'])
def get_credentials():
    global vault
    if not vault:
        return jsonify({"error": "Vault locked"}), 403

    site_query = request.args.get('site', '')
    if not site_query:
        return jsonify({"error": "No site provided"}), 400

    # Get list of [(username, password), (username, password)...]
    creds = vault.get_credentials(site_query)
    
    if creds:
        # Convert list of tuples to list of dictionaries for JSON
        account_list = [{"username": c[0], "password": c[1]} for c in creds]
        return jsonify({
            "found": True,
            "count": len(account_list),
            "accounts": account_list
        })
    else:
        return jsonify({"found": False, "count": 0})

if __name__ == '__main__':
    print("--- FireVault Browser Bridge ---")
    pwd = getpass.getpass("Enter Master Password to start server: ")
    
    try:
        # Unlock the vault once at startup
        vault = FireVaultCore.login(pwd)
        print("✅ Vault Unlocked! Listening for browser requests...")
        # Run the server on port 5000
        app.run(port=5000)
    except Exception as e:
        print(f"❌ Failed to start: {e}")