"""
Générateur d'arborescence HTML interactive pour visualiser la structure des dossiers
Utilise D3.js pour créer une visualisation en arbre horizontal
"""

from pathlib import Path
from datetime import datetime
import json


def safe_print(msg):
    """Print sécurisé qui gère les erreurs d'encodage"""
    try:
        print(msg)
    except UnicodeEncodeError:
        # Si l'encodage échoue, on affiche une version simplifiée
        print(msg.encode('ascii', 'ignore').decode('ascii'))
    except:
        pass


class TreeGenerator:
    """Générateur d'arborescence HTML interactive"""

    def __init__(self, output_path: str):
        """
        Initialise le générateur d'arborescence

        Args:
            output_path: Chemin du fichier HTML de sortie
        """
        self.output_path = Path(output_path)
        self.stats = {
            'total_files': 0,
            'total_dirs': 0,
            'total_size_mb': 0
        }

    def generate(self, source_folder: Path, exclude_folders: list = None):
        """
        Génère l'arborescence HTML

        Args:
            source_folder: Dossier source à analyser
            exclude_folders: Liste des dossiers à exclure
        """
        if exclude_folders is None:
            exclude_folders = []

        # Calculer les statistiques
        self._calculate_stats(source_folder, exclude_folders)

        # Construire l'arbre JSON
        tree_data = self._build_tree_json(source_folder, exclude_folders)
        tree_json = json.dumps(tree_data, ensure_ascii=False)

        # Générer le HTML
        html_content = self._generate_html(source_folder, tree_json)

        # Écrire le fichier
        try:
            with open(self.output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
        except Exception as e:
            safe_print(f"[ERREUR] Impossible d'écrire le fichier d'arborescence: {e}")
            raise

    def _calculate_stats(self, folder: Path, exclude_dirs: list):
        """Calcule les statistiques du dossier"""
        try:
            for item in folder.rglob('*'):
                if item.name.startswith('.'):
                    continue

                # Vérifier si dans un dossier exclu
                skip = False
                for exclude in exclude_dirs:
                    if exclude in item.parts:
                        skip = True
                        break
                if skip:
                    continue

                if item.is_file():
                    self.stats['total_files'] += 1
                    self.stats['total_size_mb'] += item.stat().st_size / (1024 * 1024)
                elif item.is_dir():
                    self.stats['total_dirs'] += 1
        except Exception as e:
            safe_print(f"Erreur calcul stats: {e}")

    def _build_tree_json(self, directory: Path, exclude_dirs: list):
        """Construit récursivement la structure JSON pour la mindmap"""
        exclude_set = set(exclude_dirs)

        node = {
            'name': directory.name or str(directory),
            'path': str(directory),
            'type': 'folder',
            'children': []
        }

        try:
            items = sorted(directory.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
        except PermissionError:
            safe_print(f"[AVERTISSEMENT] Accès refusé au dossier: {directory}")
            return node
        except Exception as e:
            safe_print(f"[ERREUR] Impossible de lire le dossier {directory}: {e}")
            return node

        for item in items:
            try:
                if item.name.startswith('.'):
                    continue
                if item.name in exclude_set:
                    continue

                if item.is_dir():
                    child = self._build_tree_json(item, exclude_dirs)
                    node['children'].append(child)
                else:
                    try:
                        size = item.stat().st_size / 1024
                        size_str = f"{size:.1f} KB" if size < 1024 else f"{size/1024:.1f} MB"
                        # Date de modification
                        mtime = item.stat().st_mtime
                        date_str = datetime.fromtimestamp(mtime).strftime('%d/%m/%Y %H:%M')
                    except Exception as e:
                        # Gérer les fichiers non accessibles
                        safe_print(f"[AVERTISSEMENT] Impossible d'accéder à {item.name}: {e}")
                        size_str = "Inaccessible"
                        date_str = "?"

                    node['children'].append({
                        'name': item.name,
                        'path': str(item),
                        'type': 'file',
                        'ext': item.suffix.lower(),
                        'size': size_str,
                        'date': date_str
                    })
            except Exception as e:
                # Erreur sur un item spécifique, on continue avec les autres
                try:
                    safe_print(f"[ERREUR] Erreur lors du traitement de {item.name}: {e}")
                except:
                    safe_print(f"[ERREUR] Erreur lors du traitement d'un fichier (nom non affichable)")
                continue

        return node

    def _get_file_color(self, ext: str) -> str:
        """Retourne une couleur selon le type de fichier"""
        ext = ext.lower()
        colors = {
            'doc': '#e74c3c',
            'sheet': '#27ae60',
            'email': '#3498db',
            'image': '#9b59b6',
            'archive': '#f39c12',
            'cad': '#e67e22',
            'default': '#95a5a6'
        }

        if ext in ['.pdf', '.doc', '.docx', '.odt']:
            return colors['doc']
        elif ext in ['.xls', '.xlsx', '.csv', '.ods']:
            return colors['sheet']
        elif ext in ['.msg', '.eml']:
            return colors['email']
        elif ext in ['.jpg', '.png', '.gif', '.bmp']:
            return colors['image']
        elif ext in ['.zip', '.rar', '.7z']:
            return colors['archive']
        elif ext in ['.dwg', '.dxf']:
            return colors['cad']
        else:
            return colors['default']

    def _get_file_types_summary(self, tree_data: dict) -> dict:
        """Calcule le nombre de fichiers par type"""
        types = {}

        def count_types(node):
            if node.get('type') == 'file':
                ext = node.get('ext', 'Autre')
                category = self._get_extension_category(ext)
                types[category] = types.get(category, 0) + 1

            for child in node.get('children', []):
                count_types(child)

        count_types(tree_data)
        return types

    def _get_extension_category(self, ext: str) -> str:
        """Retourne la catégorie d'une extension"""
        ext = ext.lower()
        if ext in ['.pdf', '.doc', '.docx', '.odt']:
            return 'Documents'
        elif ext in ['.xls', '.xlsx', '.csv', '.ods']:
            return 'Tableurs'
        elif ext in ['.msg', '.eml']:
            return 'Emails'
        elif ext in ['.jpg', '.png', '.gif', '.bmp']:
            return 'Images'
        elif ext in ['.zip', '.rar', '.7z']:
            return 'Archives'
        elif ext in ['.dwg', '.dxf']:
            return 'CAD'
        else:
            return 'Autres'

    def _generate_html(self, folder: Path, tree_json: str) -> str:
        """Génère le HTML complet avec arborescence horizontale"""
        return f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Arborescence - {folder.name}</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            overflow: hidden;
            height: 100vh;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px 30px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        }}

        .header h1 {{
            font-size: 24px;
            margin-bottom: 5px;
        }}

        .header p {{
            opacity: 0.9;
            font-size: 12px;
        }}

        .controls {{
            background: #f8f9fa;
            padding: 15px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}

        .search-box {{
            flex: 1;
            max-width: 400px;
            position: relative;
        }}

        .search-box input {{
            width: 100%;
            padding: 10px 40px 10px 15px;
            border: 2px solid #667eea;
            border-radius: 25px;
            font-size: 14px;
            outline: none;
            transition: all 0.3s;
        }}

        .search-box input:focus {{
            box-shadow: 0 0 10px rgba(102, 126, 234, 0.3);
        }}

        .search-icon {{
            position: absolute;
            right: 15px;
            top: 50%;
            transform: translateY(-50%);
            color: #667eea;
        }}

        .stats {{
            display: flex;
            gap: 20px;
            align-items: center;
        }}

        .stat-item {{
            background: white;
            padding: 10px 20px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            text-align: center;
            min-width: 100px;
        }}

        .stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
            display: block;
        }}

        .stat-label {{
            font-size: 11px;
            color: #6c757d;
            margin-top: 5px;
            display: block;
        }}

        .action-buttons {{
            display: flex;
            gap: 10px;
        }}

        .action-btn {{
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: background 0.2s;
        }}

        .action-btn:hover {{
            background: #5568d3;
        }}

        .filters-panel {{
            background: #f8f9fa;
            padding: 15px 30px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            border-top: 1px solid #e0e0e0;
            display: none;
        }}

        .filters-container {{
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            justify-content: center;
            align-items: center;
        }}

        .filter-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 13px;
            cursor: pointer;
            padding: 8px 15px;
            border-radius: 20px;
            background: white;
            transition: all 0.2s;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}

        .filter-item:hover {{
            transform: translateY(-2px);
            box-shadow: 0 3px 8px rgba(0,0,0,0.15);
        }}

        .filter-item.inactive {{
            opacity: 0.3;
            background: #f5f5f5;
        }}

        .filter-color {{
            width: 16px;
            height: 16px;
            border-radius: 50%;
            border: 2px solid rgba(0,0,0,0.2);
            transition: transform 0.2s;
        }}

        .filter-item:hover .filter-color {{
            transform: scale(1.2);
        }}

        .filter-label {{
            font-weight: 500;
            color: #2c3e50;
        }}

        .file-detail-modal {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }}

        .file-detail-content {{
            background: white;
            border-radius: 15px;
            padding: 30px;
            max-width: 600px;
            width: 90%;
            box-shadow: 0 5px 20px rgba(0,0,0,0.3);
        }}

        .file-detail-content h2 {{
            margin: 0 0 20px 0;
            color: #667eea;
            font-size: 20px;
            word-break: break-all;
        }}

        .file-detail-info {{
            display: flex;
            flex-direction: column;
            gap: 10px;
            margin-bottom: 20px;
        }}

        .file-detail-info div {{
            display: flex;
            flex-direction: column;
            gap: 5px;
        }}

        .file-detail-info strong {{
            color: #667eea;
            font-size: 12px;
            font-weight: 600;
        }}

        .file-detail-info span {{
            color: #2c3e50;
            word-break: break-all;
            white-space: pre-wrap;
            font-size: 13px;
        }}

        .modal-buttons {{
            display: flex;
            gap: 10px;
        }}

        .close-modal, .open-file-btn {{
            flex: 1;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: background 0.2s;
        }}

        .close-modal {{
            background: #6c757d;
            color: white;
        }}

        .close-modal:hover {{
            background: #5a6268;
        }}

        .open-file-btn {{
            background: #667eea;
            color: white;
        }}

        .open-file-btn:hover {{
            background: #5568d3;
        }}

        #tree-container {{
            width: 100%;
            height: calc(100vh - 160px);
            background: white;
            overflow: auto;
        }}

        .node circle {{
            cursor: pointer;
            stroke-width: 2px;
        }}

        .node text {{
            font-size: 13px;
            font-family: 'Segoe UI', sans-serif;
            fill: #2c3e50;
        }}

        .link {{
            fill: none;
            stroke: #ddd;
            stroke-width: 1.5px;
            opacity: 0.4;
            z-index: -1;
        }}

        .tooltip {{
            position: absolute;
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 8px 12px;
            border-radius: 5px;
            font-size: 12px;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.3s;
            z-index: 1000;
        }}

        .highlight {{
            stroke: #f39c12 !important;
            stroke-width: 4px !important;
        }}

        .zoom-controls {{
            position: fixed;
            top: 180px;
            right: 20px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            padding: 5px;
            z-index: 100;
        }}

        .zoom-btn {{
            display: block;
            width: 40px;
            height: 40px;
            border: none;
            background: #667eea;
            color: white;
            font-size: 20px;
            cursor: pointer;
            margin: 5px;
            border-radius: 5px;
            transition: background 0.2s;
        }}

        .zoom-btn:hover {{
            background: #5568d3;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📁 Arborescence - {folder.name}</h1>
        <p>{folder} - Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}</p>
    </div>

    <div class="controls">
        <div class="search-box">
            <input type="text" id="searchInput" placeholder="Rechercher un fichier ou dossier...">
            <span class="search-icon">🔍</span>
        </div>
        <div class="stats">
            <div class="stat-item">
                <span class="stat-value">{self.stats['total_files']}</span>
                <span class="stat-label">Fichiers</span>
            </div>
            <div class="stat-item">
                <span class="stat-value">{self.stats['total_dirs']}</span>
                <span class="stat-label">Dossiers</span>
            </div>
            <div class="stat-item">
                <span class="stat-value">{self.stats['total_size_mb']:.1f} MB</span>
                <span class="stat-label">Taille totale</span>
            </div>
        </div>
        <div class="action-buttons">
            <button class="action-btn" onclick="collapseAll()">➖ Tout Replier</button>
            <button class="action-btn" onclick="expandAll()">➕ Tout Déplier</button>
            <button class="action-btn" onclick="decreaseDepth()">➖ Niveau</button>
            <button class="action-btn" onclick="increaseDepth()">➕ Niveau</button>
            <button class="action-btn" onclick="toggleFilters()">🎯 Filtres</button>
            <button class="action-btn" onclick="exportToHTML()">📥 Exporter</button>
            <button class="action-btn" onclick="resetView()">🔄 Réinitialiser</button>
        </div>
    </div>

    <!-- Panneau de filtres dépliable -->
    <div class="filters-panel" id="filtersPanel" style="display: none;">
        <div class="filters-container">
            <div class="filter-item active" data-filter="folder" onclick="toggleFilter('folder', this)">
                <div class="filter-color" style="background: #667eea;"></div>
                <span class="filter-label">Dossiers</span>
            </div>
            <div class="filter-item active" data-filter="doc" onclick="toggleFilter('doc', this)">
                <div class="filter-color" style="background: #e74c3c;"></div>
                <span class="filter-label">Documents</span>
            </div>
            <div class="filter-item active" data-filter="sheet" onclick="toggleFilter('sheet', this)">
                <div class="filter-color" style="background: #27ae60;"></div>
                <span class="filter-label">Tableurs</span>
            </div>
            <div class="filter-item active" data-filter="email" onclick="toggleFilter('email', this)">
                <div class="filter-color" style="background: #3498db;"></div>
                <span class="filter-label">Emails</span>
            </div>
            <div class="filter-item active" data-filter="image" onclick="toggleFilter('image', this)">
                <div class="filter-color" style="background: #9b59b6;"></div>
                <span class="filter-label">Images</span>
            </div>
            <div class="filter-item active" data-filter="archive" onclick="toggleFilter('archive', this)">
                <div class="filter-color" style="background: #f39c12;"></div>
                <span class="filter-label">Fichiers compressés</span>
            </div>
            <div class="filter-item active" data-filter="cad" onclick="toggleFilter('cad', this)">
                <div class="filter-color" style="background: #e67e22;"></div>
                <span class="filter-label">CAD</span>
            </div>
            <div class="filter-item active" data-filter="other" onclick="toggleFilter('other', this)">
                <div class="filter-color" style="background: #95a5a6;"></div>
                <span class="filter-label">Autres</span>
            </div>
        </div>
    </div>

    <div id="tree-container"></div>

    <div class="zoom-controls">
        <button class="zoom-btn" onclick="zoomIn()">+</button>
        <button class="zoom-btn" onclick="resetZoom()">⟲</button>
        <button class="zoom-btn" onclick="zoomOut()">−</button>
    </div>

    <div class="tooltip" id="tooltip"></div>

    <!-- Modal pour afficher les détails du fichier -->
    <div class="file-detail-modal" id="fileDetailModal" onclick="closeModal()">
        <div class="file-detail-content" onclick="event.stopPropagation()">
            <h2 id="modalFileName"></h2>
            <div class="file-detail-info">
                <div>
                    <strong>Type:</strong>
                    <span id="modalFileType"></span>
                </div>
                <div>
                    <strong>Taille:</strong>
                    <span id="modalFileSize"></span>
                </div>
                <div>
                    <strong>Date:</strong>
                    <span id="modalFileDate"></span>
                </div>
                <div>
                    <strong>Chemin:</strong>
                    <span id="modalFilePath"></span>
                </div>
            </div>
            <div class="modal-buttons">
                <button class="open-file-btn" onclick="openFile()">📂 Ouvrir</button>
                <button class="close-modal" onclick="closeModal()">Fermer</button>
            </div>
        </div>
    </div>

    <script>
        const treeData = {tree_json};

        // Configuration - ARBRE HORIZONTAL avec espacements optimisés
        const margin = {{top: 50, right: 150, bottom: 50, left: 150}};
        const width = Math.max(3000, window.innerWidth * 2);  // Plus large
        const height = Math.max(2000, window.innerHeight * 2);

        // Créer le SVG
        const svg = d3.select("#tree-container")
            .append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom);

        const g = svg.append("g")
            .attr("transform", `translate(${{margin.left}},${{margin.top}})`);

        // Zoom
        const zoom = d3.zoom()
            .scaleExtent([0.1, 3])
            .on("zoom", (event) => {{
                g.attr("transform", event.transform);
            }});

        svg.call(zoom);

        // Créer la hiérarchie - ARBRE HORIZONTAL
        const root = d3.hierarchy(treeData);

        // Tout déplier par défaut (aucun nœud caché)
        // Pas de cache initial des enfants

        const treeLayout = d3.tree()
            .size([height, width - 400])
            .nodeSize([30, 450]);  // Vertical: 30px, Horizontal: 450px (encore plus d'espace)

        // États des filtres
        const activeFilters = {{
            folder: true,
            doc: true,
            sheet: true,
            email: true,
            image: true,
            archive: true,
            cad: true,
            other: true
        }};

        let isolatedNode = null;  // Nœud isolé
        let currentFilePath = null;  // Chemin du fichier actuel dans la modal

        treeLayout(root);

        // Clic sur le fond pour désactiver la surbrillance
        svg.on("click", function(event) {{
            if (event.target === this) {{
                clearHighlight();
            }}
        }});

        // Désactiver la surbrillance uniquement
        function clearHighlight() {{
            g.selectAll("circle").classed("highlight", false);
            g.selectAll(".node").style("opacity", 1);
            g.selectAll(".link").style("opacity", 0.4);
        }}

        // Couleurs selon le type de fichier
        function getColor(node) {{
            if (node.data.type === 'folder') return '#667eea';
            const ext = node.data.ext || '';
            if (['.pdf', '.doc', '.docx'].includes(ext)) return '#e74c3c';
            if (['.xls', '.xlsx'].includes(ext)) return '#27ae60';
            if (['.msg', '.eml'].includes(ext)) return '#3498db';
            if (['.jpg', '.png', '.gif'].includes(ext)) return '#9b59b6';
            if (['.zip', '.rar'].includes(ext)) return '#f39c12';
            if (['.dwg', '.dxf'].includes(ext)) return '#e67e22';
            return '#95a5a6';
        }}

        // Créer un groupe pour les liens (dessiné en premier = arrière-plan)
        const linksGroup = g.append("g").attr("class", "links-group");
        // Créer un groupe pour les nœuds (dessiné en dernier = premier plan)
        const nodesGroup = g.append("g").attr("class", "nodes-group");

        // Dessiner initialement
        update(root);

        function update(source) {{
            // Calculer la nouvelle disposition
            treeLayout(root);

            // Dessiner les liens - HORIZONTAL (dans linksGroup, toujours derrière)
            const links = linksGroup.selectAll(".link")
                .data(root.links(), d => `${{d.source.data.path}}-${{d.target.data.path}}`);

            // Supprimer les anciens liens
            links.exit().remove();

            // Mettre à jour les liens existants
            links.attr("d", d3.linkHorizontal()
                .x(d => d.y)
                .y(d => d.x));

            // Ajouter les nouveaux liens
            links.enter()
                .append("path")
                .attr("class", "link")
                .attr("d", d3.linkHorizontal()
                    .x(d => d.y)
                    .y(d => d.x));

            // Dessiner les noeuds (dans nodesGroup, toujours devant)
            const nodes = nodesGroup.selectAll(".node")
                .data(root.descendants(), d => d.data.path);

            // Supprimer les anciens nœuds
            nodes.exit().remove();

            // Mettre à jour les nœuds existants
            const nodeUpdate = nodes.attr("transform", d => `translate(${{d.y}},${{d.x}})`);

            // Mettre à jour les cercles existants
            nodeUpdate.select("circle")
                .attr("r", d => d.data.type === 'folder' ? 6 : 4)
                .style("fill", d => getColor(d))
                .style("stroke", d => d3.rgb(getColor(d)).darker());

            // Mettre à jour les textes existants
            nodeUpdate.select("text")
                .attr("x", d => d.children || d._children ? -10 : 10)
                .attr("text-anchor", d => d.children || d._children ? "end" : "start")
                .text(d => d.data.name.length > 60 ? d.data.name.substring(0, 60) + '...' : d.data.name);

            // Ajouter les nouveaux nœuds
            const nodeEnter = nodes.enter()
                .append("g")
                .attr("class", "node")
                .attr("transform", d => `translate(${{d.y}},${{d.x}})`);

            nodeEnter.append("circle")
                .attr("r", d => d.data.type === 'folder' ? 6 : 4)
                .style("fill", d => getColor(d))
                .style("stroke", d => d3.rgb(getColor(d)).darker())
                .style("cursor", "pointer")
                .on("mouseover", showTooltip)
                .on("mouseout", hideTooltip)
                .on("click", click);

            nodeEnter.append("text")
                .attr("dy", "0.31em")
                .attr("x", d => d.children || d._children ? -10 : 10)
                .attr("text-anchor", d => d.children || d._children ? "end" : "start")
                .text(d => d.data.name.length > 60 ? d.data.name.substring(0, 60) + '...' : d.data.name)
                .style("font-size", "12px")
                .style("cursor", "pointer")
                .on("click", click);
        }}

        // Clic pour afficher détails (fichiers) ou mettre en surbrillance (dossiers)
        function click(event, d) {{
            event.stopPropagation();

            if (d.data.type === 'file') {{
                // Afficher la modal avec les détails
                showFileDetails(d);
            }} else {{
                // Pour les dossiers : Ctrl+clic pour replier/déplier, clic simple pour surbrillance
                if (event.ctrlKey || event.metaKey) {{
                    // Ctrl+clic : toggle expand/collapse
                    if (d.children) {{
                        d._children = d.children;
                        d.children = null;
                    }} else {{
                        d.children = d._children;
                        d._children = null;
                    }}
                    update(d);
                }} else {{
                    // Clic simple : mettre en surbrillance
                    highlightNode(d);
                }}
            }}
        }}

        // Mettre en surbrillance un nœud et ses descendants
        function highlightNode(d) {{
            // Réinitialiser le highlight
            g.selectAll("circle").classed("highlight", false);
            g.selectAll(".node").style("opacity", 0.2);
            g.selectAll(".link").style("opacity", 0.05);

            // Trouver tous les descendants
            const descendants = d.descendants();
            const descendantSet = new Set(descendants);

            // Trouver tous les ancêtres
            const ancestors = [];
            let parent = d.parent;
            while (parent) {{
                ancestors.push(parent);
                parent = parent.parent;
            }}

            // Combiner descendants et ancêtres
            const nodesToShow = new Set([...descendants, ...ancestors]);

            // Afficher les nœuds sélectionnés
            g.selectAll(".node")
                .filter(function(node) {{ return nodesToShow.has(node); }})
                .style("opacity", 1)
                .selectAll("circle")
                .classed("highlight", node => node === d);

            // Afficher les liens connectés
            g.selectAll(".link")
                .filter(function(link) {{
                    return nodesToShow.has(link.source) && nodesToShow.has(link.target);
                }})
                .style("opacity", 0.4);
        }}

        // Isoler un nœud
        function isolateNode(d) {{
            if (isolatedNode === d) {{
                // Désisoler
                isolatedNode = null;
                g.selectAll(".node").style("opacity", 1);
                g.selectAll(".link").style("opacity", 1);
            }} else {{
                // Isoler ce nœud
                isolatedNode = d;

                // Masquer tous les autres
                g.selectAll(".node").style("opacity", 0.1);
                g.selectAll(".link").style("opacity", 0.1);

                // Afficher le nœud isolé et ses descendants
                const descendants = d.descendants();
                const descendantSet = new Set(descendants);

                g.selectAll(".node")
                    .filter(function(node) {{ return descendantSet.has(node); }})
                    .style("opacity", 1);

                g.selectAll(".link")
                    .filter(function(link) {{ return descendantSet.has(link.target); }})
                    .style("opacity", 1);
            }}
        }}

        // Afficher les détails du fichier
        function showFileDetails(d) {{
            currentFilePath = d.data.path;
            document.getElementById('modalFileName').textContent = d.data.name;
            document.getElementById('modalFileType').textContent = d.data.ext || 'Dossier';
            document.getElementById('modalFileSize').textContent = d.data.size || '-';
            document.getElementById('modalFileDate').textContent = d.data.date || '-';
            document.getElementById('modalFilePath').textContent = d.data.path || '-';
            document.getElementById('fileDetailModal').style.display = 'flex';
        }}

        function closeModal() {{
            document.getElementById('fileDetailModal').style.display = 'none';
            currentFilePath = null;
        }}

        function openFile() {{
            if (currentFilePath) {{
                // Ouvrir le fichier dans un nouvel onglet
                const fileUrl = 'file:///' + currentFilePath.replace(/\\\\/g, '/');
                window.open(fileUrl, '_blank');
            }}
        }}

        // Tooltip avec date
        const tooltip = d3.select("#tooltip");

        function showTooltip(event, d) {{
            let content = `<strong>${{d.data.name}}</strong><br>`;
            content += `Type: ${{d.data.type === 'folder' ? 'Dossier 📁' : 'Fichier 📄'}}<br>`;
            if (d.data.size) content += `Taille: ${{d.data.size}}<br>`;
            if (d.data.date) content += `Date: ${{d.data.date}}`;

            tooltip
                .style("opacity", 1)
                .html(content)
                .style("left", (event.pageX + 10) + "px")
                .style("top", (event.pageY - 10) + "px");
        }}

        function hideTooltip() {{
            tooltip.style("opacity", 0);
        }}

        // Recherche améliorée
        const searchInput = document.getElementById('searchInput');
        searchInput.addEventListener('input', (e) => {{
            const searchTerm = e.target.value.toLowerCase();

            // Réinitialiser le highlight
            g.selectAll("circle").classed("highlight", false);
            g.selectAll(".node").style("opacity", 1);
            g.selectAll(".link").style("opacity", 0.4);

            if (searchTerm.length > 0) {{
                // Déplier tous les niveaux pour la recherche
                expandAll();

                // Trouver les nœuds correspondants
                const matchingNodes = [];
                root.descendants().forEach(d => {{
                    if (d.data.name.toLowerCase().includes(searchTerm)) {{
                        matchingNodes.push(d);
                    }}
                }});

                if (matchingNodes.length > 0) {{
                    // Masquer tout
                    g.selectAll(".node").style("opacity", 0.1);
                    g.selectAll(".link").style("opacity", 0.05);

                    // Afficher les nœuds correspondants et leurs ancêtres
                    const nodesToShow = new Set();
                    matchingNodes.forEach(d => {{
                        // Ajouter le nœud lui-même
                        nodesToShow.add(d);
                        // Ajouter tous ses ancêtres
                        let parent = d.parent;
                        while (parent) {{
                            nodesToShow.add(parent);
                            parent = parent.parent;
                        }}
                    }});

                    // Afficher les nœuds sélectionnés
                    g.selectAll(".node")
                        .filter(function(node) {{ return nodesToShow.has(node); }})
                        .style("opacity", 1)
                        .selectAll("circle")
                        .classed("highlight", d => matchingNodes.includes(d));

                    // Afficher les liens connectés
                    g.selectAll(".link")
                        .filter(function(link) {{ return nodesToShow.has(link.target); }})
                        .style("opacity", 0.4);
                }}
            }}
        }});

        // Contrôles zoom
        let currentScale = 1;

        function zoomIn() {{
            // Zoomer sur le centre de la fenêtre
            const svgRect = svg.node().getBoundingClientRect();
            const centerX = svgRect.width / 2;
            const centerY = svgRect.height / 2;

            svg.transition()
                .duration(300)
                .call(zoom.scaleBy, 1.3, [centerX, centerY]);
        }}

        function zoomOut() {{
            // Dézoomer sur le centre de la fenêtre
            const svgRect = svg.node().getBoundingClientRect();
            const centerX = svgRect.width / 2;
            const centerY = svgRect.height / 2;

            svg.transition()
                .duration(300)
                .call(zoom.scaleBy, 0.77, [centerX, centerY]);
        }}

        function resetZoom() {{
            // Centrer sur tout ce qui est affiché
            fitToScreen();
        }}

        // Expand / Collapse All
        function expandAll() {{
            root.descendants().forEach(d => {{
                if (d._children) {{
                    d.children = d._children;
                    d._children = null;
                }}
            }});
            update(root);
        }}

        function collapseAll() {{
            root.descendants().forEach(d => {{
                if (d.depth > 0 && d.children) {{
                    d._children = d.children;
                    d.children = null;
                }}
            }});
            update(root);
        }}

        // Toggle filtre (clic sur légende)
        function toggleFilter(filterType, element) {{
            activeFilters[filterType] = !activeFilters[filterType];

            // Mettre à jour l'apparence
            if (activeFilters[filterType]) {{
                element.classList.add('active');
                element.classList.remove('inactive');
            }} else {{
                element.classList.remove('active');
                element.classList.add('inactive');
            }}

            // Appliquer les filtres
            applyFilters();
        }}

        function applyFilters() {{
            // Déplier tous les niveaux lors du filtrage
            expandAll();

            // Réinitialiser
            g.selectAll(".node").style("opacity", 1).style("display", "block");
            g.selectAll(".link").style("opacity", 0.4).style("display", "block");

            // Filtrer selon les types actifs
            const nodesToHide = new Set();

            root.descendants().forEach(d => {{
                let shouldHide = false;

                if (d.data.type === 'folder') {{
                    shouldHide = !activeFilters.folder;
                }} else {{
                    const ext = d.data.ext || '';
                    if (['.pdf', '.doc', '.docx'].includes(ext)) shouldHide = !activeFilters.doc;
                    else if (['.xls', '.xlsx'].includes(ext)) shouldHide = !activeFilters.sheet;
                    else if (['.msg', '.eml'].includes(ext)) shouldHide = !activeFilters.email;
                    else if (['.jpg', '.png', '.gif'].includes(ext)) shouldHide = !activeFilters.image;
                    else if (['.zip', '.rar'].includes(ext)) shouldHide = !activeFilters.archive;
                    else if (['.dwg', '.dxf'].includes(ext)) shouldHide = !activeFilters.cad;
                    else shouldHide = !activeFilters.other;
                }}

                if (shouldHide) {{
                    nodesToHide.add(d);
                }}
            }});

            // Masquer les nœuds filtrés
            g.selectAll(".node")
                .filter(function(node) {{ return nodesToHide.has(node); }})
                .style("display", "none");

            // Masquer les liens vers les nœuds cachés
            g.selectAll(".link")
                .filter(function(link) {{ return nodesToHide.has(link.target); }})
                .style("display", "none");
        }}

        // Variable pour suivre le niveau de dépliage actuel
        let currentDepthLevel = 100; // Par défaut tout déplié

        // Déplier jusqu'à un niveau
        function expandToLevel(maxLevel) {{
            currentDepthLevel = maxLevel;
            root.descendants().forEach(d => {{
                if (d.depth < maxLevel) {{
                    if (d._children) {{
                        d.children = d._children;
                        d._children = null;
                    }}
                }} else {{
                    if (d.children) {{
                        d._children = d.children;
                        d.children = null;
                    }}
                }}
            }});
            update(root);
        }}

        // Augmenter le niveau de dépliage
        function increaseDepth() {{
            currentDepthLevel++;
            expandToLevel(currentDepthLevel);
        }}

        // Diminuer le niveau de dépliage
        function decreaseDepth() {{
            if (currentDepthLevel > 1) {{
                currentDepthLevel--;
                expandToLevel(currentDepthLevel);
            }}
        }}

        // Réinitialiser la vue complètement
        function resetView() {{
            // Réinitialiser les états
            isolatedNode = null;

            // Désactiver surbrillance
            clearHighlight();

            // Vider la recherche
            document.getElementById('searchInput').value = '';

            // Réactiver tous les filtres
            Object.keys(activeFilters).forEach(key => {{
                activeFilters[key] = true;
            }});

            // Mettre à jour l'UI des filtres
            document.querySelectorAll('.filter-item').forEach(item => {{
                item.classList.add('active');
                item.classList.remove('inactive');
            }});

            // Réafficher tous les nœuds
            g.selectAll(".node").style("display", "block");
            g.selectAll(".link").style("display", "block");

            // Tout déplier
            expandAll();

            // Centrer et ajuster le zoom pour voir toute l'arborescence
            fitToScreen();
        }}

        // Ajuster la vue pour voir toute l'arborescence
        function fitToScreen() {{
            const bounds = g.node().getBBox();
            const parent = svg.node().getBoundingClientRect();
            const fullWidth = bounds.width;
            const fullHeight = bounds.height;
            const midX = bounds.x + fullWidth / 2;
            const midY = bounds.y + fullHeight / 2;

            const scale = 0.8 / Math.max(fullWidth / parent.width, fullHeight / parent.height);
            const translate = [parent.width / 2 - scale * midX, parent.height / 2 - scale * midY];

            svg.transition()
                .duration(750)
                .call(zoom.transform, d3.zoomIdentity
                    .translate(translate[0], translate[1])
                    .scale(scale));

            currentScale = scale;
        }}

        // Export HTML
        function exportToHTML() {{
            const htmlContent = document.documentElement.outerHTML;
            const blob = new Blob([htmlContent], {{type: 'text/html'}});
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = 'arborescence_export.html';
            link.click();
            URL.revokeObjectURL(url);
        }}

        // Toggle panneau filtres
        function toggleFilters() {{
            const panel = document.getElementById('filtersPanel');
            if (panel.style.display === 'none' || panel.style.display === '') {{
                panel.style.display = 'block';
            }} else {{
                panel.style.display = 'none';
            }}
        }}
    </script>
</body>
</html>"""
