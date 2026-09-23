#!/usr/bin/env python3
"""
shieldHer - Safety Check-in Application
A simple MVP for personal safety awareness
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import subprocess
import time
import threading
import json
import hashlib
import datetime
import shutil
import urllib.request
import urllib.error
import urllib.parse
import webbrowser
import smtplib
import http.server
import socketserver
from email.message import EmailMessage

# File paths
DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
GLOBAL_CONTACTS_FILE = os.path.join(DATA_DIR, "contacts.txt")
GLOBAL_SAFE_PLACES_FILE = os.path.join(DATA_DIR, "safe_places.txt")

# Analyzer binary name per platform
ANALYZER_BIN = "analyzer.exe" if os.name == "nt" else "./analyzer"

# Timer slider settings (in seconds for UI, converted to minutes for C analyzer)
TIMER_MIN_SECONDS = 10  # 10 seconds minimum
TIMER_MAX_SECONDS = 600  # 10 minutes maximum
TIMER_DEFAULT_SECONDS = 60  # 1 minute default

LOCATION_API_URL = "https://ipapi.co/json/"


def _digits_only(value):
    return "".join(ch for ch in value if ch.isdigit())


def _to_indian_10_digits(value):
    digits = _digits_only(value)
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    elif len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]
    return digits if len(digits) == 10 else None


def _is_valid_email(value):
    text = value.strip()
    if not text:
        return False
    if "@" not in text:
        return False
    local, _, domain = text.partition("@")
    if not local or not domain:
        return False
    if "." not in domain:
        return False
    return True


COLORS = {
    "bg_primary": "#0F0A1A",       # Deep dark purple/charcoal
    "bg_secondary": "#1A1428",      # Card background
    "bg_tertiary": "#221D30",       # Input fields & hover
    "accent_primary": "#8B5CF6",    # Vibrant purple
    "accent_secondary": "#A78BFA",  # Soft purple / hover
    "accent_tertiary": "#C4B5FD",   # Light lavender
    "text_primary": "#F5F3FF",      # Near white
    "text_secondary": "#A5A0B8",    # Muted grey-purple
    "text_muted": "#6B6580",        # Dim text
    "success": "#10B981",           # Green - low risk
    "warning": "#F59E0B",           # Amber - medium risk
    "danger": "#EF4444",            # Red - high risk
    "critical": "#DC2626",          # Deep red - critical
    "border": "#2E2A3C",            # Subtle borders
    "card_bg": "#1E1A2E",           # Slightly lighter card
    "btn_primary": "#8B5CF6",
    "btn_hover": "#9D6FFF",
    "btn_text": "#F5F3FF",
    "gradient_top": "#2D1B69",      # Purple gradient top
    "gradient_bottom": "#0F0A1A",   # Gradient bottom
}


def styled_button(parent, text, bg, fg, font=None, on_click=None,
                  padx=20, pady=10, hover_bg=None, width=None, anchor="center"):
    """Create a Label-based button that renders correctly on all platforms including macOS."""
    _font = font or ("Segoe UI", 11, "bold")
    _hover = hover_bg or bg
    btn = tk.Label(parent, text=text, bg=bg, fg=fg, font=_font,
                   padx=padx, pady=pady, cursor="hand2", anchor=anchor)
    if width:
        btn.configure(width=width)
    btn.bind("<Button-1>", lambda e: on_click() if on_click else None)
    btn.bind("<Enter>", lambda e: btn.configure(bg=_hover))
    btn.bind("<Leave>", lambda e: btn.configure(bg=bg))
    return btn


def configure_app_style(root):
    """Apply a modern dark visual style."""
    style = ttk.Style(root)
    available = style.theme_names()
    if "clam" in available:
        style.theme_use("clam")

    bg = COLORS["bg_primary"]
    fg = COLORS["text_primary"]

    root.configure(bg=bg)
    style.configure(".", font=("Segoe UI", 10), background=bg, foreground=fg)

    style.configure("TFrame", background=bg)
    style.configure("App.TFrame", background=bg)
    style.configure("Dark.TFrame", background=COLORS["bg_secondary"])
    style.configure("Card.TFrame", background=COLORS["card_bg"])

    style.configure("TLabel", background=bg, foreground=fg)
    style.configure("Title.TLabel", background=bg, foreground=COLORS["accent_primary"], font=("Segoe UI", 24, "bold"))
    style.configure("Subtitle.TLabel", background=bg, foreground=COLORS["text_secondary"], font=("Segoe UI", 12))
    style.configure("Heading.TLabel", background=bg, foreground=COLORS["accent_secondary"], font=("Segoe UI", 14, "bold"))
    style.configure("Muted.TLabel", background=bg, foreground=COLORS["text_muted"], font=("Segoe UI", 9))

    style.configure("Card.TLabelframe", background=COLORS["card_bg"], borderwidth=1, relief="solid")
    style.configure(
        "Card.TLabelframe.Label",
        background=COLORS["card_bg"],
        foreground=COLORS["accent_secondary"],
        font=("Segoe UI", 11, "bold"),
    )

    style.configure("TEntry", fieldbackground=COLORS["bg_tertiary"],
                    foreground=fg, insertcolor=fg, padding=8)
    style.map("TEntry", fieldbackground=[("focus", COLORS["bg_secondary"])])

    style.configure("TCheckbutton", background=bg, foreground=COLORS["text_secondary"])
    style.map("TCheckbutton", foreground=[("selected", COLORS["accent_primary"])])

    style.configure("TNotebook", background=bg, borderwidth=0)
    style.configure("TNotebook.Tab", 
                    background=COLORS["bg_secondary"],
                    foreground=COLORS["text_secondary"],
                    padding=(24, 10),
                    font=("Segoe UI", 10))
    style.map("TNotebook.Tab",
              background=[("selected", COLORS["accent_primary"])],
              foreground=[("selected", COLORS["text_primary"])],
              expand=[("selected", [1, 1, 1, 0])])

    style.configure("TScale", background=bg, troughcolor=COLORS["bg_tertiary"])

    style.configure("Primary.TButton",
                    background=COLORS["btn_primary"],
                    foreground=COLORS["btn_text"],
                    padding=(20, 10),
                    font=("Segoe UI", 10, "bold"),
                    borderwidth=0)
    style.map("Primary.TButton",
              background=[("active", COLORS["btn_hover"]),
                          ("pressed", COLORS["accent_primary"])])

    style.configure("Secondary.TButton",
                    background=COLORS["bg_tertiary"],
                    foreground=COLORS["text_primary"],
                    padding=(14, 8),
                    borderwidth=0)
    style.map("Secondary.TButton",
              background=[("active", COLORS["bg_secondary"]),
                          ("pressed", COLORS["bg_tertiary"])])

    style.configure("Danger.TButton",
                    background=COLORS["danger"],
                    foreground="#FFFFFF",
                    padding=(14, 8),
                    borderwidth=0)

    style.configure("TProgressbar",
                    background=COLORS["accent_primary"],
                    troughcolor=COLORS["bg_tertiary"],
                    borderwidth=0,
                    thickness=10)


def hash_password(password, salt):
    """Hash password with salt using sha256"""
    return hashlib.sha256((salt + password).encode()).hexdigest()


def generate_salt():
    """Generate a random salt"""
    import secrets

    return secrets.token_hex(16)


def load_users():
    """Load users from JSON file"""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_users(users):
    """Save users to JSON file"""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


def get_user_dir(username):
    """Get user-specific directory"""
    return os.path.join(DATA_DIR, "users", username)


def get_user_file(username, filename):
    """Get user-specific file path"""
    return os.path.join(get_user_dir(username), filename)


def init_user_files(username):
    """Initialize user files from global defaults if they don't exist"""
    user_dir = get_user_dir(username)
    os.makedirs(user_dir, exist_ok=True)

    # Initialize contacts from global if not exists
    user_contacts = get_user_file(username, "contacts.txt")
    if not os.path.exists(user_contacts):
        if os.path.exists(GLOBAL_CONTACTS_FILE):
            shutil.copy(GLOBAL_CONTACTS_FILE, user_contacts)

    # Initialize safe_places from global if not exists
    user_safe_places = get_user_file(username, "safe_places.txt")
    if not os.path.exists(user_safe_places):
        if os.path.exists(GLOBAL_SAFE_PLACES_FILE):
            shutil.copy(GLOBAL_SAFE_PLACES_FILE, user_safe_places)


