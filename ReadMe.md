
# Test technique de Matthieu Bachelot 

Ce projet met en place un pipeline d'analyse automatique des rapports de laboratoire pour une analyse des pesticides
Il inclut :
- Un **notebook Jupyter** qui présente le déroulement de la pipeline avec les différentes explications.
- Des **fichiers utils / fichier api** pour la lisibilitée & le cloisonnement.
- Des **résultats intermédiaires** pour la tracabilitée.

Le projet se structure comme il suit 

project/
│── api_key.py                                          # Clé API openAI (dans le .gitigore)
│── utils.py                                            # Fonctions utilitaires 
│── pipeline.ipynb                                      # Notebook principal (pipeline en question)
│── examples/
│     └── *.pdf                                         # Rapports de laboratoire à analyser
│── json_outputs/
│     └── *.json                                        # Résultats intermédiaires de l'analyse
│── requirements.txt                                    # Dépendances
│── ReadMe.md                                           # Documentation
│── Tracklab_Senior Data Scientist_Technical Case.pdf   # Consignes


## 1. Installation 

### Dans le répertoire de ce fichier, créer votre environnement : 

```
python -m venv tracklab
```

### Puis l'activer 

```
source tracklab/bin/activate
```

### Télecharger les packages nécessaires  

```
pip install -r requirements.txt
```

## 2. Visualisation de la pipeline avec le notebook 

### L'intégralité de la pipeline est visible dans le notebook pipeline.ipynb. Ceci étant les résultats ne seront pas reproductible sans clé API stockée dans un fichier à part (api_key.py) sous la forme d'une constante : 
OPENAI_API_KEY = "sk- ..."

```
jupyter notebook
```

## 3. HYPOTHÈSES DE TRAVAIL

Les contraintes de temps pour développer ce pipeline nous a conduit à faire certaines hypothèses ainsi que certains choix de structures :
- La structure en deux dossiers examples & json_outputs est adaptée pour peu d'exemples. Dans des cas avec plus de documents un dossier par analyse sera plus adapté
- Le formattage des noms dans les DB de l'UE sont supposés être en anglais (et commencent tous avec une majuscule)
- Les analyses de MRL sont des entiers
- Les résultats renvoyé par l'API sont tous des strings avec * à la fin



