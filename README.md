# ePub to Audio

Une application multiplateforme (macOS, Android) permettant de convertir des livres électroniques (ePub) en fichiers audio grâce à différents services de synthèse vocale.

## Fonctionnalités

- Conversion d'ePub en fichiers audio MP3
- Support de plusieurs services TTS :
  - Microsoft Edge TTS (toutes plateformes)
  - Google TTS (Android natif)
- Interface utilisateur moderne et responsive
- Thèmes multiples (Normal, Nuit, Sépia, Bleu, Vert)
- Traitement par lots des chapitres
- Gestion des erreurs et tentatives multiples
- Affichage de la progression en temps réel

## Prérequis

### Pour le développement

- Python 3.10 ou supérieur
- pip (gestionnaire de paquets Python)
- virtualenv (recommandé)

### Pour Android

- Android 5.0 (API 21) ou supérieur
- Permissions de stockage

## Installation

1. Cloner le dépôt :
   ```bash
   git clone https://github.com/votre-username/epub-to-audio.git
   cd epub-to-audio
   ```

2. Créer et activer un environnement virtuel :
   ```bash
   # Windows
   python -m venv TTSenv
   TTSenv\Scripts\activate

   # macOS/Linux
   python -m venv TTSenv
   source TTSenv/bin/activate
   ```

3. Installer les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

## Utilisation

### Version Desktop (macOS)

1. Lancer l'application :
   ```bash
   python main.py
   ```

2. Sélectionner un fichier ePub
3. Choisir un dossier de destination
4. Sélectionner le service TTS et la voix désirée
5. Cliquer sur "Analyser" pour extraire les chapitres
6. Cliquer sur "Convertir" pour démarrer la conversion

### Version Android

1. Compiler l'application avec Buildozer :
   ```bash
   buildozer android debug
   ```

2. Installer l'APK généré sur votre appareil Android
3. Accorder les permissions de stockage demandées
4. Suivre les mêmes étapes que pour la version desktop

## Structure du projet

```
epub-to-audio/
├── main.py              # Point d'entrée de l'application
├── epub_processor.py    # Traitement des fichiers ePub
├── assets/             
│   └── index.html      # Interface utilisateur
├── requirements.txt     # Dépendances Python
└── buildozer.spec      # Configuration pour Android
```

## Développement

### Tests

Pour vérifier l'environnement de développement :
```bash
python test_env.py
```

### Compilation Android

1. Installer les dépendances de buildozer
2. Configurer buildozer.spec selon vos besoins
3. Lancer la compilation :
   ```bash
   buildozer android debug
   ```

## Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
- Signaler des bugs
- Proposer des améliorations
- Soumettre des pull requests

## Licence

[MIT License](LICENSE)

## Auteurs

- Votre nom (@votre-username)

## Remerciements

- Microsoft Edge TTS pour le service de synthèse vocale
- L'équipe Kivy pour le framework
- La communauté Python pour les différentes bibliothèques utilisées

## Futurs ajouts

- Intégration de nouveaux services TTS
- Amélioration de l'interface utilisateur
- Support pour d'autres formats de fichiers (ex: DOCX, TXT)
- Optimisation des performances sur Android
- Ajout de fonctionnalités de partage et de gestion des fichiers audio
