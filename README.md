# FileExplorer - DocExplorer & AnalystHelper

Outils d'analyse et de classification de documents 

## 🎯 Projets Disponibles

### 1. DocExplorer (Nouveau !)
**Interface moderne pour l'analyse de documents**

- ✅ Interface graphique intuitive et élégante
- ✅ Classification automatique (Dossier technique / Correspondance / Autres)
- ✅ Renommage intelligent des emails (Date_Expéditeur_Destinataire)
- ✅ Extraction automatique des pièces jointes
- ✅ Export Excel avec traçabilité complète
- ✅ Rapport HTML interactif
- ✅ Arborescence source visualisable
- ✅ Dossier de sortie personnalisable
- ✅ Historique des traitements

**Lancement:**
```bash
python doc_explorer.py
# ou double-clic sur: lancer_doc_explorer.bat
```

### 2. AnalystHelper v3
**Package Python pour automatisation documentaire**

- Scan récursif de dossiers
- Classification par type de fichier
- Extraction et renommage emails
- Export multi-format (Excel, HTML, JSON)

## 📦 Installation

### Prérequis
- Python 3.8+
- Windows, macOS ou Linux

### Dépendances
```bash
pip install -r requirements.txt
```

**Packages requis:**
- `extract-msg` - Lecture fichiers .msg Outlook
- `Pillow` - Gestion images (logos, bannières)
- `openpyxl` - Export Excel
- `tkinter` - Interface graphique (inclus avec Python)

## 🚀 Démarrage Rapide

### DocExplorer (Recommandé)
1. Lancer l'interface: `python doc_explorer.py`
2. Sélectionner un dossier source
3. Choisir les fonctionnalités désirées
4. Cliquer sur "Lancer l'Analyse"
5. Consulter les résultats (Excel, HTML, dossiers classés)

### En Ligne de Commande
```python
from analyst_helper import FolderScanner

scanner = FolderScanner("chemin/vers/dossier")
files = scanner.scan()
print(f"Fichiers trouvés: {scanner.stats['total_files']}")
```

## 📁 Structure du Projet

```
FileExplorer/
├── doc_explorer.py          # Interface DocExplorer (⭐ Nouveau)
├── analyst_helper/          # Package principal
│   ├── core/               # Modules de base
│   │   ├── scanner.py      # Scan de dossiers
│   │   ├── email_renamer.py # Renommage emails
│   │   └── reporter.py     # Génération rapports
│   └── __init__.py
├── lancer_doc_explorer.bat  # Lanceur Windows
├── logo.png                 # Logo interface
├── Banière.png             # Bannière interface
├── requirements.txt         # Dépendances production
├── requirements_dev.txt     # Dépendances développement
└── _archives/              # Anciennes versions
```

## 🔧 Fonctionnalités Détaillées

### Classification Automatique
- **Dossier technique:** PDF, DWG, DXF, DOC, XLS, PPT, ZIP, RAR
- **Correspondance:** MSG, EML
- **Autres fichiers:** Tout le reste

### Renommage Emails
Format: `YYMMDD_Expediteur_Destinataire.msg`

Exemple: `241024_Dupont_Martin.msg`

### Extraction Pièces Jointes
- Extraction automatique depuis emails
- Classification selon type
- Protection contre path traversal
- Gestion noms de fichiers sécurisés

### Rapports
- **Excel:** Liste complète avec statistiques
- **HTML:** Rapport interactif avec visualisations
- **Arborescence:** Mindmap D3.js interactive

## 🛡️ Sécurité & Robustesse

DocExplorer v2 inclut:
- ✅ Validation permissions fichiers (R/W)
- ✅ Protection path traversal
- ✅ Gestion propre des ressources (fermeture fichiers)
- ✅ Backup automatique historique
- ✅ Nettoyage dossiers temporaires
- ✅ Support multi-plateforme (Windows/Mac/Linux)
- ✅ Throttling UI pour performances
- ✅ Arrêt propre des threads



## 📊 Historique des Traitements

DocExplorer sauvegarde automatiquement l'historique dans `.docexplorer_history.json`:
- Fichiers déjà traités (évite doublons)
- Statistiques par exécution
- Configuration utilisée
- Rapports générés

## 🔄 Workflow Typique

1. **Préparation:** Placer tous documents dans un dossier source
2. **Analyse:** Lancer DocExplorer, sélectionner le dossier
3. **Configuration:** Choisir fonctionnalités (classification, PJ, rapports)
4. **Exécution:** L'outil crée:
   - Dossiers classés (Dossier technique / Correspondance / Autres)
   - Excel de traçabilité
   - Rapport HTML
   - Arborescence source
5. **Consultation:** Ouvrir rapports via boutons interface

## 💡 Conseils d'Utilisation

### Première Utilisation
- Tester sur petit volume (< 100 fichiers)
- Vérifier les résultats
- Ajuster configuration si nécessaire

### Gros Volumes (> 1000 fichiers)
- Désactiver fonctionnalités non nécessaires
- Utiliser dossier de sortie sur disque rapide (SSD)
- Prévoir temps de traitement proportionnel

### Dossier de Sortie Personnalisé
Recommandé pour:
- Séparer sources et résultats
- Traiter dossiers en lecture seule
- Archivage sur autre disque

## 🐛 Dépannage

### "Pas de permission de lecture"
→ Vérifier droits d'accès au dossier

### "Le fichier Excel n'existe pas"
→ Vérifier que "Export Excel" était coché

### Erreur extraction PJ
→ Installer/réinstaller `extract-msg`: `pip install --upgrade extract-msg`

### Interface ne s'affiche pas
→ Vérifier Tkinter: `python -m tkinter`

## 📝 Licence

Voir [LICENSE](LICENSE)

## 👤 Auteur

Maxime Lhuillier 

## 🔗 Liens Utiles

- **Archive Documentation:** [_archives/README.md](_archives/README.md)
- **Audit de Robustesse:** [_archives/AUDIT_ROBUSTESSE.md](_archives/AUDIT_ROBUSTESSE.md)
- **Tri des Fichiers:** [_archives/TRI_FICHIERS.md](_archives/TRI_FICHIERS.md)

---

*Dernière mise à jour: Novembre 2025*
*Version: DocExplorer v2.0 + AnalystHelper v2.0*
