<p align="center">
  <a href="https://www.econology.fr/?utm_source=github&utm_medium=readme&utm_campaign=vents_a21">
    <img src="docs/econology.png" alt="Econology, la qualité d'air au meilleur prix" width="302">
  </a>
</p>

# VMC double flux ECONOPRIME Connect dans Home Assistant

Pilotez et surveillez votre VMC double flux **ECONOPRIME Connect** (automate VENTS A21) depuis Home Assistant : températures des quatre flux d'air, rendement de récupération, vitesses, bypass, état des filtres, alarmes.

La liaison se fait en **Modbus TCP sur votre réseau local** (Wi-Fi ou Ethernet). Aucun cloud, aucun compte, aucun boîtier supplémentaire.

Une intégration proposée par [Econology](https://www.econology.fr/?utm_source=github&utm_medium=readme&utm_campaign=vents_a21), spécialiste français de la ventilation.

<p align="center">
  <img src="docs/tuile.png" alt="La tuile de tableau de bord : les quatre flux d'air colorés selon leur température, le rendement au centre, les vitesses en dessous" width="500">
</p>

## Machines compatibles

Toutes les VMC double flux ECONOPRIME équipées de l'automate A21 (gammes « Connect »), en vente sur econology.fr :

| Machine | Référence | Débit max | Fiche produit | Filtres de rechange |
|---|---|---|---|---|
| **Zephyr 240 S Connect** | ZEPH240A21 | 310 m³/h | [Voir](https://www.econology.fr/zephyr-240-connect-vmc-double-flux-zeph240a21-econoprime.html?utm_source=github&utm_medium=readme&utm_campaign=vents_a21) | [F7](https://www.econology.fr/filtre-f7-vmc-double-flux-zephyr-240-fzeph240f7-econoprime.html?utm_source=github&utm_medium=readme&utm_campaign=vents_a21) / [G4](https://www.econology.fr/filtre-g4-vmc-double-flux-zephyr-240-fzeph240g4-econoprime.html?utm_source=github&utm_medium=readme&utm_campaign=vents_a21) |
| **Zephyr 270 V Connect R** | 114800002 | 331 m³/h | [Voir](https://www.econology.fr/zephyr-270-connect-econoprime-vmc-double-flux-114800002.html?utm_source=github&utm_medium=readme&utm_campaign=vents_a21) | [F7](https://www.econology.fr/filtre-f7-zephyr-270-12300001-econoprime.html?utm_source=github&utm_medium=readme&utm_campaign=vents_a21) / [G4](https://www.econology.fr/filtre-g4-zephyr-270-12300002-econoprime.html?utm_source=github&utm_medium=readme&utm_campaign=vents_a21) |
| **Zephyr 550 V PH Connect R** | 114800003 | 720 m³/h | [Voir](https://www.econology.fr/vmc-double-flux-zephyr-550-v-ph-connect-r-econoprime-114800003.html?utm_source=github&utm_medium=readme&utm_campaign=vents_a21) | Sur la fiche produit |

Générations précédentes, toujours prises en charge :

| Machine | Référence | Débit max | Filtres de rechange |
|---|---|---|---|
| DF 180 Flat Connect | DFF18021 | 220 m³/h | [Voir](https://www.econology.fr/filtre-vmc-double-flux-df-180-econoprime.html?utm_source=github&utm_medium=readme&utm_campaign=vents_a21) |
| DF 270 Connect | DF27021 | 300 m³/h | [Voir](https://www.econology.fr/filtre-vmc-double-flux-df-270-econoprime.html?utm_source=github&utm_medium=readme&utm_campaign=vents_a21) |
| DF 350 Connect | DF35021 | 450 m³/h | [Voir](https://www.econology.fr/filtre-vmc-double-flux-df-350-econoprime.html?utm_source=github&utm_medium=readme&utm_campaign=vents_a21) |

Les autres machines à automate A21 (VENTS, Blauberg) utilisent la même table Modbus et devraient fonctionner : choisissez « Autre machine à automate A21 » à l'installation.

## Ce que vous obtenez

- **Une tuile prête à poser** sur votre tableau de bord, sans rien configurer : la machine vue de face, les quatre flux d'air colorés selon leur température réelle, le rendement de l'échangeur, les boutons de vitesse et la marche/arrêt.
- **Un rappel avant l'échéance des filtres**, avec le lien vers les bons filtres pour votre modèle.
- **Toutes les mesures dans l'historique** : air neuf, air soufflé, air extrait, air rejeté, humidité, CO₂, PM2.5 et COV si les sondes sont montées, régime et puissance des ventilateurs, ouverture du bypass, heures de fonctionnement.
- **Les commandes pour vos automatisations** : marche/arrêt, mode (ventilation, chauffage, rafraîchissement, automatique), vitesses 1 à 5 et vitesse manuelle, consigne de température, minuterie, programmation hebdomadaire, bypass forcé ouvert ou fermé pour le rafraîchissement nocturne.
- **Les alarmes** de la machine, avec leurs codes, et le bouton pour les acquitter.

Seules les sondes et options réellement présentes sur votre machine sont activées. Les autres restent disponibles, désactivées, dans la page de l'appareil.

## Installation

### 1. Préparer la machine

1. Raccordez la machine à votre réseau avec son application mobile (Wi-Fi) ou par câble Ethernet.
2. Relevez son adresse IP, dans l'application ou dans la liste des appareils de votre box.
3. Dans votre box, réservez-lui cette adresse (bail DHCP statique) pour qu'elle ne change plus.

La machine n'accepte **qu'une seule connexion Modbus TCP** par interface réseau. Si une GTB ou une autre domotique l'interroge déjà en Modbus TCP, Home Assistant ne pourra pas s'y connecter. De son côté, Home Assistant n'occupe la connexion que le temps de chaque lecture.

### 2. Installer l'intégration avec HACS

[![Ouvrir ce dépôt dans HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=floecono&repository=ha-vents-A21&category=integration)

Ou à la main : HACS, menu à trois points, **Dépôts personnalisés**, collez `https://github.com/floecono/ha-vents-A21`, type **Intégration**, puis installez « ECONOPRIME Connect (VENTS A21) » et redémarrez Home Assistant.

Sans HACS : copiez le dossier `custom_components/vents_a21` dans le dossier `custom_components` de votre Home Assistant, puis redémarrez.

### 3. Ajouter la machine

[![Ajouter l'intégration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=vents_a21)

Ou : **Paramètres**, **Appareils et services**, **Ajouter une intégration**, cherchez « ECONOPRIME ». Saisissez l'adresse IP et choisissez votre modèle. Le port (502) et l'adresse Modbus (1) sont dans les paramètres avancés, à ne modifier que si vous les avez changés sur la machine.

### 4. Poser la tuile

Sur votre tableau de bord : crayon en haut à droite, **Ajouter une carte**, cherchez « VMC ». La tuile trouve la machine toute seule. Rien à déclarer dans les ressources : elle est livrée avec l'intégration.

En YAML :

```yaml
type: custom:vents-a21-card
```

Avec plusieurs machines, précisez `device_id` (l'éditeur de la carte propose la liste) et, si vous voulez, `name` pour le titre.

## Bon à savoir

- **Rendement de récupération** : calculé côté air neuf, (air soufflé − air neuf) ÷ (air extrait − air neuf). Il n'est affiché que lorsqu'il a un sens : machine en marche, bypass fermé, pas de batterie de chauffage en action, et au moins 5 °C d'écart entre intérieur et extérieur.
- **Intervalle de lecture** : 15 secondes par défaut, réglable dans les options de l'intégration.
- **Réglages installateur** : la remise aux réglages d'usine, le mot de passe du menu ingénieur et les coefficients de régulation ne sont volontairement pas exposés.
- **Assistance** : dans la page de l'intégration, menu à trois points, **Télécharger les diagnostics**. Le fichier contient les registres bruts de la machine, sans son adresse IP : joignez-le à votre demande.

## État de la version 0.1.0

L'intégration est écrite d'après la table Modbus officielle de l'automate A21 (VENTS, document V55-8-1EN-02). Elle est vérifiée contre un simulateur de la machine, par une suite de tests automatiques et par un essai dans une instance Home Assistant. Elle n'a pas encore été validée sur une machine réelle : vos retours sont les bienvenus, [ouvrez un ticket](https://github.com/floecono/ha-vents-A21/issues) en joignant les diagnostics.

## Besoin de filtres, d'une sonde, d'un conseil ?

Filtres de rechange, sondes CO₂ et hygrométriques, batteries de préchauffage, conduits et bouches : tout est sur **[econology.fr](https://www.econology.fr/?utm_source=github&utm_medium=readme&utm_campaign=vents_a21)**, avec une équipe qui connaît ces machines.

## Pour les développeurs

```bash
pip install -r requirements_test.txt
pytest
```

`tests/simulator.py` est un simulateur Modbus TCP de l'automate A21, sans dépendance. Lancé seul (`python tests/simulator.py --port 5020`), il permet d'essayer l'intégration sans machine. Le client Modbus est embarqué dans l'intégration (`modbus.py`) pour ne dépendre d'aucune bibliothèque externe.

L'ordre des octets des registres composés (minuteries, version du micrologiciel) reprend celui documenté par le projet [pybls21](https://github.com/jvitkauskas/pybls21) pour l'automate Blauberg S21, de la même famille que l'A21.
