from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
import os
from cryptography.fernet import Fernet
import secrets
import string

app = Flask(__name__)
db_path = os.path.join("instance", "password_manager.db")

# Charger la clé secrète (doit exister : secret.key à la racine)
KEY_FILE = "secret.key"
if not os.path.exists(KEY_FILE):
    raise SystemExit("Le fichier 'secret.key' est introuvable. Crée-le à la racine du projet avant de lancer l'application.")

with open(KEY_FILE, "rb") as f:
    key = f.read()
cipher = Fernet(key)

# Initialiser la base de données si elle n'existe pas
def init_db():
    os.makedirs("instance", exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS passwords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service TEXT NOT NULL,
            username TEXT,
            password BLOB NOT NULL,
            notes TEXT
        )
        """)
init_db()

def dict_from_row(row):
    """Convertit sqlite3.Row en dict simple (valeur bytes pour password)."""
    return {k: row[k] for k in row.keys()}

# Dashboard principal
@app.route('/')
def index():
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM passwords ORDER BY id DESC").fetchall()

    decrypted = []
    for r in rows:
        d = dict_from_row(r)
        try:
            # password stocké en BLOB (bytes)
            decrypted_password = cipher.decrypt(d["password"]).decode()
        except Exception:
            decrypted_password = "<erreur décryptage>"
        d["password"] = decrypted_password
        decrypted.append(d)

    return render_template('index.html', passwords=decrypted)

# Ajouter un mot de passe
@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        service = request.form.get('service', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        notes = request.form.get('notes', '').strip()

        if not service or not password:
            return "Service et password requis", 400

        encrypted_password = cipher.encrypt(password.encode())

        with sqlite3.connect(db_path) as conn:
            conn.execute(
                "INSERT INTO passwords (service, username, password, notes) VALUES (?, ?, ?, ?)",
                (service, username, encrypted_password, notes)
            )
        return redirect(url_for('index'))

    return render_template('add_edit.html', action="Ajouter", data={})

# Modifier un mot de passe
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM passwords WHERE id = ?", (id,)).fetchone()

    if not row:
        return "Entrée non trouvée", 404

    if request.method == 'POST':
        service = request.form.get('service', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        notes = request.form.get('notes', '').strip()

        if not service or not password:
            return "Service et password requis", 400

        encrypted_password = cipher.encrypt(password.encode())

        with sqlite3.connect(db_path) as conn:
            conn.execute(
                "UPDATE passwords SET service=?, username=?, password=?, notes=? WHERE id=?",
                (service, username, encrypted_password, notes, id)
            )
        return redirect(url_for('index'))

    # Pré-remplir le formulaire avec le mot de passe déchiffré
    try:
        pwd_plain = cipher.decrypt(row["password"]).decode()
    except Exception:
        pwd_plain = ""
    data = {
        "service": row["service"],
        "username": row["username"],
        "password": pwd_plain,
        "notes": row["notes"]
    }
    return render_template('add_edit.html', action="Modifier", data=data)

# Supprimer un mot de passe
@app.route('/delete/<int:id>')
def delete(id):
    with sqlite3.connect(db_path) as conn:
        conn.execute("DELETE FROM passwords WHERE id = ?", (id,))
    return redirect(url_for('index'))

# Route API pour générer un mot de passe sécurisé
@app.route('/generate_password', methods=['POST'])
def generate_password():
    """
    Génère un mot de passe sécurisé.
    JSON body: {"length": <int>}
    Réponse: {"password": "<mot_de_passe>"}
    """
    try:
        data = request.get_json(force=True) or {}
        length = int(data.get('length', 16))
    except Exception:
        length = 16

    length = max(4, min(128, length))
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+[]{};:,.<>?/"
    pwd = ''.join(secrets.choice(alphabet) for _ in range(length))
    return jsonify({"password": pwd})

if __name__ == '__main__':
    app.run(debug=True)