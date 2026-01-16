import os
import json
import base64
import sqlite3
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class FireVaultCore:
    def __init__(self, master_password):
        self.db_name = "vault.db"
        # We derive a secure key from your master password
        self.key = self._generate_key(master_password)
        self.cipher = Fernet(self.key)
        self._init_db()

    def _generate_key(self, password):
        """Turn a text password into a 32-byte Fernet Key using Salt"""
        # In a real app, store this salt in a file. For now, we hardcode a 'fixed' salt 
        # so you can restart the app and still get the same key.
        salt = b'some_hardcoded_salt_change_this_later' 
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

    def _init_db(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS secrets (
                id INTEGER PRIMARY KEY,
                site TEXT UNIQUE,
                username TEXT,
                encrypted_password TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def add_password(self, site, username, password):
        encrypted_pwd = self.cipher.encrypt(password.encode()).decode()
        
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO secrets (site, username, encrypted_password) VALUES (?, ?, ?)", 
                           (site, username, encrypted_password))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False

    def get_password(self, site):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        # Find entries where the site contains the search term (e.g., "google" finds "google.com")
        cursor.execute("SELECT username, encrypted_password FROM secrets WHERE site LIKE ?", (f'%{site}%',))
        result = cursor.fetchone()
        conn.close()

        if result:
            username, enc_pwd = result
            decrypted_pwd = self.cipher.decrypt(enc_pwd.encode()).decode()
            return username, decrypted_pwd
        return None, None

# --- TEST IT OUT ---
if __name__ == "__main__":
    # 1. Login
    mp = input("Set a Master Password for this session: ")
    vault = FireVaultCore(mp)

    # 2. Add a fake password
    vault.add_password("facebook.com", "cool_user", "Hunter2_Secret!")
    print("Saved password for Facebook.")

    # 3. Retrieve it
    user, pwd = vault.get_password("facebook")
    if user:
        print(f"Found! User: {user} | Password: {pwd}")
    else:
        print("Not found.")