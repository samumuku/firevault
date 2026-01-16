import os
import json
import base64
import sqlite3
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

CONFIG_FILE = "vault_config.json"
DB_FILE = "vault.db"

class FireVaultCore:
    def __init__(self, key):
        self.db_name = DB_FILE
        self.cipher = Fernet(key)

    @staticmethod
    def is_setup():
        return os.path.exists(CONFIG_FILE) and os.path.exists(DB_FILE)

    @staticmethod
    def create_vault(master_password):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        
        auth_salt = os.urandom(16)
        key_salt = os.urandom(16)
        auth_hash = hashlib.sha256(auth_salt + master_password.encode()).hexdigest()

        config = {"auth_salt": auth_salt.hex(), "key_salt": key_salt.hex(), "auth_hash": auth_hash}
        with open(CONFIG_FILE, "w") as f: json.dump(config, f)

        key = FireVaultCore._derive_key(master_password, key_salt)
        vault = FireVaultCore(key)
        vault._init_db()
        return vault

    @staticmethod
    def login(master_password):
        if not os.path.exists(CONFIG_FILE): raise Exception("Vault not found.")
        with open(CONFIG_FILE, "r") as f: config = json.load(f)

        auth_salt = bytes.fromhex(config["auth_salt"])
        key_salt = bytes.fromhex(config["key_salt"])
        
        if hashlib.sha256(auth_salt + master_password.encode()).hexdigest() != config["auth_hash"]:
            raise ValueError("Invalid Password")

        key = FireVaultCore._derive_key(master_password, key_salt)
        return FireVaultCore(key)

    @staticmethod
    def _derive_key(password, salt):
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=480000)
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

    def _init_db(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        # CHANGED: 'site' is no longer UNIQUE by itself.
        # We added UNIQUE(site, username) so you can have google/bob and google/alice, but not google/bob twice.
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS secrets (
                id INTEGER PRIMARY KEY,
                site TEXT,
                username TEXT,
                encrypted_password TEXT,
                UNIQUE(site, username)
            )
        ''')
        conn.commit()
        conn.close()

    def add_password(self, site, username, password):
        site = site.strip()
        username = username.strip()
        try:
            encrypted_pwd = self.cipher.encrypt(password.encode()).decode()
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO secrets (site, username, encrypted_password) VALUES (?, ?, ?)", 
                           (site, username, encrypted_pwd))
            conn.commit()
            conn.close()
            return True, "Success"
        except Exception as e:
            return False, str(e)

    # CHANGED: Returns a LIST of (username, password) tuples
    def get_credentials(self, site):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT username, encrypted_password FROM secrets WHERE site = ?", (site,))
        results = cursor.fetchall()
        conn.close()

        decrypted_accounts = []
        for username, enc_pwd in results:
            try:
                dec_pwd = self.cipher.decrypt(enc_pwd.encode()).decode()
                decrypted_accounts.append((username, dec_pwd))
            except:
                decrypted_accounts.append((username, "DECRYPTION ERROR"))
        
        return decrypted_accounts
    
    def get_all_sites(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT site FROM secrets")
        results = [r[0] for r in cursor.fetchall()]
        conn.close()
        return results