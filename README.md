# Scan_Docker

Un outil d'analyse statique de sécurité (SAST) pour les environnements Docker.

Ce script Python analyse automatiquement les fichiers `Dockerfile` et `docker-compose.yml` pour détecter des mauvaises configurations de sécurité courantes avant le déploiement.

## Fonctionnalités

Le scanner vérifie les règles suivantes :

* **Permissions** : Détecte l'absence de l'instruction `USER` (exécution en tant que root).
* **Versionning** : Détecte l'utilisation du tag `:latest` ou l'absence de version explicite.
* **Secrets** : Identifie les mots de passe, clés API ou tokens laissés en clair dans les variables d'environnement.
* **Exclusions** : Permet d'ignorer des faux positifs via des commentaires.

## Prérequis

* Python 3.x
* Aucune dépendance externe requise (utilise uniquement la librairie standard).

## Installation

```bash
git clone [https://github.com/axel-g-dev/Scan_Docker.git](https://github.com/axel-g-dev/Scan_Docker.git)
cd Scan_Docker
```

Ensuite 

```python
python3 test.py
```
