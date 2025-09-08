from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os
from cryptography.fernet import Fernet

app = Flask(__name__)
db_path = os.path.join("instance", "password_manager.db")

# Charger la clé secrète
with open("secret.key", "rb") as f:
    key = f.read()
cipher = Fernet(key)

# Initialiser la base de données si elle n'existe pas
def init_db():
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

# Dashboard principal
@app.route('/')
def index():
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        passwords = conn.execute("SELECT * FROM passwords").fetchall()

    # Déchiffrement avant affichage
    decrypted_passwords = []
    for pwd in passwords:
        decrypted_passwords.append({
            "id": pwd["id"],
            "service": pwd["service"],
            "username": pwd["username"],
            "password": cipher.decrypt(pwd["password"]).decode(),
            "notes": pwd["notes"]
        })
    return render_template('index.html', passwords=decrypted_passwords)

# Ajouter un mot de passe
@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        service = request.form['service']
        username = request.form['username']
        password = request.form['password']
        notes = request.form['notes']

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
        pwd = conn.execute("SELECT * FROM passwords WHERE id = ?", (id,)).fetchone()

    if request.method == 'POST':
        service = request.form['service']
        username = request.form['username']
        password = request.form['password']
        notes = request.form['notes']

        encrypted_password = cipher.encrypt(password.encode())

        with sqlite3.connect(db_path) as conn:
            conn.execute(
                "UPDATE passwords SET service=?, username=?, password=?, notes=? WHERE id=?",
                (service, username, encrypted_password, notes, id)
            )
        return redirect(url_for('index'))

    # Pré-remplir le formulaire avec le mot de passe déchiffré
    data = {
        "service": pwd["service"],
        "username": pwd["username"],
        "password": cipher.decrypt(pwd["password"]).decode(),
        "notes": pwd["notes"]
    }
    return render_template('add_edit.html', action="Modifier", data=data)

# Supprimer un mot de passe
@app.route('/delete/<int:id>')
def delete(id):
    with sqlite3.connect(db_path) as conn:
        conn.execute("DELETE FROM passwords WHERE id = ?", (id,))
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)