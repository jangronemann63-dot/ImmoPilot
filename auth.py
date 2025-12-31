import sqlite3
import hashlib
import re
import smtplib
import random
import ssl
import json
from email.message import EmailMessage

DB_NAME = "users.db"
# Deine Zugangsdaten
SENDER_EMAIL = "jan.gronemann63@gmail.com"
SENDER_PASSWORD = "mzys hnen ahef iliq" 

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Tabelle Users
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            verification_code TEXT,
            is_verified INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabelle Watchlist
    c.execute('''
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT,
            objekt_id TEXT,
            title TEXT,
            price REAL,
            url TEXT,
            data_json TEXT, 
            status TEXT DEFAULT 'Neu',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# --- AUTH FUNKTIONEN ---

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def send_verification_email(to_email, code):
    subject = "Dein ImmoPilot Bestätigungscode"
    body = f"Dein Code: {code}"
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_email
    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)
        return True
    except Exception as e:
        print(f"Mail Fehler: {e}")
        return False

def initiate_registration(email, password):
    if not is_valid_email(email): return False, "Ungültige E-Mail."
    if len(password) < 6: return False, "Passwort zu kurz."
    code = str(random.randint(100000, 999999))
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute("INSERT OR REPLACE INTO users (email, password, verification_code, is_verified) VALUES (?, ?, ?, 0)", 
                  (email, hash_password(password), code))
        conn.commit()
        conn.close()
        if send_verification_email(email, code): return True, "Code gesendet."
        return False, "SMTP Fehler."
    except Exception as e:
        conn.close(); return False, f"DB Fehler: {e}"

def verify_user_code(email, code_input):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT verification_code FROM users WHERE email = ?", (email,))
    res = c.fetchone()
    if res and str(res[0]).strip() == str(code_input).strip():
        c.execute("UPDATE users SET is_verified = 1, verification_code = NULL WHERE email = ?", (email,))
        conn.commit(); conn.close()
        return True, "Erfolg!"
    conn.close(); return False, "Falscher Code."

def authenticate_user(email, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT password, is_verified FROM users WHERE email = ?", (email,))
    res = c.fetchone()
    conn.close()
    if res:
        if res[0] == hash_password(password):
            return (True, "Login ok") if res[1] else (False, "Nicht verifiziert.")
    return False, "Falsche Daten."

def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

# --- WATCHLIST FUNKTIONEN ---

def save_to_watchlist(email, listing_data):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id FROM watchlist WHERE user_email = ? AND objekt_id = ?", (email, listing_data['id']))
    if c.fetchone():
        conn.close(); return False, "Objekt schon vorhanden."
    try:
        c.execute('''
            INSERT INTO watchlist (user_email, objekt_id, title, price, url, data_json)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (email, listing_data['id'], listing_data['objektname'], listing_data['preis'], listing_data['url'], json.dumps(listing_data)))
        conn.commit(); conn.close()
        return True, "Gespeichert!"
    except Exception as e:
        conn.close(); return False, str(e)

def get_user_watchlist(email):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, title, price, url, data_json, created_at FROM watchlist WHERE user_email = ? ORDER BY created_at DESC", (email,))
    rows = c.fetchall()
    conn.close()
    results = []
    for r in rows:
        results.append({
            "db_id": r[0], "title": r[1], "price": r[2], "url": r[3],
            "data": json.loads(r[4]), "date": r[5]
        })
    return results

def delete_from_watchlist(db_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM watchlist WHERE id = ?", (db_id,))
    conn.commit(); conn.close()

# --- NEUE FUNKTION FÜR PDF UPDATES ---
def update_watchlist_entry(db_id, new_data_json):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute("UPDATE watchlist SET data_json = ? WHERE id = ?", (json.dumps(new_data_json), db_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.close()
        print(e)
        return False