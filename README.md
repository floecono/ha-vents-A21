<p align="center">
  <a href="https://www.econology.fr/?utm_source=github&utm_medium=readme&utm_campaign=vents_a21">
    <img src="https://raw.githubusercontent.com/floecono/ha-vents-A21/main/docs/econology.png" alt="Econology, la qualité d'air au meilleur prix" width="302">
  </a>
</p>

# VMC double flux ECONOPRIME Connect dans Home Assistant

Pilotez et surveillez votre VMC double flux **ECONOPRIME Connect** (automate VENTS A21) depuis Home Assistant : températures des quatre flux d'air, rendement de récupération, vitesses, bypass, état des filtres, alarmes.

La liaison se fait en **Modbus TCP sur votre réseau local** (Wi-Fi ou Ethernet). Aucun cloud, aucun compte, aucun boîtier supplémentaire.

Une intégration proposée par [Econology](https://www.econology.fr/?utm_source=github&utm_medium=readme&utm_campaign=vents_a21), spécialiste français de la ventilation.

<p align="center">
  <img src="https://raw.githubusercontent.com/floecono/ha-vents-A21/main/docs/tuile.png" alt="La tuile de tableau de bord : les quatre flux d'air colorés selon leur température, le rendement au centre, les vitesses en dessous" width="440">
</p>

## Machines compatibles

Toutes les VMC double flux ECONOPRIME équipées de l'automate A21 (gammes « Connect »), en vente sur econology.fr :

| Machine | Référence | Débit max | Fiche produit | Filtres de rechange |
|---|---|---|---|---|
| **Zephyr 240 S Connect** | ZEPH240A21 | 310 m³/h | [Voir](https://www.econology.fr/zephyr-240-connect-vmc-double-flux-zeph240a21-econoprime.html?utm_source=github&utm_medium=readme&utm_campaign=vents_a21) | [F7](https://www.econology.fr/filtre-f7-vmc-double-flux-zephyr-240-fzeph240f7-econoprime.html?utm_source=github&utm_medium=readme&utm_campaign=vents_a21) / [G4](https://www.econology.fr/filtre-g4-vmc-double-flux-zephyr-240-fzeph240g4-econoprime.html?utm_source=github&utm_medium=readme&utm_campaign=vents_a21) |
| **Zephyr 270 V Connect R** | 114800002 | 331 m³/h | [Voir](https://www.econology.fr/zephyr-270-connect-econoprime-vmc-double-flux-114800002.html?utm_source=github&utm_medium=readme&utm_campaign=vents_a21) | [F7](https://www.econology.fr/filtre-f7-zephyr-270-12300001-econoprime.html?utm_source=github&utm_medium=readme&utm_campaign=vents_a21) / [G4](https://www.econology.fr/filtre-g4-zephyr-270-12300002-econoprime.html?utm_source=github&utm_medium=readme&utm_campaign=vents_a21) |
| **Zephyr 550 V PH Connect R** | 114800003 | 720 m³/h | [Voir](https://www.econology.fr/vmc-double-flux-zephyr-550-v-ph-connect-r-econoprime-114800003.html?utm_source=github&utm_medium=readme&utm_campaign=vents_a21) | [F7](https://www.econology.fr/filtre-de-rechange-f7-pour-centrale-double-flux-zephyr-550-econoprime-123000004.html?utm_source=github&utm_medium=readme&utm_campaign=vents_a21) / [G4](https://www.econology.fr/filtre-de-rechange-g4-pour-centrale-double-flux-zephyr-550-econoprime-123000003.html?utm_source=github&utm_medium=readme&utm_campaign=vents_a21) |

Générations précédentes, toujours prises en charge :

| Machine | Référence | Débit max | Filtres de rechange |
|---|---|---|---|
| DF 180 Flat Connect | DFF18021 | 220 m³/h | [Voir](https://www.econology.fr/filtre-vmc-double-flux-df-180-econoprime.html?utm_source=github&utm_medium=readme&utm_campaign=vents_a21) |
| DF 270 Connect | DF27021 | 300 m³/h | [Voir](https://www.econology.fr/filtre-vmc-double-flux-df-270-econoprime.html?utm_source=github&utm_medium=readme&utm_campaign=vents_a21) |
| DF 350 Connect | DF35021 | 450 m³/h | [Voir](https://www.econology.fr/filtre-vmc-double-flux-df-350-econoprime.html?utm_source=github&utm_medium=readme&utm_campaign=vents_a21) |

Les autres machines à automate A21 (VENTS, Blauberg) utilisent la même table Modbus et devraient fonctionner : choisissez « Autre machine à automate A21 » à l'installation.

## Ce que vous obtenez

- **Une tuile prête à poser** sur votre tableau de bord, sans rien configurer : les quatre flux d'air colorés selon leur température réelle, le rendement de l'échangeur, la position du bypass (le flux dévié contourne l'échangeur sur le dessin), les boutons de vitesse et la marche/arrêt.
- **Une tuile « toutes les mesures »** pour ceux qui veulent tout voir : puissance, régime, débit et pression de chaque ventilateur, toutes les sondes, l'état de l'échangeur et des batteries, les entrées, l'entretien.
- **Les alarmes en clair** : les 46 codes de la machine sont traduits (« Défaut du ventilateur de soufflage », « Sonde de CO₂ non détectée »…), en distinguant les alarmes, qui arrêtent la machine, des simples avertissements.
- **Un rappel avant l'échéance des filtres**, 21 jours avant (délai réglable) puis à l'échéance. En option, la tuile ajoute le lien vers les bons filtres pour votre modèle.
- **Les réglages de l'application mobile** dans la page de l'appareil : puissance des ventilateurs de soufflage et d'extraction pour chaque vitesse, veille, boost et ses temporisations, seuils d'humidité et de qualité d'air, intervalle des filtres, minuterie, bascule hiver/été.
- **Toutes les mesures dans l'historique** et **toutes les commandes pour vos automatisations** : marche/arrêt, mode, vitesses 1 à 5 et vitesse manuelle, consigne, minuterie, programmation hebdomadaire, bypass forcé ouvert ou fermé pour le rafraîchissement nocturne.

### Tout ce que vous pouvez faire

Plus de 100 entités, deux tuiles, et tout passe par Modbus TCP en local, sans cloud. Les points marqués *(option)* dépendent des sondes et batteries montées sur la machine, ou d'un réglage à activer.

**Piloter**, depuis la tuile, la page de l'appareil ou vos automatisations

- Marche / arrêt et mode : **Ventilation** (récupération de chaleur seule, pas de régulation de température), **Chaud** (la machine vise la consigne par le haut : bypass et batterie d'appoint si elle existe), **Froid** (elle vise la consigne par le bas : bypass et refroidisseur s'il existe), **Automatique** (elle choisit). La logique du bypass est détaillée plus bas.
- Vitesses 1, 2, 3 (jusqu'à 5 selon la machine) et vitesse manuelle en %.
- Consigne de température de 15 à 30 °C.
- Minuterie : lancement, vitesse, durée, température.
- Programmation hebdomadaire : activation / désactivation.
- Bypass : automatique, ouvert ou fermé.
- Acquittement des alarmes, remise à zéro du compteur des filtres.

**Surveiller**, chaque mesure étant une entité avec son historique

- Les quatre températures : air neuf, soufflé, extrait, rejeté.
- Rendement de récupération calculé en direct.
- Ventilateurs : puissance en %, régime en tr/min ; débit en m³/h et pression en Pa selon le mode de régulation.
- Position du bypass et air dévié.
- Filtres : jours restants, état, encrassement.
- Humidité, CO₂, PM2.5, COV, entrée 0-10 V, sondes externes *(option)*.
- Puissance du préchauffage, du chauffage, du refroidissement *(option)*.
- Boost, mode cheminée, chauffage et refroidissement en cours ; alarme incendie ; seuils de qualité d'air dépassés.
- Heures de fonctionnement, pile de l'horloge.

**Régler, comme dans l'application**, dans le bloc Configuration de l'appareil

- Soufflage et extraction séparés pour chaque vitesse et pour la veille : déséquilibre au choix, en %, en m³/h ou en Pa.
- Boost : vitesses, délais de marche et d'arrêt. Mode cheminée : vitesses de soufflage et d'extraction.
- Seuils d'humidité, de CO₂, de PM2.5 et de COV. Intervalle de remplacement des filtres.
- Sonde de régulation (air extrait, boîtier, air soufflé), température de bascule hiver / été.
- Menu ingénieur *(désactivé par défaut)* : activation des sondes et des entrées, type de batterie, protection antigel, corrections des sondes, régulateurs PID, réglages de la batterie à eau, mise à l'heure.

**Comprendre** : les 46 codes de la machine, en français

- Alarmes (la machine s'arrête) et avertissements (elle continue), distingués, en clair sur la tuile et dans les capteurs.
- Rappel des filtres avant l'échéance, délai réglable, lien vers les bons filtres en option.
- Rendement expliqué quand il n'est pas mesurable, rappel antigel si le bypass est piloté à la main.

**Automatiser** : quelques idées, toutes réalisables avec les entités ci-dessus

- Vitesse 3 pendant la douche, puis retour en vitesse 2.
- Vitesse selon la présence, l'heure ou le CO₂ d'une sonde Zigbee.
- Free cooling nocturne à vos conditions, avec vos propres thermomètres.
- Notification quand les filtres sont à remplacer ou qu'une alarme tombe.
- Arrêt sur alarme incendie de votre centrale, redémarrage ensuite.
- Réduction en votre absence, retour au confort avant votre arrivée.

**Deux tuiles livrées**, rien à installer en plus

- La machine d'un coup d'œil : flux colorés, consigne au-dessus de l'échangeur (au degré entier, c'est la résolution de la machine), rendement, bypass, vitesses, marche / arrêt, curseur de vitesse manuelle quand « Manuelle » est choisie. Les points qui circulent dans les flux vont à la vitesse de chaque ventilateur, et la ligne « Ventilateurs » affiche dès le changement de vitesse le pourcentage visé, le temps que les ventilateurs y arrivent.
- Toutes les mesures : vue technique complète, mise à jour en direct.
- Options : rappel des filtres, lien de commande, commande du bypass. Français et anglais, thème clair et sombre.

### Seules vos options apparaissent

Les sondes d'humidité, de CO₂, de PM2.5 et de COV, l'entrée 0-10 V, les batteries de chauffage ou de refroidissement sont des options : toutes les machines ne les ont pas. L'intégration regarde ce qui est réellement monté et n'affiche que cela. Le reste existe, désactivé, dans la page de l'appareil : si vous ajoutez une sonde plus tard, activez son entité.

## Installation

### 1. Préparer la machine

1. Raccordez la machine à votre réseau avec son application mobile (Wi-Fi) ou par câble Ethernet.
2. Relevez son adresse IP, dans l'application ou dans la liste des appareils de votre box.
3. Dans votre box, réservez-lui cette adresse (bail DHCP statique) pour qu'elle ne change plus.

Dans les paramètres avancés du formulaire, le **mot de passe de l'appareil** (1111 d'usine, celui que demande l'application mobile ; ce n'est pas le mot de passe du menu ingénieur) ne sert qu'à une chose : demander à la machine son numéro d'identification, par le même protocole que l'application mobile, pour l'afficher dans la page de l'appareil et repérer vos commandes de filtres. L'automate ne l'expose pas en Modbus. Si vous l'avez changé dans l'application, indiquez-le ici ; s'il est faux, l'intégration fonctionne quand même, sans ce numéro.

La machine n'accepte **qu'une seule connexion Modbus TCP** par interface réseau. Si une GTB ou une autre domotique l'interroge déjà en Modbus TCP, Home Assistant ne pourra pas s'y connecter. Home Assistant garde cette connexion ouverte en permanence (voir « Coupures passagères » plus bas) : pendant qu'il est raccordé, aucun autre client Modbus TCP ne peut l'être. Si la machine refuse la connexion juste après un arrêt brutal de Home Assistant (coupure de courant), c'est qu'elle croit encore l'ancienne connexion ouverte ; elle la libère d'elle-même au bout de quelques minutes.

### 2. Installer l'intégration avec HACS

[![Ouvrir ce dépôt dans HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=floecono&repository=ha-vents-A21&category=integration)

Ou à la main : HACS, menu à trois points, **Dépôts personnalisés**, collez `https://github.com/floecono/ha-vents-A21`, type **Intégration**, puis installez « ECONOPRIME Connect (VENTS A21) » et redémarrez Home Assistant.

Sans HACS : copiez le dossier `custom_components/vents_a21` dans le dossier `custom_components` de votre Home Assistant, puis redémarrez.

### 3. Ajouter la machine

[![Ajouter l'intégration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=vents_a21)

Ou : **Paramètres**, **Appareils et services**, **Ajouter une intégration**, cherchez « ECONOPRIME ». Saisissez l'adresse IP et choisissez votre modèle. Le port (502) et l'adresse Modbus (1) sont dans les paramètres avancés, à ne modifier que si vous les avez changés sur la machine.

### 4. Poser les tuiles

Sur votre tableau de bord : crayon en haut à droite, **Ajouter une carte**, cherchez « VMC ». Deux tuiles sont proposées, et chacune trouve la machine toute seule. Rien à déclarer dans les ressources : l'intégration inscrit elle-même sa carte dans **Paramètres → Tableaux de bord → Ressources** et la met à jour à chaque version (ne supprimez pas cette ligne ; si vos ressources sont en YAML, la carte est chargée directement par la page).

| La machine d'un coup d'œil | Toutes les mesures |
|---|---|
| <img src="https://raw.githubusercontent.com/floecono/ha-vents-A21/main/docs/tuile.png" alt="Tuile principale" width="360"> | <img src="https://raw.githubusercontent.com/floecono/ha-vents-A21/main/docs/tuile-details.png" alt="Tuile détaillée : fonctionnement, ventilateurs, températures, qualité d'air, échangeur, entrées, entretien" width="360"> |

En YAML :

```yaml
type: custom:vents-a21-card          # la machine d'un coup d'œil
```

```yaml
type: custom:vents-a21-details-card  # toutes les mesures
```

Avec plusieurs machines, précisez `device_id` (l'éditeur de la carte propose la liste) et, si vous voulez, `name` pour le titre.

#### Rappel des filtres et lien de commande

La tuile principale affiche un rappel quand les filtres arrivent à échéance. Le délai se règle sur la machine, pas sur la tuile : le réglage **Rappel des filtres avant échéance**, dans la page de l'appareil à côté des stocks de filtres, donne le nombre de jours avant l'échéance à partir duquel le rappel s'affiche (21 par défaut ; avec 0, il n'apparaît qu'une fois l'échéance atteinte). Toutes les tuiles de la machine suivent ce réglage. Pour ne pas avoir à chercher la page de l'appareil, l'éditeur de la tuile le propose aussi, dans son bloc **Réglages de la machine** : ce que vous y saisissez part directement dans la machine, pas dans la tuile. L'ancienne option de tuile `filter_reminder_days` n'est plus lue qu'avec une intégration antérieure à la 0.2.12.

Une option se règle dans l'éditeur de la tuile, ou en YAML :

- **`filter_link`** : ajoute au rappel un bouton **Commander les filtres**. Il demande quels filtres vous voulez et en quelle quantité, puis les met directement dans votre panier sur econology.fr, dans un nouvel onglet : il ne reste qu'à valider. La commande est repérée comme venant de Home Assistant, avec le modèle et le numéro d'identification de votre machine (celui que montre l'application), que l'intégration lui demande à l'installation ; à défaut, l'identifiant que Home Assistant lui a donné. Désactivé par défaut.

#### Filtres de rechange : la réserve

Commander un lot de filtres plutôt qu'un jeu à chaque fois économise les frais de port, à condition de savoir ce qu'il reste dans le placard. L'intégration le sait pour vous :

- Des réglages par machine dans la page de l'appareil : **Filtres G4 en stock** et **Filtres F7 en stock**, **Rappel des filtres avant échéance** (le délai du rappel, voir plus haut), et **Filtres air neuf** (G4, F7 ou G4 + F7, selon ce qui équipe le côté air neuf de votre machine ; le côté extraction prend toujours un G4). Par défaut : un G4 à l'extraction, un F7 à l'air neuf.
- **La réserve baisse toute seule au changement de filtres** : dès que le compteur de jours de la machine repart, que la remise à zéro vienne de Home Assistant, de l'application ou du panneau, un jeu est retiré du stock.
- **La fenêtre de commande propose un an de filtres** d'après l'intervalle de remplacement réglé dans la machine (par exemple 4 G4 + 4 F7 pour un intervalle de 90 jours), moins ce qui est déjà en stock ; vous ajustez les quantités avant d'envoyer au panier. La tuile retient ensuite « commande en cours » et affiche **Reçus** : un clic à l'ouverture du colis, et la réserve est à jour.
- Le rappel tient compte de la réserve : s'il reste de quoi faire le prochain changement, il le dit et ne propose pas de commander ; sinon, le bouton de commande apparaît. Quand la réserve est vide après un changement, la tuile le signale même loin de l'échéance, pour commander au calme.

Rien de tout cela n'est actif tant que vous n'avez pas renseigné un stock ou passé une commande : une installation neuve n'affiche pas « plus de filtres en réserve ». Les services `vents_a21.filters_ordered` et `vents_a21.filters_received` sont ceux qu'utilise la tuile ; ils servent aussi dans vos automatisations.

```yaml
type: custom:vents-a21-card
filter_link: true
```

#### Commande manuelle du bypass

Par défaut, la tuile se contente d'afficher l'état du bypass (fermé, ouvert, ou la position intermédiaire). Le dessin suit cette position : à 40 %, une part fine du flux contourne l'échangeur et le reste le traverse. Ce pourcentage est la position du volet, estimée par la machine à partir de son temps de course, pas une mesure de débit : la répartition réelle de l'air entre les deux chemins dépend des pertes de charge de chacun. Pour les utilisateurs avertis qui veulent le piloter eux-mêmes (voir [Piloter le bypass soi-même](#piloter-le-bypass-soi-même)), elle peut afficher en plus une rangée **Bypass : Auto / Ouvert / Fermé**. Désactivée par défaut, elle s'active dans l'éditeur de la tuile ou en YAML. Quand elle est active, la tuile ne signale plus l'avertissement « Bypass en mode manuel » que la machine émet tant qu'on lui a retiré la main : c'est voulu.

```yaml
type: custom:vents-a21-card
bypass_control: true
```

## Réglages

Dans **Paramètres**, **Appareils et services**, ouvrez la machine : le bloc **Configuration** reprend les réglages de l'application mobile.

- **Vitesses** : pourcentage du ventilateur de soufflage et d'extraction pour la veille et pour chaque vitesse. Sur une machine réglée en débit constant ou en pression constante, ce sont des m³/h ou des pascals qui sont proposés à la place.
- **Boost** : vitesses de soufflage et d'extraction, temporisations de démarrage et d'arrêt.
- **Minuterie** : vitesse, durée, température.
- **Qualité d'air** : seuils d'humidité, de CO₂, de PM2.5 et de COV, selon les sondes montées.
- **Filtres** : intervalle de remplacement, remise à zéro du compteur.
- **Divers** : sonde servant à la régulation, température de bascule hiver/été, mode du bypass.

Les **options de l'intégration** (bouton **Configurer** sur la page de l'intégration) règlent l'intervalle de lecture et, pour ceux qui pilotent le bypass eux-mêmes, l'option **Bypass piloté par Home Assistant** (voir plus bas).

Les réglages du **menu ingénieur** existent aussi, désactivés par défaut : activation des sondes et des entrées, type de batterie, protection antigel, corrections des sondes de température, temporisations, coefficients des régulateurs. Activez seulement ceux dont vous avez besoin, ils agissent directement sur la machine.

Deux choses ne sont volontairement pas proposées : la remise aux réglages d'usine et le mot de passe du menu ingénieur.

### Piloter le bypass soi-même

En mode **Automatique**, la machine ouvre et ferme le bypass selon les règles de la notice de l'application DF Connect (annexe « Algorithme de régulation »), que nous avons confrontées à une DF 350 Connect (microprogramme 0.41) au cours d'une nuit d'essai :

- **Réglez la sonde de régulation sur « air extrait » pour un rafraîchissement nocturne qui vise la maison.** La machine régule le bypass sur la température mesurée par la sonde choisie. Avec « air extrait », c'est la température de la pièce (reprise) qui est comparée à la consigne : le bypass s'ouvre tant que la maison est trop chaude. Avec « air soufflé », c'est la température de l'air soufflé qui est comparée à la consigne ; celle de la maison n'entre pas dans la décision. Lors de l'essai, consigne à 20 °C, le soufflage a été tenu à 20,5 °C pendant que la maison restait à 23 °C : la machine régule ce qu'elle souffle, pas ce que vous ressentez. (La notice affirme qu'aucune régulation du bypass n'a lieu avec la sonde « air soufflé » ; sur le microprogramme 0.41, c'est faux, elle a lieu, mais sur la mauvaise température.) La valeur d'usine est « air soufflé » : vérifiez ce réglage dans la page de l'appareil avant de juger que le bypass ne fonctionne pas.
- **Mode Froid (ou Automatique en été)** : le bypass s'ouvre quand la température régulée dépasse la consigne d'au moins 1 °C, que l'air extérieur est au moins 2 °C plus frais, qu'il fait au moins 16 °C dehors et que le préchauffage est désactivé. Il se referme quand l'air extérieur n'est plus plus frais, ou sous 15 °C dehors. La notice ajoute « ou quand l'extérieur passe sous la consigne » : nous ne l'avons pas observé (bypass resté ouvert plus d'une heure avec 19,8 °C dehors pour une consigne de 20 °C) ; il y a au moins une hystérésis que la notice ne décrit pas.
- **Mode Chaud (ou Automatique en hiver)** : le bypass s'ouvre quand la température régulée est sous la consigne d'au moins 1 °C et que l'air extérieur est au moins 2 °C plus chaud (chaleur gratuite). Il se referme dès que l'extérieur n'est plus plus chaud, ou quand l'extérieur dépasse la consigne.
- La machine réagit en moins de dix minutes à un changement de consigne ou de sonde, et le mouvement est proportionnel, pas tout ou rien : lors d'un second essai, consigne placée juste sous la température extraite, le volet a été tenu 45 minutes entre 60 et 84 % d'ouverture, avec une commande toujours égale à la position lue. La régulation module donc bien le volet trois points entre ses butées ; vous verrez ces positions intermédiaires sur la tuile et dans **Ouverture du bypass**. La consigne du thermostat, elle, est au degré entier : une valeur de 23,5 °C est arrondie à 24 °C par la machine.
- Si vous préférez décider vous-même, par exemple pour un rafraîchissement nocturne (free cooling) à vos conditions, l'entité **Mode du bypass** de la machine accepte trois valeurs : **Automatique**, **Ouvert** (l'air neuf contourne l'échangeur) et **Fermé** (récupération de chaleur). Elle se pilote depuis la page de l'appareil, depuis la tuile si vous activez sa commande manuelle, ou par automatisation.
- **En manuel, c'est tout ou rien.** La modulation décrite ci-dessus n'existe qu'en mode Automatique : c'est le régulateur de la machine qui calcule la position et y amène le volet. En manuel, le microprogramme n'accepte pour le volet trois points des machines ECONOPRIME que « ouvert » ou « fermé » ; il n'y a pas de consigne de position à lui envoyer, et l'intégration n'en propose donc pas. (L'automate A21 connaît une position manuelle en pourcentage, mais seulement pour les bypass à servomoteur analogique ou les échangeurs rotatifs, qu'on trouve chez d'autres marques.) Si vous voulez une ouverture partielle, laissez la machine en Automatique et jouez sur la consigne et la sonde.

Exemple : ouvrir le bypass la nuit en été quand l'air extérieur est plus frais que l'intérieur, et rendre la main à la machine le matin.

```yaml
automation:
  - alias: "VMC : free cooling nocturne"
    triggers:
      - trigger: time
        at: "22:30:00"
    conditions:
      - condition: numeric_state
        entity_id: sensor.vmc_temperature_exterieure   # adaptez les noms d'entités à votre machine
        below: 20
      - condition: template
        value_template: >
          {{ states('sensor.vmc_temperature_exterieure') | float
             < states('sensor.vmc_temperature_extraite') | float - 2 }}
    actions:
      - action: select.select_option
        target:
          entity_id: select.vmc_mode_du_bypass
        data:
          option: open      # valeurs possibles : auto, open, closed

  - alias: "VMC : retour en automatique"
    triggers:
      - trigger: time
        at: "07:00:00"
    actions:
      - action: select.select_option
        target:
          entity_id: select.vmc_mode_du_bypass
        data:
          option: auto
```

Tant que le bypass n'est pas en **Automatique**, la machine émet l'avertissement « Bypass en mode manuel » (code 38). Si c'est votre choix, dites-le à l'intégration : **Paramètres**, **Appareils et services**, l'intégration, **Configurer**, puis cochez **Bypass piloté par Home Assistant**. Cet avertissement disparaît alors des tuiles, du capteur « Alarmes actives », du capteur d'état et du capteur binaire « Alarme » ; les autres alarmes et avertissements restent signalés normalement. Sans cette option, seule la tuile dont la commande du bypass est activée le passe sous silence.

Deux précautions :

- En mode **Ouvert**, c'est vous qui décidez : la machine ne refermera pas le bypass si l'air extérieur devient froid. Prévoyez toujours une automatisation de retour.
- **Antigel** : sans résistance de préchauffage, c'est la gestion du bypass qui protège l'échangeur du gel. Tant que le bypass est en manuel, cette protection ne joue plus. **En hiver, repassez en Automatique.** La tuile le rappelle dès que l'air extérieur descend sous 5 °C, même si vous avez fait taire l'avertissement « Bypass en mode manuel », et la tuile détaillée l'indique en permanence sous « Commande ».

## Alarmes et avertissements

Le capteur **Alarmes actives** donne le nombre de codes actifs, et ses attributs leur signification :

- `alarms` : les alarmes. La machine s'arrête et attend que vous appuyiez sur **Acquitter les alarmes** une fois la cause traitée.
- `warnings` : les avertissements. La machine continue de tourner, et l'avertissement disparaît seul quand sa cause disparaît.

Exemple de notification :

```yaml
automation:
  - alias: "VMC : prévenir en cas d'alarme"
    triggers:
      - trigger: state
        entity_id: binary_sensor.zephyr_240_s_connect_alarme
        to: "on"
    actions:
      - action: notify.notify
        data:
          title: "VMC"
          message: >
            {{ (state_attr('sensor.zephyr_240_s_connect_alarmes_actives', 'alarms')
                + state_attr('sensor.zephyr_240_s_connect_alarmes_actives', 'warnings')) | join(', ') }}
```

## Bon à savoir

- **Rendement de récupération** : calculé côté air neuf, (air soufflé − air neuf) ÷ (air extrait − air neuf). Un chiffre n'est donné que lorsqu'il a un sens : machine en marche, bypass fermé, pas de batterie en action, et au moins 4 °C d'écart entre intérieur et extérieur. En dessous, l'erreur des sondes, divisée par un écart trop petit, rendrait le chiffre faux. L'échangeur récupère pourtant bien la chaleur dans ce cas : la tuile l'indique (« Actif », « Récupération active, rendement non mesurable ») au lieu de laisser un vide, et le capteur `heat_recovery_efficiency` porte un attribut `status` qui donne la raison (`small_difference`, `heating`, `cooling`, `preheating`, `bypass`, `off`).
- **Intervalle de lecture** : 30 secondes par défaut (la cadence de l'application du constructeur), réglable dans les options de l'intégration. Descendre en dessous n'apporte rien de visible et sollicite davantage le module Wi-Fi de la machine.
- **Coupures passagères** : une lecture qui échoue est retentée une seconde plus tard, et les dernières valeurs sont conservées pendant trois lectures manquées de suite avant que la machine passe « indisponible ». Un paquet perdu en Wi-Fi ne vide donc pas la tuile et ne déclenche pas vos automatisations. L'intégration garde une seule connexion ouverte avec la machine entre les lectures, au lieu d'en ouvrir une nouvelle à chaque fois : le module Wi-Fi de la machine n'a que quelques connexions disponibles, et les ouvertures-fermetures répétées sur une liaison qui perd des paquets finissent par les épuiser. Le module Wi-Fi laisse parfois passer dans le flux Modbus du texte destiné à sa propre puce radio (`AT+RFPOWER`, `AT+CIPSEND`) ; l'intégration l'ignore et poursuit sur la même connexion. Si la machine passe quand même souvent en indisponible, c'est le réseau qu'il faut regarder : un module Wi-Fi en limite de portée dans un local technique, c'est fréquent, et une liaison câblée ou un point d'accès plus proche règle la question. Les compteurs de la liaison (requêtes, réponses perdues, parasites) sont dans les **diagnostics** de l'intégration.
- **Module Wi-Fi figé** : il arrive (constaté avec le firmware 0.43, après une série de pertes de paquets) que le module accepte encore les connexions mais ne réponde plus à rien, ni en Modbus ni à l'application. Aucune commande ne le relance. Quand l'intégration le constate, elle ouvre une **réparation** dans Home Assistant qui demande de couper l'alimentation de la machine quelques secondes ; au retour, tout repart seul et la réparation disparaît. Si cela se répète, améliorez le signal Wi-Fi à l'emplacement de la machine.
- **Échangeur** : les machines ECONOPRIME ont un échangeur à plaques avec bypass. L'automate A21 sait aussi piloter un échangeur rotatif, qu'on trouve chez d'autres marques : l'intégration le reconnaît et adapte ses libellés, mais ce cas ne concerne pas la gamme.
- **Programmation hebdomadaire** : elle s'active et se désactive depuis Home Assistant. Ses créneaux se règlent pour l'instant dans l'application mobile.
- **Automatisations Home Assistant** : vous pouvez aussi vous passer de la programmation de la machine et tout piloter par des automatisations, par exemple changer de vitesse selon l'heure, la présence, l'humidité ou le CO₂, lancer la minuterie pendant la douche ou être prévenu quand les filtres sont à remplacer. Dans ce cas, désactivez la programmation hebdomadaire de la machine, pour que les deux ne se contredisent pas.
- **Horloge** : le bouton « Mettre l'horloge à l'heure » envoie l'heure de Home Assistant à la machine (validé sur machine). Si la pile de l'horloge est faible, une automatisation qui l'appuie chaque nuit dépanne en attendant de la changer.
- **Assistance** : dans la page de l'intégration, menu à trois points, **Télécharger les diagnostics**. Le fichier contient les registres bruts de la machine, sans son adresse IP : joignez-le à votre demande.

## Sécurité du réseau

Le protocole Modbus TCP ne prévoit ni mot de passe ni chiffrement : tout appareil présent sur le même réseau que la machine peut la lire et la piloter. Ce n'est pas propre à cette intégration, c'est le fonctionnement du protocole. La protection se fait donc par le réseau et par Home Assistant.

- **Ne redirigez jamais le port 502 vers Internet** sur votre box ou votre routeur.
- **Pilotez à distance en passant par Home Assistant** (son accès distant ou un VPN), jamais en ouvrant un accès direct à la machine.
- **Protégez Home Assistant** : c'est lui qui porte les comptes et les mots de passe. Activez la double authentification.
- **Invités** : faites-les passer par le Wi-Fi invité de votre box, qui est isolé du réseau où se trouve la machine.
- **Pour aller plus loin, un réseau à part pour les appareils sans authentification** : si votre routeur le permet, regroupez dans un VLAN dédié la machine et vos autres équipements qui se pilotent sans mot de passe (Modbus, objets connectés), et n'autorisez que Home Assistant à les joindre. Un ordinateur ou un téléphone du réseau principal ne peut alors plus les atteindre directement. La marche à suivre est détaillée ci-dessous.

### Installations professionnelles ou réseau partagé

C'est la méthode des gestions techniques de bâtiment : on ne sécurise pas le Modbus lui-même, on l'enferme dans une zone technique, et les personnes s'identifient sur la supervision. Ici, Home Assistant joue le rôle de la supervision.

- **Réseau technique séparé** : placez la machine dans un VLAN dédié, distinct des postes de travail et du Wi-Fi.
- **Pare-feu en liste blanche** : bloquez tout entre les réseaux, et n'ouvrez qu'un flux, de Home Assistant vers la machine, en TCP sur le port 502.
- **Un seul maître** : Home Assistant est le seul à interroger la machine en Modbus. Les utilisateurs passent par lui, avec leurs comptes et leurs droits.
- **Accès distant des mainteneurs** : par un VPN vers Home Assistant, jamais par un accès direct à la machine.
- **Sortie Internet de la machine** : bloquez-la si vous n'utilisez pas le pilotage à distance de l'application mobile.
- **Passerelle RS485 vers Ethernet** : si la machine est raccordée par une passerelle Modbus, celle-ci n'authentifie pas davantage ses clients. Placez-la dans le même réseau technique et changez son mot de passe d'administration.

## État de la version 0.2.11

L'intégration est écrite d'après la table Modbus officielle de l'automate A21 (VENTS, document V55-8-1EN-02) et la notice de l'application DF Connect pour la signification des codes d'alarme. Elle est vérifiée contre un simulateur de la machine, par une suite de tests automatiques et par un essai dans une instance Home Assistant. Elle est utilisée sur une DF 350 Connect (micrologiciel 0.41) depuis le 13 octobre 2026 ; la mise à l'heure, l'ordre des octets et les codes d'alarme y ont été vérifiés. Vos retours sur les autres modèles sont les bienvenus, [ouvrez un ticket](https://github.com/floecono/ha-vents-A21/issues) en joignant les diagnostics.

## Besoin de filtres, d'une sonde, d'un conseil ?

Filtres de rechange, sondes CO₂ et hygrométriques, batteries de préchauffage, conduits et bouches : tout est sur **[econology.fr](https://www.econology.fr/?utm_source=github&utm_medium=readme&utm_campaign=vents_a21)**, avec une équipe qui connaît ces machines.

## Pour les développeurs

```bash
pip install -r requirements_test.txt
pytest
```

`tests/simulator.py` est un simulateur Modbus TCP de l'automate A21, sans dépendance. Lancé seul (`python tests/simulator.py --port 5020`), il permet d'essayer l'intégration sans machine. Le client Modbus est embarqué dans l'intégration (`modbus.py`) pour ne dépendre d'aucune bibliothèque externe.

L'ordre des octets des registres composés (minuteries, version du micrologiciel) reprend celui documenté par le projet [pybls21](https://github.com/jvitkauskas/pybls21) pour l'automate Blauberg S21, de la même famille que l'A21.

## Licence

Copyright © 2026 Econology.

Cette intégration est un logiciel libre, distribué sous la licence [GNU GPL version 3](LICENSE) : vous pouvez l'utiliser, la modifier et la redistribuer, à condition de conserver cette mention et de publier vos versions modifiées sous la même licence. Elle est fournie sans aucune garantie.

La licence porte sur le code. Elle ne donne aucun droit sur les noms et logos Econology et ECONOPRIME.
