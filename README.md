# PMSI Data Quality Automation

Projet de démonstration consacré au contrôle qualité, à la fiabilisation et à l’automatisation des traitements de données hospitalières et PMSI.

L’objectif est de simuler un environnement de contrôle de données médicales dans lequel plusieurs sources sont extraites, transformées, validées puis intégrées dans une base PostgreSQL, avec suivi des anomalies dans un tableau de bord Streamlit.

> Les données utilisées dans ce projet sont entièrement synthétiques et ne contiennent aucune donnée patient réelle.

---

## Objectifs

Ce projet vise à illustrer plusieurs problématiques rencontrées dans un environnement DIM :

1. Contrôler l’exhaustivité des données
2. Détecter les incohérences et anomalies
3. Vérifier la cohérence entre différentes sources
4. Contrôler les diagnostics et informations de séjour
5. Identifier les doublons
6. Sécuriser les relations entre patients, séjours et diagnostics
7. Automatiser les contrôles répétitifs
8. Produire des indicateurs de qualité
9. Faciliter l’identification des données nécessitant une correction
10. Mettre à disposition un tableau de bord de suivi

---

## Technologies

- Python
- Pandas
- SQL
- PostgreSQL
- SQLAlchemy
- Streamlit
- Plotly
- Docker
- Pytest
- Git / GitHub

---

## Architecture générale

Le pipeline suit une logique ETL :

```text
Sources hospitalières simulées
        |
        v
Extraction CSV / XML
        |
        v
Nettoyage et standardisation
        |
        v
Contrôles qualité
        |
        v
Détection des anomalies
        |
        v
Chargement PostgreSQL
        |
        v
Dashboard Streamlit