class AuthScreen:
    """Modern authentication screen with login and signup"""

    def __init__(self, root, on_login_success):
        self.root = root
        self.root.title("shieldHer")
        self.root.geometry("480x680")
        self.root.minsize(420, 600)
        self.root.resizable(True, True)
        self.on_login_success = on_login_success
        configure_app_style(self.root)

        self._center_window(480, 680)
        self.setup_ui()

    def _center_window(self, w, h):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def setup_ui(self):
        bg = COLORS["bg_primary"]
        card_bg = COLORS["card_bg"]

        main_frame = tk.Frame(self.root, bg=bg)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Gradient header area using Canvas
        header = tk.Canvas(main_frame, height=200, bg=bg, highlightthickness=0)
        header.pack(fill=tk.X)

        # Draw gradient bars as visual header
        for i in range(200):
            r = int(15 + (45 - 15) * i / 200)
            g = int(10 + (27 - 10) * i / 200)
            b = int(26 + (105 - 26) * i / 200)
            color = f"#{r:02x}{g:02x}{b:02x}"
            header.create_line(0, i, 600, i, fill=color, width=1)

        # Logo area
        header.create_oval(190, 30, 290, 130, fill=COLORS["accent_primary"], outline="")
        header.create_text(240, 80, text="SH", fill="#FFFFFF",
                           font=("Segoe UI", 32, "bold"))

        header.create_text(240, 150, text="shieldHer", fill=COLORS["text_primary"],
                           font=("Segoe UI", 26, "bold"))
        header.create_text(240, 178, text="Safety Check-in", fill=COLORS["accent_tertiary"],
                           font=("Segoe UI", 12))

        # Card area
        card_container = tk.Frame(main_frame, bg=bg)
        card_container.pack(fill=tk.BOTH, expand=True, padx=20)

        # Tab selector (custom toggle-style)
        tab_frame = tk.Frame(card_container, bg=COLORS["bg_secondary"])
        tab_frame.pack(fill=tk.X, pady=(0, 1))

        self.login_tab_btn = tk.Label(
            tab_frame, text="  Sign In  ",
            bg=COLORS["accent_primary"], fg=COLORS["text_primary"],
            font=("Segoe UI", 11, "bold"), padx=30, pady=8, cursor="hand2")
        self.login_tab_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.login_tab_btn.bind("<Button-1>", lambda e: self._show_tab(0))

        self.signup_tab_btn = tk.Label(
            tab_frame, text="  Create Account  ",
            bg=COLORS["bg_secondary"], fg=COLORS["text_secondary"],
            font=("Segoe UI", 11, "bold"), padx=30, pady=8, cursor="hand2")
        self.signup_tab_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.signup_tab_btn.bind("<Button-1>", lambda e: self._show_tab(1))

        def on_hover(e, btn, active):
            if btn != self._active_tab_btn():
                btn.configure(bg=COLORS["bg_tertiary"] if active else COLORS["bg_secondary"])

        for btn in [self.login_tab_btn, self.signup_tab_btn]:
            btn.bind("<Enter>", lambda e, b=btn: on_hover(e, b, True))
            btn.bind("<Leave>", lambda e, b=btn: on_hover(e, b, False))

        # Form content area with card background, wrapped in scrollable canvas
        self.form_card = tk.Frame(card_container, bg=card_bg)
        self.form_card.pack(fill=tk.BOTH, expand=True)

        # Scrollable canvas + bar
        self.form_canvas = tk.Canvas(self.form_card, bg=card_bg, highlightthickness=0, bd=0)
        self.form_scrollbar = tk.Scrollbar(self.form_card, orient=tk.VERTICAL,
                                            command=self.form_canvas.yview)
        self.form_canvas.configure(yscrollcommand=self.form_scrollbar.set)

        self.form_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.form_inner = tk.Frame(self.form_canvas, bg=card_bg, padx=30, pady=20)
        self._canvas_win = self.form_canvas.create_window((0, 0), window=self.form_inner,
                                                           anchor="nw")

        self.form_inner.bind("<Configure>",
                              lambda e: self.form_canvas.configure(
                                  scrollregion=self.form_canvas.bbox("all")))
        self.form_canvas.bind("<Configure>",
                               lambda e: self.form_canvas.itemconfigure(
                                   self._canvas_win, width=e.width))

        # Mousewheel scrolling
        def _on_form_scroll(event):
            if event.delta:
                self.form_canvas.yview_scroll(int(-event.delta / 120), "units")
        self.form_canvas.bind("<MouseWheel>", _on_form_scroll)

        # Build login form
        self._build_login_form()
        # Build signup form (hidden)
        self._build_signup_form()
        # Show login by default
        self._show_tab(0)

    def _active_tab_btn(self):
        if self.login_form.winfo_viewable():
            return self.login_tab_btn
        return self.signup_tab_btn

    def _show_tab(self, idx):
        if idx == 0:
            self.login_tab_btn.configure(bg=COLORS["accent_primary"], fg=COLORS["text_primary"])
            self.signup_tab_btn.configure(bg=COLORS["bg_secondary"], fg=COLORS["text_secondary"])
            self.signup_form.pack_forget()
            self.login_form.pack(fill=tk.BOTH, expand=True)
            self.form_scrollbar.pack_forget()
        else:
            self.signup_tab_btn.configure(bg=COLORS["accent_primary"], fg=COLORS["text_primary"])
            self.login_tab_btn.configure(bg=COLORS["bg_secondary"], fg=COLORS["text_secondary"])
            self.login_form.pack_forget()
            self.signup_form.pack(fill=tk.BOTH, expand=True)
            self.form_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_input(self, parent, label_text, show=""):
        """Create a styled input field."""
        frm = tk.Frame(parent, bg=COLORS["card_bg"])
        frm.pack(fill=tk.X, pady=4)

        lbl = tk.Label(frm, text=label_text, bg=COLORS["card_bg"],
                       fg=COLORS["text_secondary"], font=("Segoe UI", 9),
                       anchor="w")
        lbl.pack(anchor="w")

        entry = tk.Entry(frm, bg=COLORS["bg_tertiary"], fg=COLORS["text_primary"],
                         insertbackground=COLORS["accent_primary"],
                         font=("Segoe UI", 11), relief="flat",
                         show=show, bd=0, highlightthickness=0)
        entry.pack(fill=tk.X, ipady=8, pady=(4, 0))

        # Draw bottom accent line
        line = tk.Frame(frm, height=2, bg=COLORS["border"])
        line.pack(fill=tk.X)

        def on_focus_in(e):
            line.configure(bg=COLORS["accent_primary"])

        def on_focus_out(e):
            line.configure(bg=COLORS["border"])

        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)

        return entry

    def _build_login_form(self):
        card_bg = COLORS["card_bg"]

        self.login_form = tk.Frame(self.form_inner, bg=card_bg)

        info = tk.Label(self.login_form, text="Welcome back", bg=card_bg,
                        fg=COLORS["accent_secondary"], font=("Segoe UI", 16, "bold"))
        info.pack(pady=(10, 20))

        self.login_username = self._create_input(self.login_form, "Username")
        self.login_password = self._create_input(self.login_form, "Password", show="*")

        login_btn = styled_button(
            self.login_form, text="Sign In",
            bg=COLORS["btn_primary"], fg=COLORS["btn_text"],
            font=("Segoe UI", 13, "bold"),
            hover_bg=COLORS["btn_hover"],
            on_click=self.do_login,
            padx=20, pady=14)
        login_btn.pack(fill=tk.X, pady=(24, 0))

        self.login_password.bind("<Return>", lambda e: self.do_login())

    def _build_signup_form(self):
        card_bg = COLORS["card_bg"]

        self.signup_form = tk.Frame(self.form_inner, bg=card_bg)

        info = tk.Label(self.signup_form, text="Create your account", bg=card_bg,
                        fg=COLORS["accent_secondary"], font=("Segoe UI", 16, "bold"))
        info.pack(pady=(10, 20))

        self.signup_username = self._create_input(self.signup_form, "Username")
        self.signup_password = self._create_input(self.signup_form, "Password", show="*")
        self.signup_fullname = self._create_input(self.signup_form, "Full Name")
        self.signup_phone = self._create_input(self.signup_form, "Phone (10 digits)")

        # Trusted Contacts
        contacts_lbl = tk.Label(self.signup_form, text="Trusted Contacts (3)",
                                bg=card_bg, fg=COLORS["accent_secondary"],
                                font=("Segoe UI", 11, "bold"))
        contacts_lbl.pack(anchor="w", pady=(16, 8))

        self.signup_contacts = []
        for i in range(3):
            cframe = tk.Frame(self.signup_form, bg=COLORS["bg_secondary"], padx=10, pady=8)
            cframe.pack(fill=tk.X, pady=3)

            tk.Label(cframe, text=f"Contact {i+1}", bg=COLORS["bg_secondary"],
                     fg=COLORS["text_secondary"], font=("Segoe UI", 9, "bold")).pack(anchor="w")

            row = tk.Frame(cframe, bg=COLORS["bg_secondary"])
            row.pack(fill=tk.X, pady=2)

            name_entry = tk.Entry(row, bg=COLORS["bg_tertiary"], fg=COLORS["text_primary"],
                                  font=("Segoe UI", 10), relief="flat", bd=0, width=14)
            name_entry.pack(side=tk.LEFT, padx=(0, 4), ipady=4)

            phone_entry = tk.Entry(row, bg=COLORS["bg_tertiary"], fg=COLORS["text_primary"],
                                   font=("Segoe UI", 10), relief="flat", bd=0, width=14)
            phone_entry.pack(side=tk.LEFT, padx=4, ipady=4)

            email_entry = tk.Entry(row, bg=COLORS["bg_tertiary"], fg=COLORS["text_primary"],
                                   font=("Segoe UI", 10), relief="flat", bd=0, width=18)
            email_entry.pack(side=tk.LEFT, padx=(4, 0), ipady=4)

            self.signup_contacts.append((name_entry, phone_entry, email_entry))

        signup_btn = styled_button(
            self.signup_form, text="Create Account",
            bg=COLORS["btn_primary"], fg=COLORS["btn_text"],
            font=("Segoe UI", 13, "bold"),
            hover_bg=COLORS["btn_hover"],
            on_click=self.do_signup,
            padx=20, pady=14)
        signup_btn.pack(fill=tk.X, pady=(20, 0))

    def do_login(self):
        """Handle login"""
        username = self.login_username.get().strip()
        password = self.login_password.get()

        if not username or not password:
            messagebox.showerror("Error", "Username and password are required")
            return

        users = load_users()

        if username not in users:
            messagebox.showerror("Error", "Invalid username or password")
            return

        user = users[username]
        password_hash = hash_password(password, user["salt"])

        if password_hash != user["password_hash"]:
            messagebox.showerror("Error", "Invalid username or password")
            return

        # Initialize user files if needed
        init_user_files(username)

        # Success - call callback
        self.on_login_success(username)

    def do_signup(self):
        """Handle signup"""
        username = self.signup_username.get().strip()
        password = self.signup_password.get()
        fullname = self.signup_fullname.get().strip()
        phone_raw = self.signup_phone.get().strip()

        if not username or not password:
            messagebox.showerror("Error", "Username and password are required")
            return

        if len(username) < 3:
            messagebox.showerror("Error", "Username must be at least 3 characters")
            return

        if len(password) < 4:
            messagebox.showerror("Error", "Password must be at least 4 characters")
            return

        if not fullname:
            messagebox.showerror("Error", "Full name is required")
            return

        phone_digits = _to_indian_10_digits(phone_raw)
        if not phone_digits:
            messagebox.showerror("Error", "Your phone number must be exactly 10 digits")
            return

        users = load_users()

        if username in users:
            messagebox.showerror("Error", "Username already exists")
            return

        contacts = []
        for idx, (name_entry, phone_entry, email_entry) in enumerate(
            self.signup_contacts, start=1
        ):
            name = name_entry.get().strip()
            contact_phone_raw = phone_entry.get().strip()
            contact_email = email_entry.get().strip()

            if not name and not contact_phone_raw and not contact_email:
                continue
            if not name or not contact_phone_raw or not contact_email:
                messagebox.showerror(
                    "Error",
                    f"Trusted Contact {idx} requires name, phone, and email",
                )
                return

            contact_phone_digits = _to_indian_10_digits(contact_phone_raw)
            if not contact_phone_digits:
                messagebox.showerror(
                    "Error",
                    f"Trusted Contact {idx} phone must be exactly 10 digits",
                )
                return

            if not _is_valid_email(contact_email):
                messagebox.showerror(
                    "Error",
                    f"Trusted Contact {idx} email is invalid",
                )
                return

            contacts.append(f"{name},{contact_phone_digits},{contact_email},")

        salt = generate_salt()
        users[username] = {
            "username": username,
            "password_hash": hash_password(password, salt),
            "salt": salt,
            "full_name": fullname,
            "phone": phone_digits or "",
            "created_at": datetime.datetime.now().isoformat(),
        }

        save_users(users)

        init_user_files(username)

        if contacts:
            user_contacts = get_user_file(username, "contacts.txt")
            with open(user_contacts, "w") as f:
                for contact in contacts:
                    f.write(contact + "\n")

        messagebox.showinfo("Success", "Account created! Please sign in.")
        self._show_tab(0)
        self.login_username.delete(0, tk.END)
        self.login_password.delete(0, tk.END)
        self.signup_username.delete(0, tk.END)
        self.signup_password.delete(0, tk.END)
        self.signup_fullname.delete(0, tk.END)
        self.signup_phone.delete(0, tk.END)
        for name_entry, phone_entry, email_entry in self.signup_contacts:
            name_entry.delete(0, tk.END)
            phone_entry.delete(0, tk.END)
            email_entry.delete(0, tk.END)


