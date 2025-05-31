# NEAT-Based Autonomous Racing Agent

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python Version](https://img.shields.io/badge/Python-3.8%2B-blue.svg)
![Pygame](https://img.shields.io/badge/Pygame-2.6.1-green.svg)
![NEAT-Python](https://img.shields.io/badge/NEAT--Python-0.92-orange.svg)

# NEAT-Based Autonomous Racing Agent

## Description
Un agent de conduite autonome évolué via **NEAT-Python** dans un simulateur 2D développé avec **Pygame**. L’objectif est d’apprendre à une voiture virtuelle à boucler un circuit en un temps minimum tout en évitant les sorties de piste.

- **Capteurs (radars)** : 5 rayons orientés à –60°, –30°, 0°, +30°, +60° renvoyant la distance à la sortie de la piste.
- **Actions** : tourner à gauche, tourner à droite, accélérer, freiner (sorties du réseau).
- **Fitness** : récompense proportionnelle à la vitesse, bonus pour tour complet et nouveau meilleur temps, pénalité en cas de collision ou de vitesse trop faible.

- **Assets/** : images des circuits et sprite des voitures.
- **config.txt** : paramètres NEAT (pop_size, mutation, spéciation, etc.).
- **main.py** : initialise Pygame, crée la population NEAT, exécute la boucle d’évolution.
- **requirements.txt** : `neat-python==0.92`, `pygame==2.6.1`.

- **Assets/** : images des circuits et sprite de la voiture.
- **config.txt** : paramètres NEAT (pop_size, mutation, spéciation, etc.).
- **main.py** : initialise Pygame, crée la population NEAT, exécute la boucle d’évolution.
- **requirements.txt** : `neat-python==0.92`, `pygame==2.6.1`.

## Installation
1. Cloner le dépôt :
   ```bash
   git clone https://votre-repo.git
   cd votre-repo
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt

## Utilisation
   python main.py : 
    - Choisir un circuit en saisissant son numéro.
    - La fenêtre Pygame s’ouvre et l’évolution démarre (20 voitures/génération, jusqu’à 1000 générations ou fitness_threshold).
    - Regarder la console pour les statistiques (meilleur fitness, génération).

Auteurs

Benjamin Soyer 2A - ASR
Enzo Baita 2A - ASR
Ysabel Fallot 2A - ASR
Alexandre Vanicotte–Hochman 2A - ASR

Basé sur : https://github.com/MaxRohowsky/DriveAI



