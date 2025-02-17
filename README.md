# AndroidAudiobookGen

Application pour convertir des ePubs en livres audio avec une interface graphique moderne.

## Prérequis

- Python 3.9 ou supérieur
- pip (gestionnaire de paquets Python)
- macOS (pour la version actuelle)

## Installation

1. Cloner le dépôt :
```bash
git clone [url-du-repo]
cd AndroidAudiobookGen
```

2. Créer un environnement virtuel (recommandé) :
```bash
python -m venv venv
source venv/bin/activate  # Sur macOS
```

3. Installer les dépendances :
```bash
pip install -r requirements.txt
```

## Lancement de l'application

```bash
python main.py
```

L'interface s'ouvrira dans une fenêtre de 360x650 pixels.

## Fonctionnalités

- Interface graphique moderne avec pywebview
- Conversion d'ePub en audio avec edge-tts
- Support des fichiers ePub
- Interface adaptative et responsive
- Icône d'application personnalisée

## Configuration requise

- **macOS** : PyObjC est requis et sera installé automatiquement
- **Python** : Version 3.9 ou supérieure requise pour la compatibilité avec PyObjC

## Dépendances principales

- Kivy 2.3.0 : Framework d'interface graphique
- pywebview 5.4+ : Composant webview natif
- edge-tts 6.1.9+ : Moteur de synthèse vocale
- PyObjC 11.0+ : Bindings Python pour macOS

## Notes de version

- Support complet de macOS
- Interface graphique optimisée (380x600)
- Icône d'application intégrée
- Compatibilité Python 3.9+

## Problèmes connus

Si vous rencontrez des problèmes d'installation :
1. Assurez-vous d'utiliser Python 3.9 ou supérieur
2. Sur macOS, vérifiez que PyObjC est correctement installé
3. En cas d'erreur avec pip, essayez de mettre à jour pip : `pip install --upgrade pip`