class SafetyApp:
    """Modern safety check-in dashboard"""

    def __init__(self, root, username, on_logout=None):
        self.root = root
        self.username = username
        self.on_logout = on_logout
        self.root.title(f"shieldHer - {username}")
        self.root.geometry("680x860")
        self.root.minsize(560, 700)
        self.root.resizable(True, True)
        self._center_window(680, 860)
        configure_app_style(self.root)

        self.user_dir = get_user_dir(username)
        self.INPUT_FILE = get_user_file(username, "input.txt")
        self.OUTPUT_FILE = get_user_file(username, "output.txt")
        self.CONTACTS_FILE = get_user_file(username, "contacts.txt")
        self.SOS_DRAFT_FILE = get_user_file(username, "sos_draft.txt")
        self.HISTORY_FILE = get_user_file(username, "history.csv")
        self.user_profile = self._get_user_profile()
        self.full_name = (
            self.user_profile.get("full_name") or username
        ).strip() or username

        self.questions = {
            "isolated": tk.BooleanVar(value=False),
            "poor_lighting": tk.BooleanVar(value=False),
            "late_night": tk.BooleanVar(value=False),
            "followed": tk.BooleanVar(value=False),
            "low_battery": tk.BooleanVar(value=False),
            "crowded": tk.BooleanVar(value=False),
        }

        self.confidence = tk.IntVar(value=3)
        self.timer_seconds = tk.IntVar(value=TIMER_DEFAULT_SECONDS)
        self.timer_expired = 0
        self.notes = tk.StringVar(value="")
        self.current_location = tk.StringVar(value="No location")
        self.current_time = tk.StringVar(value="")
        self.gps_request_running = False

        self.timer_running = False
        self.timer_thread = None
        self.timer_remaining = 0
        self.last_risk_score = None

        self.setup_ui()
        self.check_night_warning()
        self.update_local_time()
        self.root.after(600, self.prompt_location_permission)

    def _center_window(self, w, h):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def setup_ui(self):
        """Build the modern dashboard layout."""
        bg = COLORS["bg_primary"]
        card_bg = COLORS["card_bg"]

        outer = tk.Frame(self.root, bg=bg)
        outer.pack(fill=tk.BOTH, expand=True)

        # Canvas for potential gradient
        self.main_canvas = tk.Canvas(outer, bg=bg, highlightthickness=0)
        sb = tk.Scrollbar(outer, orient=tk.VERTICAL, command=self.main_canvas.yview)
        self.main_canvas.configure(yscrollcommand=sb.set)

        self.main_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        main_frame = tk.Frame(self.main_canvas, bg=bg, padx=16, pady=12)
        self._canvas_win = self.main_canvas.create_window(
            (0, 0), window=main_frame, anchor="nw")

        main_frame.bind("<Configure>",
                        lambda e: self.main_canvas.configure(
                            scrollregion=self.main_canvas.bbox("all")))
        self.main_canvas.bind("<Configure>",
                              lambda e: self.main_canvas.itemconfigure(
                                  self._canvas_win, width=e.width))

        def _on_mw(event):
            if event.delta:
                self.main_canvas.yview_scroll(int(-event.delta/120), "units")

        self.main_canvas.bind("<MouseWheel>", _on_mw)

        # ---- Header Bar ----
        header = tk.Frame(main_frame, bg=COLORS["bg_secondary"], padx=14, pady=10)
        header.pack(fill=tk.X)

        # Avatar circle
        avatar = tk.Canvas(header, width=36, height=36, bg=COLORS["bg_secondary"],
                           highlightthickness=0)
        avatar.create_oval(2, 2, 34, 34, fill=COLORS["accent_primary"], outline="")
        initials = self.full_name[:2].upper() if self.full_name else self.username[:2].upper()
        avatar.create_text(18, 18, text=initials, fill="#FFFFFF",
                           font=("Segoe UI", 11, "bold"))
        avatar.pack(side=tk.LEFT, padx=(0, 10))

        tk.Label(header, text=self.full_name, bg=COLORS["bg_secondary"],
                 fg=COLORS["text_primary"], font=("Segoe UI", 12, "bold")).pack(side=tk.LEFT)
        tk.Label(header, text=f"@{self.username}", bg=COLORS["bg_secondary"],
                 fg=COLORS["text_muted"], font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=6)

        logout_btn = styled_button(header, text="Logout",
                                    bg=COLORS["bg_tertiary"],
                                    fg=COLORS["text_secondary"],
                                    font=("Segoe UI", 9),
                                    hover_bg=COLORS["danger"],
                                    on_click=self.logout,
                                    padx=12, pady=4)
        logout_btn.pack(side=tk.RIGHT)

        # ---- Title & Time ----
        title_area = tk.Frame(main_frame, bg=bg, pady=8)
        title_area.pack(fill=tk.X)

        tk.Label(title_area, text="Safety Check", bg=bg,
                 fg=COLORS["text_primary"], font=("Segoe UI", 22, "bold")).pack(side=tk.LEFT)
        self.time_display_label = tk.Label(title_area, textvariable=self.current_time,
                                           bg=bg, fg=COLORS["accent_secondary"],
                                           font=("Segoe UI", 10))
        self.time_display_label.pack(side=tk.RIGHT)

        # ---- Risk Gauge ----
        self._build_risk_gauge(main_frame)

        # ---- Live Context Card ----
        self._build_card(main_frame, "Live Context", self._build_context_content)

        # ---- Safety Questions Card ----
        self._build_card(main_frame, "Safety Questions (Check all that apply)",
                         self._build_questions_content)

        # ---- Confidence Card ----
        self._build_card(main_frame, "Safety Confidence",
                         self._build_confidence_content)

        # ---- Timer Card ----
        self._build_card(main_frame, "Check-in Timer",
                         self._build_timer_content)

        # ---- Notes Card ----
        self._build_card(main_frame, "Notes",
                         self._build_notes_content)

        # ---- Analyze Button ----
        analyze_btn = styled_button(main_frame, text="Analyze Safety",
                                     bg=COLORS["btn_primary"],
                                     fg=COLORS["btn_text"],
                                     font=("Segoe UI", 14, "bold"),
                                     hover_bg=COLORS["btn_hover"],
                                     on_click=self.run_analysis,
                                     padx=20, pady=16)
        analyze_btn.pack(fill=tk.X, pady=(8, 4))

        # ---- Results Area ----
        results_card = tk.Frame(main_frame, bg=card_bg, padx=14, pady=12)
        results_card.pack(fill=tk.BOTH, expand=True, pady=4)

        tk.Label(results_card, text="Results", bg=card_bg,
                 fg=COLORS["accent_secondary"], font=("Segoe UI", 11, "bold")).pack(anchor="w")

        self.results_text = tk.Text(results_card, height=6, bg=COLORS["bg_tertiary"],
                                    fg=COLORS["text_primary"],
                                    font=("Segoe UI", 10), relief="flat", bd=0,
                                    wrap=tk.WORD, padx=10, pady=10,
                                    insertbackground=COLORS["accent_primary"])
        self.results_text.pack(fill=tk.BOTH, expand=True, pady=(4, 0))
        self.results_text.insert("1.0", "Run an analysis to see your risk assessment.")
        self.results_text.configure(state="disabled")

        # ---- Action Buttons ----
        btn_bar = tk.Frame(main_frame, bg=bg, pady=8)
        btn_bar.pack(fill=tk.X)

        action_btns = [
            ("View SOS Draft", self.view_sos_draft),
            ("Send SOS Email", self.send_sos_email_demo),
            ("Contacts", self.view_contacts),
            ("Edit Contacts", self.edit_contacts),
        ]
        for label, cmd in action_btns:
            b = styled_button(btn_bar, text=label,
                              bg=COLORS["bg_secondary"],
                              fg=COLORS["text_secondary"],
                              font=("Segoe UI", 9),
                              hover_bg=COLORS["bg_tertiary"],
                              on_click=cmd,
                              padx=12, pady=6)
            b.pack(side=tk.LEFT, padx=2)

    def _build_risk_gauge(self, parent):
        """Circular risk gauge that updates after analysis."""
        card_bg = COLORS["card_bg"]
        frame = tk.Frame(parent, bg=card_bg, padx=10, pady=8)
        frame.pack(fill=tk.X, pady=4)

        self.gauge_canvas = tk.Canvas(frame, width=100, height=100,
                                      bg=card_bg, highlightthickness=0)
        self.gauge_canvas.pack(side=tk.LEFT, padx=(0, 14))

        self.gauge_canvas.create_oval(10, 10, 90, 90, fill=COLORS["bg_tertiary"],
                                      outline=COLORS["border"], width=2)
        self.gauge_arc = self.gauge_canvas.create_arc(10, 10, 90, 90,
                                                       start=90, extent=0,
                                                       fill=COLORS["accent_primary"],
                                                       outline="")
        self.gauge_canvas.create_oval(25, 25, 75, 75, fill=card_bg, outline=card_bg)
        self.gauge_score = self.gauge_canvas.create_text(50, 44, text="--",
                                                          fill=COLORS["text_primary"],
                                                          font=("Segoe UI", 18, "bold"))
        self.gauge_label = self.gauge_canvas.create_text(50, 66, text="Score",
                                                          fill=COLORS["text_muted"],
                                                          font=("Segoe UI", 8))

        info_frame = tk.Frame(frame, bg=card_bg)
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.gauge_level_text = tk.Label(info_frame, text="Not analyzed",
                                         bg=card_bg, fg=COLORS["text_secondary"],
                                         font=("Segoe UI", 13, "bold"))
        self.gauge_level_text.pack(anchor="w")

        self.gauge_trend_text = tk.Label(info_frame, text="",
                                         bg=card_bg, fg=COLORS["text_muted"],
                                         font=("Segoe UI", 9))
        self.gauge_trend_text.pack(anchor="w")

        self.gauge_advice_text = tk.Label(info_frame, text="Answer safety questions and click Analyze",
                                          bg=card_bg, fg=COLORS["text_muted"],
                                          font=("Segoe UI", 9), wraplength=350,
                                          justify="left")
        self.gauge_advice_text.pack(anchor="w", pady=(4, 0))

        # Location row
        loc_row = tk.Frame(frame, bg=card_bg)
        loc_row.pack(fill=tk.X, pady=(6, 0))

        self.gauge_location_label = tk.Label(loc_row, textvariable=self.current_location,
                                              bg=card_bg, fg=COLORS["text_primary"],
                                              font=("Segoe UI", 10), anchor="w")
        self.gauge_location_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        styled_button(loc_row, text="Update Location",
                      bg=COLORS["bg_tertiary"],
                      fg=COLORS["text_secondary"],
                      font=("Segoe UI", 8),
                      hover_bg=COLORS["bg_secondary"],
                      on_click=self.fetch_location_from_gps,
                      padx=8, pady=3).pack(side=tk.RIGHT)

    def _build_card(self, parent, title, content_fn):
        """Create a styled card section."""
        card_bg = COLORS["card_bg"]
        card = tk.Frame(parent, bg=card_bg, padx=14, pady=10)
        card.pack(fill=tk.X, pady=4)

        tk.Label(card, text=title, bg=card_bg,
                 fg=COLORS["accent_secondary"],
                 font=("Segoe UI", 11, "bold")).pack(anchor="w")

        content_fn(card)

    def _build_context_content(self, parent):
        card_bg = COLORS["card_bg"]
        row = tk.Frame(parent, bg=card_bg)
        row.pack(fill=tk.X, pady=4)

        styled_button(row, text="Approx Location",
                      bg=COLORS["bg_tertiary"],
                      fg=COLORS["text_secondary"],
                      font=("Segoe UI", 9),
                      hover_bg=COLORS["bg_secondary"],
                      on_click=self.fetch_location_from_gps,
                      padx=10, pady=5).pack(side=tk.LEFT, padx=2)
        styled_button(row, text="Precise GPS",
                      bg=COLORS["bg_tertiary"],
                      fg=COLORS["text_secondary"],
                      font=("Segoe UI", 9),
                      hover_bg=COLORS["bg_secondary"],
                      on_click=self.start_precise_location_capture,
                      padx=10, pady=5).pack(side=tk.LEFT, padx=2)

    def _build_questions_content(self, parent):
        card_bg = COLORS["card_bg"]
        question_texts = [
            ("isolated", "I am in an isolated area"),
            ("poor_lighting", "The area has poor lighting"),
            ("late_night", "It is late at night"),
            ("followed", "I feel like someone is following/watching me"),
            ("low_battery", "My phone battery is below 20%"),
            ("crowded", "I am in a crowded but non-protective environment"),
        ]
        for key, text in question_texts:
            var = self.questions[key]
            row = tk.Frame(parent, bg=card_bg)
            row.pack(fill=tk.X, pady=1)
            cb = tk.Checkbutton(row, text=text, variable=var,
                                bg=card_bg, fg=COLORS["text_secondary"],
                                selectcolor=COLORS["bg_tertiary"],
                                activebackground=card_bg,
                                activeforeground=COLORS["accent_primary"],
                                font=("Segoe UI", 10),
                                bd=0, highlightthickness=0,
                                relief="flat")
            cb.pack(anchor="w")

    def _build_confidence_content(self, parent):
        card_bg = COLORS["card_bg"]
        self.confidence_display = tk.Label(parent, text="3 - Moderate",
                                            bg=card_bg, fg=COLORS["warning"],
                                            font=("Segoe UI", 18, "bold"))
        self.confidence_display.pack(pady=4)

        # Confidence bar
        bar_frame = tk.Frame(parent, bg=card_bg, height=32)
        bar_frame.pack(fill=tk.X, pady=(4, 8))
        bar_frame.pack_propagate(False)

        segments = [
            ("Very Low", COLORS["critical"]),
            ("Low", COLORS["danger"]),
            ("Moderate", COLORS["warning"]),
            ("Good", COLORS["accent_primary"]),
            ("High", COLORS["success"]),
        ]
        self.confidence_segments = []
        for i, (label, color) in enumerate(segments):
            seg = tk.Label(bar_frame, text=label, bg=COLORS["bg_tertiary"],
                           fg=COLORS["text_muted"], font=("Segoe UI", 7),
                           width=10)
            seg.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=1)
            seg.bind("<Button-1>", lambda e, v=i+1: self._set_confidence(v))
            self.confidence_segments.append(seg)

        self._highlight_confidence(3)

    def _highlight_confidence(self, val):
        colors = [COLORS["critical"], COLORS["danger"], COLORS["warning"],
                  COLORS["accent_primary"], COLORS["success"]]
        labels = {
            1: "1 - Very Uncertain", 2: "2 - Uncertain", 3: "3 - Moderate",
            4: "4 - Confident", 5: "5 - Very Confident"
        }
        for i, seg in enumerate(self.confidence_segments):
            if i == val - 1:
                seg.configure(bg=colors[i], fg="#FFFFFF")
            else:
                seg.configure(bg=COLORS["bg_tertiary"], fg=COLORS["text_muted"])
        self.confidence_display.configure(text=labels.get(val, str(val)),
                                          fg=colors[val-1])

    def _set_confidence(self, val):
        self.confidence.set(val)
        self._highlight_confidence(val)

    def _build_timer_content(self, parent):
        card_bg = COLORS["card_bg"]
        self.timer_display = tk.Label(parent, text="00:00",
                                       bg=card_bg, fg=COLORS["text_primary"],
                                       font=("Segoe UI", 28, "bold"))
        self.timer_display.pack(pady=4)

        # Timer progress bar
        self.timer_bar = ttk.Progressbar(parent, style="TProgressbar",
                                         length=400, mode="determinate")
        self.timer_bar.pack(fill=tk.X, pady=(0, 8))

        # Duration label
        self.timer_duration_label = tk.Label(parent,
                                              text=self.format_timer_duration(
                                                  self.timer_seconds.get()),
                                              bg=card_bg, fg=COLORS["text_muted"],
                                              font=("Segoe UI", 9))
        self.timer_duration_label.pack()

        # Slider
        slider_row = tk.Frame(parent, bg=card_bg)
        slider_row.pack(fill=tk.X, pady=4)

        tk.Label(slider_row, text="Duration:", bg=card_bg,
                 fg=COLORS["text_muted"], font=("Segoe UI", 9)).pack(side=tk.LEFT)

        self.timer_slider = tk.Scale(slider_row, from_=TIMER_MIN_SECONDS,
                                     to=TIMER_MAX_SECONDS,
                                     orient=tk.HORIZONTAL, bg=card_bg,
                                     fg=COLORS["accent_primary"],
                                     troughcolor=COLORS["bg_tertiary"],
                                     highlightbackground=card_bg,
                                     variable=self.timer_seconds,
                                     command=self.on_timer_slider_change,
                                     length=200, showvalue=False)
        self.timer_slider.pack(side=tk.LEFT, padx=8, fill=tk.X, expand=True)

        # Start/Stop button
        self.timer_button = styled_button(parent, text="Start Timer",
                                           bg=COLORS["btn_primary"],
                                           fg=COLORS["btn_text"],
                                           font=("Segoe UI", 11, "bold"),
                                           hover_bg=COLORS["btn_hover"],
                                           on_click=self.toggle_timer,
                                           padx=16, pady=10)
        self.timer_button.pack(pady=6)

    def _build_notes_content(self, parent):
        card_bg = COLORS["card_bg"]
        self.notes_entry = tk.Entry(parent, textvariable=self.notes,
                                     bg=COLORS["bg_tertiary"],
                                     fg=COLORS["text_primary"],
                                     font=("Segoe UI", 10), relief="flat",
                                     bd=0, insertbackground=COLORS["accent_primary"])
        self.notes_entry.pack(fill=tk.X, ipady=6, pady=4)

    def _get_user_profile(self):
        """Fetch the logged-in user's profile from users.json."""
        users = load_users()
        profile = users.get(self.username, {})
        if isinstance(profile, dict):
            return profile
        return {}

    def logout(self):
        """Return to auth screen"""
        self.stop_timer()
        self.root.destroy()
        if self.on_logout:
            self.on_logout()

    def check_night_warning(self):
        """Check if current time is late night and show warning"""
        hour = datetime.datetime.now().hour
        if hour >= 22 or hour < 6:
            messagebox.showwarning(
                "Night Time Warning",
                "It is late at night. Please be extra cautious and "
                "ensure you are in a safe location.",
            )
            # Auto-check late night question
            self.questions["late_night"].set(True)

    def update_local_time_display(self):
        """Refresh local time label immediately."""
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.current_time.set(now)

    def update_local_time(self):
        """Keep local time updated every second."""
        self.update_local_time_display()
        self.root.after(1000, self.update_local_time)

    def prompt_location_permission(self):
        """Ask user permission before approximate GPS lookup."""
        allow = messagebox.askyesno(
            "Location Access",
            "Allow shieldHer to fetch your approximate location using internet GPS/IP?",
        )
        if allow:
            self.fetch_location_from_gps()

    def fetch_location_from_gps(self):
        """Fetch approximate location from public IP geolocation service."""
        try:
            with urllib.request.urlopen(LOCATION_API_URL, timeout=8) as response:
                data = json.loads(response.read().decode("utf-8"))

            city = data.get("city", "")
            region = data.get("region", "")
            country = data.get("country_name", "")
            lat = data.get("latitude")
            lon = data.get("longitude")

            parts = [p for p in [city, region, country] if p]
            location_text = (
                ", ".join(parts) if parts else "Approximate location unavailable"
            )
            if lat is not None and lon is not None:
                location_text = f"{location_text} (Lat {lat}, Lon {lon})"

            self.current_location.set(location_text)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            self.current_location.set("Unable to fetch location (network unavailable)")
            messagebox.showwarning(
                "Location Unavailable",
                "Could not fetch location right now. You can continue using the app.",
            )

    def start_precise_location_capture(self):
        """Capture precise GPS location via browser geolocation API."""
        if self.gps_request_running:
            messagebox.showinfo(
                "Precise GPS",
                "Precise location capture is already running.",
            )
            return

        allow = messagebox.askyesno(
            "Precise GPS Access",
            "A browser tab will open to request GPS permission. Continue?",
        )
        if not allow:
            return

        self.gps_request_running = True
        self.current_location.set("Waiting for precise GPS permission in browser...")
        threading.Thread(target=self._run_precise_location_server, daemon=True).start()

    def _run_precise_location_server(self):
        """Run a one-time localhost listener to receive browser geolocation."""
        token = hashlib.sha256(
            f"{time.time()}-{self.username}".encode("utf-8")
        ).hexdigest()[:16]
        result = {
            "done": False,
            "error": "",
            "lat": None,
            "lon": None,
            "accuracy": None,
        }

        html_page = f"""<!doctype html>
<html>
<head><meta charset=\"utf-8\"><title>shieldHer GPS</title></head>
<body style=\"font-family:Arial,sans-serif;padding:20px\">
  <h3>shieldHer GPS Permission</h3>
  <p id=\"status\">Requesting precise location...</p>
  <script>
    const params = new URLSearchParams(window.location.search);
    const token = params.get('token') || '';
    function done(msg) {{ document.getElementById('status').textContent = msg; }}
    function sendPosition(pos) {{
      const payload = {{
        token: token,
        lat: pos.coords.latitude,
        lon: pos.coords.longitude,
        accuracy: pos.coords.accuracy
      }};
      fetch('/submit', {{
        method: 'POST',
        headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify(payload)
      }})
      .then(() => done('Location captured. You can close this tab.'))
      .catch(() => done('Failed to send location to app.'));
    }}
    function onError(err) {{
      done('Location error: ' + err.message);
    }}
    if (!navigator.geolocation) {{
      done('Geolocation is not supported by this browser.');
    }} else {{
      navigator.geolocation.getCurrentPosition(sendPosition, onError, {{
        enableHighAccuracy: true,
        timeout: 15000,
        maximumAge: 0
      }});
    }}
  </script>
</body>
</html>"""

        class GeoHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(html_page.encode("utf-8"))

            def do_POST(self):
                if self.path != "/submit":
                    self.send_response(404)
                    self.end_headers()
                    return

                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    payload = self.rfile.read(length)
                    data = json.loads(payload.decode("utf-8"))
                    if data.get("token") != token:
                        raise ValueError("Token mismatch")

                    result["lat"] = float(data.get("lat"))
                    result["lon"] = float(data.get("lon"))
                    result["accuracy"] = float(data.get("accuracy", 0))
                    result["done"] = True
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b"ok")
                except Exception as exc:
                    result["error"] = str(exc)
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b"bad request")

            def log_message(self, format_str, *args):
                return

        try:
            with socketserver.TCPServer(("127.0.0.1", 0), GeoHandler) as server:
                server.timeout = 1
                port = server.server_address[1]
                url = f"http://127.0.0.1:{port}/?token={token}"
                self.root.after(0, lambda: webbrowser.open_new(url))

                deadline = time.time() + 60
                while (
                    time.time() < deadline
                    and not result["done"]
                    and not result["error"]
                ):
                    server.handle_request()

                if result["done"]:
                    lat = result["lat"]
                    lon = result["lon"]
                    accuracy = result["accuracy"]
                    address = self._reverse_geocode(lat, lon)
                    location_text = self._format_precise_location(
                        lat, lon, accuracy, address
                    )
                    self.root.after(0, lambda: self.current_location.set(location_text))
                elif result["error"]:
                    self.root.after(
                        0,
                        lambda: messagebox.showwarning(
                            "Precise GPS",
                            f"Could not capture precise location: {result['error']}",
                        ),
                    )
                    self.root.after(
                        0,
                        lambda: self.current_location.set(
                            "Precise GPS capture failed; use approximate location instead"
                        ),
                    )
                else:
                    self.root.after(
                        0,
                        lambda: messagebox.showwarning(
                            "Precise GPS",
                            "Timed out waiting for browser location permission.",
                        ),
                    )
                    self.root.after(
                        0,
                        lambda: self.current_location.set(
                            "Precise GPS capture timed out; use approximate location instead"
                        ),
                    )
        finally:
            self.root.after(0, self._mark_gps_request_done)

    def _mark_gps_request_done(self):
        self.gps_request_running = False

    def _reverse_geocode(self, lat, lon):
        """Best-effort reverse geocoding for GPS coordinates."""
        try:
            url = (
                "https://nominatim.openstreetmap.org/reverse?format=jsonv2"
                f"&lat={lat}&lon={lon}"
            )
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "shieldHer/1.0"},
            )
            with urllib.request.urlopen(request, timeout=8) as response:
                data = json.loads(response.read().decode("utf-8"))
            return data.get("display_name", "")
        except Exception:
            return ""

    def _format_precise_location(self, lat, lon, accuracy, address):
        """Format precise location text with optional address details."""
        parts = []
        if address:
            parts.append(address)
        parts.append(f"Lat {lat:.6f}, Lon {lon:.6f}")
        if accuracy and accuracy > 0:
            parts.append(f"Accuracy +/- {int(accuracy)} m")
        return " | ".join(parts)

    def format_timer_duration(self, seconds):
        """Format timer duration for display"""
        if seconds >= 60:
            mins = seconds // 60
            secs = seconds % 60
            if secs == 0:
                return f"{mins} minute{'s' if mins > 1 else ''}"
            return f"{mins}m {secs}s"
        return f"{seconds} seconds"

    def on_timer_slider_change(self, value):
        """Handle timer slider change"""
        secs = int(float(value))
        self.timer_duration_label.configure(text=self.format_timer_duration(secs))
        if self.timer_running:
            self.stop_timer()
            self.start_timer()

    def toggle_timer(self):
        """Toggle timer on/off"""
        if self.timer_running:
            self.stop_timer()
        else:
            self.start_timer()

    def start_timer(self):
        """Start the countdown timer"""
        self.timer_seconds.get()
        self.timer_remaining = self.timer_seconds.get()
        self.timer_running = True
        self.timer_button.config(text="Stop Timer", bg=COLORS["danger"])
        self.timer_bar["value"] = 100
        self.timer_expired = 0
        # Rebind hover for danger state
        self.timer_button.unbind("<Enter>")
        self.timer_button.unbind("<Leave>")
        self.timer_button.bind("<Enter>", lambda e: self.timer_button.configure(bg="#FF6666"))
        self.timer_button.bind("<Leave>", lambda e: self.timer_button.configure(bg=COLORS["danger"]))

        self.timer_thread = threading.Thread(target=self.timer_countdown)
        self.timer_thread.daemon = True
        self.timer_thread.start()

    def stop_timer(self):
        """Stop the countdown timer"""
        self.timer_running = False
        self.timer_button.config(text="Start Timer", bg=COLORS["btn_primary"])
        self.timer_bar["value"] = 0
        # Restore normal hover
        self.timer_button.unbind("<Enter>")
        self.timer_button.unbind("<Leave>")
        self.timer_button.bind("<Enter>", lambda e: self.timer_button.configure(bg=COLORS["btn_hover"]))
        self.timer_button.bind("<Leave>", lambda e: self.timer_button.configure(bg=COLORS["btn_primary"]))

    def timer_countdown(self):
        """Countdown timer thread"""
        total = self.timer_seconds.get()
        while self.timer_remaining > 0 and self.timer_running:
            mins = self.timer_remaining // 60
            secs = self.timer_remaining % 60
            pct = (self.timer_remaining / total) * 100
            self.root.after(0, self.update_timer_display, mins, secs, pct)
            time.sleep(1)
            self.timer_remaining -= 1

        if self.timer_running and self.timer_remaining <= 0:
            self.timer_expired = 1
            self.root.after(0, self.on_timer_expired)

    def update_timer_display(self, mins, secs, pct):
        """Update timer display and progress bar"""
        self.timer_display.config(text=f"{mins:02d}:{secs:02d}")
        self.timer_bar["value"] = pct
        # Color the bar based on remaining
        if pct > 50:
            self.timer_display.config(fg=COLORS["text_primary"])
        elif pct > 25:
            self.timer_display.config(fg=COLORS["warning"])
        else:
            self.timer_display.config(fg=COLORS["danger"])

    def on_timer_expired(self):
        """Handle timer expiration"""
        self.timer_display.config(text="EXPIRED!", fg=COLORS["critical"])
        self.timer_button.config(text="Start Timer", bg=COLORS["btn_primary"])
        self.timer_running = False
        self.timer_bar["value"] = 0
        self.timer_button.unbind("<Enter>")
        self.timer_button.unbind("<Leave>")
        self.timer_button.bind("<Enter>", lambda e: self.timer_button.configure(bg=COLORS["btn_hover"]))
        self.timer_button.bind("<Leave>", lambda e: self.timer_button.configure(bg=COLORS["btn_primary"]))

        messagebox.showwarning(
            "Timer Expired!",
            "Your check-in timer has expired. Please contact someone you trust!",
        )

    def write_input_file(self):
        """Write the input file for the C analyzer"""
        try:
            # Write timer in seconds (primary) and minutes (fallback for backward compat)
            timer_seconds = self.timer_seconds.get()
            timer_minutes = max(1, timer_seconds // 60)

            with open(self.INPUT_FILE, "w") as f:
                f.write(f"Q_ISOLATED={1 if self.questions['isolated'].get() else 0}\n")
                f.write(
                    f"Q_POOR_LIGHTING={1 if self.questions['poor_lighting'].get() else 0}\n"
                )
                f.write(
                    f"Q_LATE_NIGHT={1 if self.questions['late_night'].get() else 0}\n"
                )
                f.write(f"Q_FOLLOWED={1 if self.questions['followed'].get() else 0}\n")
                f.write(
                    f"Q_LOW_BATTERY={1 if self.questions['low_battery'].get() else 0}\n"
                )
                f.write(f"Q_CROWDED={1 if self.questions['crowded'].get() else 0}\n")
                f.write(f"CONFIDENCE={self.confidence.get()}\n")
                f.write(f"TIMER_SECONDS={timer_seconds}\n")
                f.write(f"TIMER_MINUTES={timer_minutes}\n")
                f.write(f"TIMER_EXPIRED={self.timer_expired}\n")
                f.write(f"CURRENT_LOCATION={self.current_location.get()}\n")
                f.write(f"LOCAL_TIME={self.current_time.get()}\n")
                f.write(f"NOTES={self.notes.get()}\n")
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to write input file: {e}")
            return False

    def read_output_file(self):
        """Read the output file from the C analyzer"""
        results = {}
        try:
            with open(self.OUTPUT_FILE, "r") as f:
                for line in f:
                    line = line.strip()
                    if "=" in line:
                        key, value = line.split("=", 1)
                        results[key] = value
            return results
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read output file: {e}")
            return None

    def run_analysis(self):
        """Run the safety analysis"""
        # Write input file
        if not self.write_input_file():
            return

        # Run C analyzer with user-specific paths
        try:
            result = subprocess.run(
                [
                    ANALYZER_BIN,
                    "-i",
                    self.INPUT_FILE,
                    "-o",
                    self.OUTPUT_FILE,
                    "-h",
                    self.HISTORY_FILE,
                    "-c",
                    self.CONTACTS_FILE,
                    "-s",
                    self.SOS_DRAFT_FILE,
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                messagebox.showerror("Error", f"Analyzer failed: {result.stderr}")
                return
        except FileNotFoundError:
            messagebox.showerror(
                "Error", "Analyzer not found. Please run 'make build' first."
            )
            return
        except subprocess.TimeoutExpired:
            messagebox.showerror("Error", "Analyzer timed out")
            return
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run analyzer: {e}")
            return

        # Read output
        output = self.read_output_file()
        if output is None:
            return

        # Display results
        self.display_results(output)

    def display_results(self, output):
        """Display analysis results with color coding and gauge update."""
        risk_score = int(output.get("RISK_SCORE", 0))
        risk_level = output.get("RISK_LEVEL", "unknown")
        trend = output.get("TREND", "stable")
        sos_needed = output.get("SOS_NEEDED", "0")
        advice = output.get("ADVICE", "No advice available")
        self.last_risk_score = risk_score

        level_colors = {
            "low": COLORS["success"],
            "medium": COLORS["warning"],
            "high": COLORS["danger"],
            "critical": COLORS["critical"],
        }
        level_color = level_colors.get(risk_level, COLORS["text_secondary"])

        # Update circular gauge
        self._update_gauge(risk_score, risk_level.capitalize(), level_color, trend, advice)

        # Build formatted result text
        advice_items = advice.split(";")
        result_text = f"Risk Score: {risk_score}/100\n"
        result_text += f"Risk Level: {risk_level.upper()}\n"
        result_text += f"Trend: {trend}\n\n"
        result_text += "Advice:\n"
        for item in advice_items:
            item = item.strip()
            if item:
                result_text += f"  \u2022 {item}\n"

        if sos_needed == "1":
            result_text += "\n[!] SOS RECOMMENDED - Review your SOS draft\n"

        self.results_text.configure(state="normal")
        self.results_text.delete("1.0", tk.END)
        self.results_text.insert("1.0", result_text)
        self.results_text.configure(state="disabled")

    def _update_gauge(self, score, level, color, trend, advice):
        """Update the circular gauge meter."""
        self.gauge_canvas.itemconfigure(self.gauge_arc, fill=color)
        extent = 360 * score / 100
        self.gauge_canvas.itemconfigure(self.gauge_arc, start=90-extent, extent=extent)
        self.gauge_canvas.itemconfigure(self.gauge_score, text=str(score))
        self.gauge_canvas.itemconfigure(self.gauge_label, text=f"{level} Risk")

        self.gauge_level_text.configure(text=f"{level} Risk (Score: {score}/100)", fg=color)

        trend_text = f"Trend: {trend.capitalize()}"
        trend_color = {"improving": COLORS["success"], "worsening": COLORS["danger"],
                       "stable": COLORS["text_muted"]}.get(trend, COLORS["text_muted"])
        self.gauge_trend_text.configure(text=trend_text, fg=trend_color)

        first_advice = advice.split(";")[0].strip() if advice else "No concerns"
        self.gauge_advice_text.configure(text=first_advice)

    def view_sos_draft(self):
        """View the SOS draft file"""
        if not os.path.exists(self.SOS_DRAFT_FILE):
            messagebox.showinfo(
                "SOS Draft", "No SOS draft available yet. Run an analysis first."
            )
            return

        try:
            with open(self.SOS_DRAFT_FILE, "r") as f:
                content = f.read()

            sos_window = tk.Toplevel(self.root)
            sos_window.title("SOS Draft")
            sos_window.geometry("520x420")
            sos_window.configure(bg=COLORS["bg_primary"])

            text = tk.Text(sos_window, bg=COLORS["bg_tertiary"],
                          fg=COLORS["text_primary"],
                          font=("Segoe UI", 10), relief="flat", bd=0,
                          padx=14, pady=14, wrap=tk.WORD)
            text.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)
            text.insert("1.0", content)
            text.configure(state=tk.DISABLED)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to read SOS draft: {e}")

    def view_contacts(self):
        """View trusted contacts"""
        if not os.path.exists(self.CONTACTS_FILE):
            messagebox.showinfo("Contacts", "No contacts file found.")
            return

        try:
            contacts_text = "Trusted Contacts:\n\n"
            with open(self.CONTACTS_FILE, "r") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        parts = line.split(",")
                        if len(parts) >= 2:
                            name = parts[0]
                            phone = parts[1]
                            email = (
                                parts[2] if len(parts) > 2 and parts[2] else "No email"
                            )
                            relation = parts[3] if len(parts) > 3 else "Contact"
                            contacts_text += f"{name} ({relation}): {phone} | {email}\n"

            messagebox.showinfo("Trusted Contacts", contacts_text)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to read contacts: {e}")

    def _normalize_indian_number(self, raw_number):
        """Normalize to +91XXXXXXXXXX for SMS provider."""
        digits = _to_indian_10_digits(raw_number)
        if not digits:
            return None
        return "+91" + digits

    def _load_contact_list(self):
        """Load trusted contacts from CSV-like contacts file."""
        contacts = []
        if not os.path.exists(self.CONTACTS_FILE):
            return contacts

        with open(self.CONTACTS_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = [p.strip() for p in line.split(",")]
                if len(parts) < 2:
                    continue
                name, phone = parts[0], parts[1]
                email = parts[2] if len(parts) > 2 else ""
                normalized = self._normalize_indian_number(phone)
                if normalized and _is_valid_email(email):
                    contacts.append((name, normalized, email))
        return contacts

    def _read_contacts_for_edit(self):
        """Read first 3 contacts for the edit dialog."""
        contacts = []
        if os.path.exists(self.CONTACTS_FILE):
            with open(self.CONTACTS_FILE, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    parts = [p.strip() for p in line.split(",")]
                    if len(parts) >= 2:
                        digits = _to_indian_10_digits(parts[1])
                        email = parts[2] if len(parts) > 2 else ""
                        contacts.append((parts[0], digits or parts[1], email))
                    if len(contacts) == 3:
                        break
        while len(contacts) < 3:
            contacts.append(("", "", ""))
        return contacts

    def edit_contacts(self):
        """Open editable trusted contacts dialog with dark theme."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Trusted Contacts")
        dialog.geometry("820x360")
        dialog.configure(bg=COLORS["bg_primary"])
        dialog.transient(self.root)
        dialog.grab_set()

        frame = tk.Frame(dialog, bg=COLORS["bg_primary"], padx=16, pady=14)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text="Edit up to 3 trusted contacts (name, 10-digit phone, email)",
                 bg=COLORS["bg_primary"], fg=COLORS["text_secondary"],
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 12))

        existing = self._read_contacts_for_edit()
        rows = []
        for i in range(3):
            row = tk.Frame(frame, bg=COLORS["bg_secondary"], padx=10, pady=6)
            row.pack(fill=tk.X, pady=3)
            tk.Label(row, text=f"Contact {i+1}:", bg=COLORS["bg_secondary"],
                     fg=COLORS["text_secondary"], font=("Segoe UI", 10, "bold"),
                     width=10, anchor="w").pack(side=tk.LEFT)
            name_var = tk.StringVar(value=existing[i][0] if existing[i][0] not in ("Name", "") else "")
            phone_var = tk.StringVar(value=existing[i][1] if existing[i][1] not in ("Phone", "") else "")
            email_var = tk.StringVar(value=existing[i][2] if existing[i][2] not in ("Email", "") else "")
            tk.Entry(row, textvariable=name_var, width=20, bg=COLORS["bg_tertiary"],
                     fg=COLORS["text_primary"], font=("Segoe UI", 10), relief="flat",
                     bd=0, insertbackground=COLORS["accent_primary"]).pack(side=tk.LEFT, padx=4, ipady=4)
            tk.Entry(row, textvariable=phone_var, width=16, bg=COLORS["bg_tertiary"],
                     fg=COLORS["text_primary"], font=("Segoe UI", 10), relief="flat",
                     bd=0, insertbackground=COLORS["accent_primary"]).pack(side=tk.LEFT, padx=4, ipady=4)
            tk.Entry(row, textvariable=email_var, width=24, bg=COLORS["bg_tertiary"],
                     fg=COLORS["text_primary"], font=("Segoe UI", 10), relief="flat",
                     bd=0, insertbackground=COLORS["accent_primary"]).pack(side=tk.LEFT, padx=4, ipady=4)
            rows.append((name_var, phone_var, email_var))

        def save_contacts():
            lines = []
            for idx, (name_var, phone_var, email_var) in enumerate(rows, start=1):
                name = name_var.get().strip()
                phone_raw = phone_var.get().strip()
                email = email_var.get().strip()
                if not name and not phone_raw and not email:
                    continue
                if not name or not phone_raw or not email:
                    messagebox.showerror("Invalid Contact",
                                         f"Contact {idx} requires name, phone, and email",
                                         parent=dialog)
                    return
                phone_digits = _to_indian_10_digits(phone_raw)
                if not phone_digits:
                    messagebox.showerror("Invalid Contact",
                                         f"Contact {idx} phone must be exactly 10 digits",
                                         parent=dialog)
                    return
                if not _is_valid_email(email):
                    messagebox.showerror("Invalid Contact",
                                         f"Contact {idx} email is invalid",
                                         parent=dialog)
                    return
                lines.append(f"{name},{phone_digits},{email},")

            with open(self.CONTACTS_FILE, "w") as f:
                for line in lines:
                    f.write(line + "\n")

            dialog.destroy()
            messagebox.showinfo("Saved", "Trusted contacts updated successfully")

        btn_row = tk.Frame(frame, bg=COLORS["bg_primary"])
        btn_row.pack(fill=tk.X, pady=(14, 0))
        save_btn = styled_button(btn_row, text="Save Changes",
                                  bg=COLORS["btn_primary"],
                                  fg=COLORS["btn_text"],
                                  font=("Segoe UI", 11, "bold"),
                                  hover_bg=COLORS["btn_hover"],
                                  on_click=save_contacts,
                                  padx=16, pady=10)
        save_btn.pack(side=tk.LEFT)
        styled_button(btn_row, text="Cancel",
                      bg=COLORS["bg_tertiary"],
                      fg=COLORS["text_secondary"],
                      font=("Segoe UI", 11),
                      hover_bg=COLORS["bg_secondary"],
                      on_click=dialog.destroy,
                      padx=16, pady=10).pack(side=tk.LEFT, padx=8)

    def _build_demo_email_message(self, recipient_name, recipient_email, subject, body):
        """Build mailto URL for a manual demo email send."""
        encoded_subject = urllib.parse.quote(subject, safe="")
        encoded_body = urllib.parse.quote(body, safe="")
        return f"mailto:{recipient_email}?subject={encoded_subject}&body={encoded_body}"

    def _try_send_email_smtp(self, recipient_name, recipient_email, subject, body):
        """Try sending email via SMTP if credentials are configured."""
        smtp_host = os.environ.get("SHIELDHER_SMTP_HOST", "").strip()
        smtp_port = int(os.environ.get("SHIELDHER_SMTP_PORT", "587"))
        smtp_user = os.environ.get("SHIELDHER_SMTP_USER", "").strip()
        smtp_pass = os.environ.get("SHIELDHER_SMTP_PASS", "").strip()
        sender = os.environ.get("SHIELDHER_SMTP_FROM", smtp_user).strip()

        if not (smtp_host and smtp_user and smtp_pass and sender):
            return False, "SMTP not configured"

        msg = EmailMessage()
        msg["From"] = sender
        msg["To"] = recipient_email
        msg["Subject"] = subject
        msg.set_content(body)

        with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)

        return True, "sent via SMTP"

    def send_sos_email_demo(self):
        """Send SOS through email (SMTP if configured, else mailto fallback)."""
        if not os.path.exists(self.SOS_DRAFT_FILE):
            messagebox.showinfo(
                "Send Email",
                "No SOS draft found yet. Run analysis first so draft can be generated.",
            )
            return

        contacts = self._load_contact_list()
        if not contacts:
            messagebox.showwarning(
                "Send Email",
                "No valid trusted contacts found with email.",
            )
            return

        with open(self.SOS_DRAFT_FILE, "r") as f:
            sos_text = f.read().strip()

        if not sos_text:
            messagebox.showwarning("Send Email", "SOS draft is empty.")
            return

        send_now = messagebox.askyesno(
            "Send Email (Demo)",
            "This will send SOS via SMTP if configured, else open mail drafts in your default email app. Continue?",
        )
        if not send_now:
            return

        subject = f"SOS ALERT: {self.full_name} needs help"
        message = f"SOS ALERT from {self.full_name}.\n\n{sos_text}"

        results = []
        for name, _, email in contacts[:3]:
            try:
                ok, detail = self._try_send_email_smtp(name, email, subject, message)
                if ok:
                    status = "SENT"
                else:
                    mailto_url = self._build_demo_email_message(
                        name, email, subject, message
                    )
                    webbrowser.open_new(mailto_url)
                    status = "DRAFT OPENED"
            except Exception as exc:
                status = f"FAILED ({exc})"
            results.append(f"{name} {email}: {status}")

        messagebox.showinfo(
            "Send Email (Demo)",
            "\n".join(results),
        )


def main():
    """Main entry point"""

    def show_auth_screen():
        auth_root = tk.Tk()

        def on_login_success(username):
            auth_root.destroy()
            show_safety_screen(username)

        AuthScreen(auth_root, on_login_success)
        auth_root.mainloop()

    def show_safety_screen(username):
        safety_root = tk.Tk()

        def on_logout():
            show_auth_screen()

        SafetyApp(safety_root, username, on_logout=on_logout)
        safety_root.mainloop()

    show_auth_screen()


if __name__ == "__main__":
    main()
