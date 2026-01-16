import customtkinter as ctk
from vault_core import FireVaultCore
import pyperclip # To copy to clipboard

class LoginScreen(ctk.CTkFrame):
    def __init__(self, master, on_success):
        super().__init__(master)
        self.on_success = on_success
        self.pack(fill="both", expand=True)

        ctk.CTkLabel(self, text="🔒 FireVault", font=("Arial", 24, "bold")).pack(pady=40)
        
        self.entry = ctk.CTkEntry(self, placeholder_text="Master Password", show="*", width=200)
        self.entry.pack(pady=10)
        self.entry.bind("<Return>", lambda e: self.unlock())

        ctk.CTkButton(self, text="Unlock", command=self.unlock).pack(pady=10)

    def unlock(self):
        pwd = self.entry.get()
        if pwd:
            # Initialize the Core with this password
            vault = FireVaultCore(pwd)
            self.on_success(vault)

class VaultDashboard(ctk.CTkFrame):
    def __init__(self, master, vault):
        super().__init__(master)
        self.vault = vault
        self.pack(fill="both", expand=True)

        # UI Layout
        ctk.CTkLabel(self, text="Password Manager", font=("Arial", 20)).pack(pady=20)

        # --- ADD SECTION ---
        self.frame_add = ctk.CTkFrame(self)
        self.frame_add.pack(pady=10, padx=20, fill="x")
        
        self.entry_site = ctk.CTkEntry(self.frame_add, placeholder_text="Site (e.g. google.com)")
        self.entry_site.pack(side="left", padx=5, expand=True, fill="x")
        
        self.entry_user = ctk.CTkEntry(self.frame_add, placeholder_text="Username")
        self.entry_user.pack(side="left", padx=5, expand=True, fill="x")
        
        self.entry_pass = ctk.CTkEntry(self.frame_add, placeholder_text="Password", show="*")
        self.entry_pass.pack(side="left", padx=5, expand=True, fill="x")
        
        ctk.CTkButton(self.frame_add, text="Save", width=60, command=self.save_entry).pack(side="left", padx=5)

        # --- SEARCH SECTION ---
        self.frame_search = ctk.CTkFrame(self)
        self.frame_search.pack(pady=10, padx=20, fill="x")
        
        self.search_entry = ctk.CTkEntry(self.frame_search, placeholder_text="Search Site...")
        self.search_entry.pack(side="left", padx=5, expand=True, fill="x")
        
        ctk.CTkButton(self.frame_search, text="Get", width=60, command=self.search_entry_func).pack(side="left", padx=5)

        # --- DEBUG BUTTON ---
        ctk.CTkButton(self, text="Show All Saved Sites", fg_color="#555", command=self.show_all_sites).pack(pady=5)

        # --- RESULTS AREA ---
        self.lbl_result = ctk.CTkLabel(self, text="", font=("Consolas", 14), text_color="yellow")
        self.lbl_result.pack(pady=20)

    def save_entry(self):
        s = self.entry_site.get()
        u = self.entry_user.get()
        p = self.entry_pass.get()
        
        if s and u and p:
            success, message = self.vault.add_password(s, u, p)
            if success:
                self.lbl_result.configure(text=f"Saved {s}!", text_color="green")
                self.entry_site.delete(0, "end")
                self.entry_pass.delete(0, "end")
            else:
                # SHOW THE ERROR if it fails
                self.lbl_result.configure(text=f"Error: {message}", text_color="red")
        else:
             self.lbl_result.configure(text="Please fill all fields.", text_color="orange")

    def show_all_sites(self):
        sites = self.vault.get_all_sites()
        if sites:
            # Join them with newlines
            text = "Stored Sites:\n" + "\n".join(sites)
            self.lbl_result.configure(text=text, text_color="white")
        else:
            self.lbl_result.configure(text="Database is empty!", text_color="red")

    def search_entry_func(self):
        query = self.search_entry.get()
        u, p = self.vault.get_password(query)
        if u:
            self.lbl_result.configure(text=f"User: {u}\nPassword: {p} (Copied!)", text_color="cyan")
            pyperclip.copy(p) # Auto copy password
        else:
            self.lbl_result.configure(text="No match found.", text_color="red")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("600x400")
        self.title("FireVault")
        LoginScreen(self, self.show_dashboard)

    def show_dashboard(self, vault_instance):
        for widget in self.winfo_children(): widget.destroy()
        VaultDashboard(self, vault_instance)

if __name__ == "__main__":
    app = App()
    app.mainloop()