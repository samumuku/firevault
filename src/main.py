import customtkinter as ctk
import pyperclip
from vault_core import FireVaultCore

# --- DIALOG: ADD NEW PASSWORD ---
class AddPasswordDialog(ctk.CTkToplevel):
    def __init__(self, parent, vault, refresh_callback):
        super().__init__(parent)
        self.vault = vault
        self.refresh_callback = refresh_callback
        self.title("Add New Password")
        self.geometry("400x350")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.grab_set()

        ctk.CTkLabel(self, text="Add Credentials", font=("Arial", 20, "bold")).pack(pady=20)

        self.entry_site = ctk.CTkEntry(self, placeholder_text="Website (e.g. netflix.com)", width=300)
        self.entry_site.pack(pady=10)

        self.entry_user = ctk.CTkEntry(self, placeholder_text="Username / Email", width=300)
        self.entry_user.pack(pady=10)

        self.entry_pass = ctk.CTkEntry(self, placeholder_text="Password", show="*", width=300)
        self.entry_pass.pack(pady=10)

        ctk.CTkButton(self, text="Save Password", command=self.save, fg_color="#2ecc71").pack(pady=20)
        self.lbl_error = ctk.CTkLabel(self, text="", text_color="red")
        self.lbl_error.pack(pady=5)

    def save(self):
        s = self.entry_site.get()
        u = self.entry_user.get()
        p = self.entry_pass.get()

        if s and u and p:
            success, msg = self.vault.add_password(s, u, p)
            if success:
                self.refresh_callback() 
                self.destroy() 
            else:
                self.lbl_error.configure(text=f"Error: {msg}")
        else:
            self.lbl_error.configure(text="All fields required")

# --- SCREEN 1: CREATE NEW VAULT ---
class CreateScreen(ctk.CTkFrame):
    def __init__(self, master, on_success):
        super().__init__(master)
        self.on_success = on_success
        self.pack(fill="both", expand=True)
        self.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(self, text="Setup FireVault", font=("Arial", 24, "bold")).pack(pady=(40, 20))
        ctk.CTkLabel(self, text="Create a Master Password.\nDon't lose this! It cannot be recovered.", 
                     text_color="gray").pack(pady=(0, 20))
        
        self.entry = ctk.CTkEntry(self, placeholder_text="New Master Password", show="*", width=220)
        self.entry.pack(pady=5)
        self.entry_confirm = ctk.CTkEntry(self, placeholder_text="Confirm Password", show="*", width=220)
        self.entry_confirm.pack(pady=5)
        self.lbl_error = ctk.CTkLabel(self, text="", text_color="red")
        self.lbl_error.pack(pady=5)
        ctk.CTkButton(self, text="Create Vault", command=self.create).pack(pady=20)

    def create(self):
        p1 = self.entry.get()
        p2 = self.entry_confirm.get()
        if not p1: return
        if p1 != p2:
            self.lbl_error.configure(text="Passwords do not match")
            return
        vault = FireVaultCore.create_vault(p1)
        self.on_success(vault)

# --- SCREEN 2: UNLOCK VAULT ---
class LoginScreen(ctk.CTkFrame):
    def __init__(self, master, on_success):
        super().__init__(master)
        self.on_success = on_success
        self.pack(fill="both", expand=True)

        ctk.CTkLabel(self, text="Locked", font=("Arial", 24, "bold")).pack(pady=40)
        self.entry = ctk.CTkEntry(self, placeholder_text="Master Password", show="*", width=220)
        self.entry.pack(pady=10)
        self.entry.bind("<Return>", lambda e: self.attempt_login())
        self.lbl_error = ctk.CTkLabel(self, text="", text_color="red")
        self.lbl_error.pack(pady=5)
        ctk.CTkButton(self, text="Unlock", command=self.attempt_login).pack(pady=10)

    def attempt_login(self):
        pwd = self.entry.get()
        try:
            vault = FireVaultCore.login(pwd)
            self.on_success(vault)
        except ValueError:
            self.lbl_error.configure(text="Wrong Password!")
            self.entry.delete(0, "end")
        except Exception as e:
            self.lbl_error.configure(text=f"Error: {e}")

