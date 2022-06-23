# HARFANG3D - Dogfight sandbox 2  
## Tutorial - Ajout d'une texture dans la scène

### 1.Importer la texture  

Importer votre texture texture dans le dossier `source/assets/textures/`  

### 2.Installation Harfang Studio:  

Vous pouvez télécharger Harfang studio ici : https://www.harfang3d.com/en_US/pricing  

![screenshot](screenshots/dl_harfang_studio.jpg)  

### 3.Ouvrir le projet:

Après la procédure d'installation, démarrer Harfang Studio, puis cliquer sur "Open Project":  

![screenshot](screenshots/hs_01.jpg)  

Depuis le browser qui s'ouvre, aller dans le dossier du Dogfight puis ouvrir le fichier `source/assets/project.prj`  

![screenshot](screenshots/hs_02.jpg)  

### 4.Dupliquer la scène plane.scn  

Depuis le panneau `Project`, ouvrir la scène `primitives/plane.scn`  

![screenshot](screenshots/hs_03.jpg)  

Sauvegarder la scène sous un autre nom (ex: `my_plane.scn`)  

![screenshot](screenshots/hs_04.jpg)  
![screenshot](screenshots/hs_05.jpg)

### 5.Charger la texture dans le materiau  

Sélectionner le plan dans le panneau de la vue 3D:  

![screenshot](screenshots/hs_06.jpg)  

Dans le panneau Inspector, déployer le materiau:  

![screenshot](screenshots/hs_07.jpg)  

Cliquer sur le browser pour sélectionenr la texture d'Albedo:  

![screenshot](screenshots/hs_08.jpg)  

Sélectionner la texture:  

![screenshot](screenshots/hs_09.jpg)  

La texture a été assignée au plan:  

![screenshot](screenshots/hs_10.jpg)  

Sauvegarder la scène `my_plane.scn`

![screenshot](screenshots/hs_11.jpg)  

### 6.Importer le plan dans la scène principale  

Depuis l'explorateur de projet, ouvrir `main.scn`:  

![screenshot](screenshots/hs_12.jpg)  

Dans le menu `Scene/Add`, importer une instance:  

![screenshot](screenshots/hs_13.jpg)  

Importer votre plan:  

![screenshot](screenshots/hs_14.jpg)  

Appuyer sur Left-Shift + A pour focaliser sur le plan:  

![screenshot](screenshots/hs_15.jpg)  

Utiliser les différents types de gizmos pour déplacer / orienter / mettre à l'échelle votre plan dans la scène:

![screenshot](screenshots/hs_16.jpg)  

Une fois placé votre plan, sauvegarder:  

![screenshot](screenshots/hs_17.jpg)  

### 7.Démarrer le Dogfight !

Démarrer le Dogfight en cliquant sur le batch:
![screenshot](screenshots/hs_18.jpg)  

Votre texture est bien dans la scène !

![screenshot](screenshots/hs_19.jpg)  