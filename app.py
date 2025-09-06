from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)

# Chemin vers la base SQLite
db_path = os.path.join("instance", "password_manager.db")

# Fonction pour initialiser la base si elle n'existe pas
def init_db():
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS passwords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service TEXT NOT NULL,
            username TEXT,
            password TEXT NOT NULL,
            notes TEXT
        )
        """)
init_db()
# Dashboard principal : liste tous les mots de passe
@app.route('/')
def index():
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        passwords = conn.execute("SELECT * FROM passwords").fetchall()
    return render_template('index.html', passwords=passwords)

# Ajouter un mot de passe
@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        service = request.form['service']
        username = request.form['username']
        password = request.form['password']
        notes = request.form['notes']
        with sqlite3.connect(db_path) as conn:
            conn.execute(
                "INSERT INTO passwords (service, username, password, notes) VALUES (?, ?, ?, ?)",
                (service, username, password, notes)
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
        with sqlite3.connect(db_path) as conn:
            conn.execute(
                "UPDATE passwords SET service=?, username=?, password=?, notes=? WHERE id=?",
                (service, username, password, notes, id)
            )
        return redirect(url_for('index'))
    return render_template('add_edit.html', action="Modifier", data=pwd)

# Supprimer un mot de passe
@app.route('/delete/<int:id>')
def delete(id):
    with sqlite3.connect(db_path) as conn:
        conn.execute("DELETE FROM passwords WHERE id = ?", (id,))
    return redirect(url_for('index'))