# ePub to Audio v2

Une application multiplateforme (macOS, Windows, Linux, Android) permettant de convertir des livres électroniques (ePub, PDF) en fichiers audio grâce à différents services de synthèse vocale.

## Fonctionnalités

- Conversion d'ePub (et bientôt PDF) en fichiers audio MP3
- Support de plusieurs services TTS :
  - Microsoft Edge TTS (toutes plateformes)
  - Google TTS (Android natif) #pas encore testé
  - Microsoft Azure (à venir)
  - Amazon Polly (à venir)
- Interface utilisateur moderne et responsive
- Thèmes multiples :
  - Normal
  - Mode nuit
  - Sépia
  - Bleu clair
  - Vert clair
  - Rouge clair
- Traitement par lots des chapitres
- Gestion des erreurs et tentatives multiples
- Affichage de la progression en temps réel
- Sélection de fichiers adaptée à chaque OS
- Test des voix avant conversion

## Prérequis

### Pour le développement

- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)
- virtualenv (recommandé)

### Dépendances principales

- Kivy 2.1.0
- pywebview 4.4.1
- edge-tts 6.1.9
- beautifulsoup4
- PyPDF2
- pdfminer.six

### Pour Android

- Android 5.0 (API 21) ou supérieur
- Permissions de stockage
- Buildozer pour la compilation

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

### Version Desktop (macOS, Windows, Linux)

1. Lancer l'application :
   ```bash
   python main.py
   ```

2. Sélectionner un fichier ePub ou PDF
3. Choisir un dossier de destination
4. Sélectionner le service TTS et la voix désirée
5. Tester la voix si souhaité
6. Cliquer sur "Analyser" pour extraire les chapitres
7. Cliquer sur "Convertir" pour démarrer la conversion

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
├── epub_processor.py    # Traitement des fichiers ePub/PDF
├── assets/             
│   └── index.html      # Interface utilisateur
├── requirements.txt     # Dépendances Python
└── buildozer.spec      # Configuration pour Android
```

## Développement

### Tests

Pour vérifier l'environnement de développement :
```bash
python -m pytest tests/
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

## Roadmap

- [ ] Support de Microsoft Azure TTS
- [ ] Support d'Amazon Polly
- [ ] Support de formats supplémentaires (MOBI, DOC, etc.)
- [ ] Interface de gestion des fichiers audio
- [ ] Support multilingue de l'interface
- [ ] Optimisation des performances
- [ ] Tests unitaires complets
