#!/bin/bash

# Activer l'environnement virtuel si disponible
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Installer les dépendances requises si nécessaire
pip install requests

# Lancer le serveur Django
python manage.py runserver 0.0.0.0:8000