# --- SCREEN 3: MAIN DASHBOARD ---
class VaultDashboard(ctk.CTkFrame):
    def __init__(self, master, vault):
        super().__init__(master)
        self.vault = vault
        self.pack(fill="both", expand=True)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=1)

        # --- LEFT SIDEBAR (Global Site List) ---
        self.sidebar = ctk.CTkFrame(self, fg_color="#2b2b2b", corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        # Header with Global Search
        self.sidebar_header = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.sidebar_header.pack(fill="x", padx=10, pady=20)
        
        row1 = ctk.CTkFrame(self.sidebar_header, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(row1, text="MY SITES", font=("Arial", 14, "bold"), text_color="gray").pack(side="left")
        ctk.CTkButton(row1, text="+", width=30, height=30, fg_color="#2ecc71", command=self.open_add_dialog).pack(side="right")
        
        self.global_search = ctk.CTkEntry(self.sidebar_header, placeholder_text="Search Sites...", height=30)
        self.global_search.pack(fill="x")
        self.global_search.bind("<KeyRelease>", self.on_global_search)

        self.site_list_frame = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent")
        self.site_list_frame.pack(fill="both", expand=True, padx=5, pady=5)

        ctk.CTkButton(self.sidebar, text="Lock Vault", fg_color="#c0392b", height=40,
                      command=self.lock_app).pack(fill="x", padx=10, pady=20)

        # --- RIGHT DETAILS AREA ---
        self.details_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.details_frame.grid(row=0, column=1, sticky="nsew", padx=40, pady=40)
        
        # Initial Placeholder
        self.lbl_placeholder = ctk.CTkLabel(self.details_frame, text="Select a website to view details", 
                                            font=("Arial", 20), text_color="gray")
        self.lbl_placeholder.pack(expand=True)

        # Content Container (Hidden until site selected)
        # We split this into a Header (Fixed) and a List (Scrollable)
        self.content_area = ctk.CTkFrame(self.details_frame, fg_color="transparent")
        
        # 1. Right Header (Title + Local Search)
        self.right_header = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.right_header.pack(fill="x", pady=(0, 20))
        
        self.lbl_site_title = ctk.CTkLabel(self.right_header, text="", font=("Arial", 32, "bold"), text_color="white")
        self.lbl_site_title.pack(side="left")

        self.local_search = ctk.CTkEntry(self.right_header, placeholder_text="Filter accounts...", width=200)
        self.local_search.pack(side="right")
        self.local_search.bind("<KeyRelease>", self.on_local_search)

        # 2. Account Cards List
        self.account_list_frame = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")
        self.account_list_frame.pack(fill="both", expand=True)

        # Data State
        self.all_sites = [] 
        self.current_site_accounts = [] # Stores [(user, pass), (user, pass)]
        self.refresh_list()

    def open_add_dialog(self):
        AddPasswordDialog(self, self.vault, self.refresh_list)

    def refresh_list(self):
        self.all_sites = self.vault.get_all_sites()
        self.all_sites.sort()
        self.update_sidebar_list(self.all_sites)

    def on_global_search(self, event):
        query = self.global_search.get().lower()
        if not query:
            self.update_sidebar_list(self.all_sites)
        else:
            filtered = [s for s in self.all_sites if query in s.lower()]
            self.update_sidebar_list(filtered)

    def update_sidebar_list(self, sites_to_show):
        for widget in self.site_list_frame.winfo_children():
            widget.destroy()

        if not sites_to_show:
            ctk.CTkLabel(self.site_list_frame, text="No matches", text_color="gray").pack(pady=20)
            return

        for site in sites_to_show:
            btn = ctk.CTkButton(self.site_list_frame, text=site, anchor="w", fg_color="transparent",
                                hover_color="#444", height=40, font=("Arial", 14),
                                command=lambda s=site: self.show_details(s))
            btn.pack(fill="x", pady=2)

    def show_details(self, site):
        self.lbl_placeholder.pack_forget()
        self.content_area.pack(fill="both", expand=True)
        
        # Reset Local Search
        self.local_search.delete(0, "end")
        self.lbl_site_title.configure(text=site)

        # Fetch and Store Data
        self.current_site_accounts = self.vault.get_credentials(site)
        
        # Render
        self.render_account_cards(self.current_site_accounts)

    def on_local_search(self, event):
        query = self.local_search.get().lower()
        
        if not query:
            self.render_account_cards(self.current_site_accounts)
            return

        # Filter by Username
        filtered = [acc for acc in self.current_site_accounts if query in acc[0].lower()]
        self.render_account_cards(filtered)

    def render_account_cards(self, accounts):
        for widget in self.account_list_frame.winfo_children():
            widget.destroy()

        if not accounts:
            ctk.CTkLabel(self.account_list_frame, text="No accounts found.", text_color="red").pack()
            return

        for username, password in accounts:
            self.create_account_card(username, password)

    def create_account_card(self, username, password):
        card = ctk.CTkFrame(self.account_list_frame, fg_color="#333", corner_radius=10)
        card.pack(fill="x", pady=10, ipady=10)

        # Username
        row_user = ctk.CTkFrame(card, fg_color="transparent")
        row_user.pack(fill="x", padx=15, pady=5)
        ctk.CTkLabel(row_user, text="USERNAME", font=("Arial", 10, "bold"), text_color="gray").pack(anchor="w")
        
        u_box = ctk.CTkFrame(row_user, fg_color="transparent")
        u_box.pack(fill="x")
        ctk.CTkLabel(u_box, text=username, font=("Consolas", 16), text_color="white").pack(side="left")
        ctk.CTkButton(u_box, text="Copy", width=50, height=20, fg_color="#555",
                      command=lambda: self.copy_to_clipboard(username)).pack(side="right")

        # Password
        row_pass = ctk.CTkFrame(card, fg_color="transparent")
        row_pass.pack(fill="x", padx=15, pady=5)
        ctk.CTkLabel(row_pass, text="PASSWORD", font=("Arial", 10, "bold"), text_color="gray").pack(anchor="w")

        p_box = ctk.CTkFrame(row_pass, fg_color="transparent")
        p_box.pack(fill="x")
        
        lbl_pass = ctk.CTkLabel(p_box, text="•" * 12, font=("Consolas", 16), text_color="white")
        lbl_pass.pack(side="left")

        btns = ctk.CTkFrame(p_box, fg_color="transparent")
        btns.pack(side="right")
        
        btn_show = ctk.CTkButton(btns, text="Show", width=50, height=20, fg_color="#555")
        btn_show.configure(command=lambda l=lbl_pass, b=btn_show, p=password: self.toggle_pass(l, b, p))
        btn_show.pack(side="left", padx=5)

        ctk.CTkButton(btns, text="Copy", width=50, height=20, fg_color="#555",
                      command=lambda: self.copy_to_clipboard(password)).pack(side="left")

    def toggle_pass(self, label, btn, real_pass):
        if btn.cget("text") == "Show":
            label.configure(text=real_pass)
            btn.configure(text="Hide", fg_color="#d35400")
        else:
            label.configure(text="•" * 12)
            btn.configure(text="Show", fg_color="#555")

    def copy_to_clipboard(self, text):
        try: pyperclip.copy(text)
        except: pass

    def lock_app(self):
        self.master.show_auth_screen()

# --- APP CONTROLLER ---
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("950x650")
        self.title("FireVault")
        self.show_auth_screen()

    def show_auth_screen(self):
        for widget in self.winfo_children(): widget.destroy()
        if FireVaultCore.is_setup():
            LoginScreen(self, self.show_dashboard)
        else:
            CreateScreen(self, self.show_dashboard)

    def show_dashboard(self, vault_instance):
        for widget in self.winfo_children(): widget.destroy()
        VaultDashboard(self, vault_instance)

if __name__ == "__main__":
    app = App()
    app.mainloop()