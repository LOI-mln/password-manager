import webview
from threading import Thread
from app import app

def start_flask():
    app.run(host="127.0.0.1", port=5000, debug=False)

if __name__ == '__main__':
    # Démarrage de Flask dans un thread séparé
    t = Thread(target=start_flask, daemon=True)
    t.start()

    # Création d'une fenêtre native
    window = webview.create_window(
        "Gestionnaire de mots de passe",
        "http://127.0.0.1:5000/",
        width=1000,
        height=700,
        resizable=True
    )

    # Lancement de la fenêtre
    webview.start()