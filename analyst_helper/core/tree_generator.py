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
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #e8eaf0;
            overflow: hidden;
            height: 100vh;
        }}

        .header {{
            background: #ffffff;
            border-bottom: 2px solid #c5cae0;
            padding: 14px 28px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        }}

        .header-title {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .header h1 {{
            font-size: 18px;
            font-weight: 700;
            color: #0a0d1a;
        }}

        .header-info {{
            font-size: 12px;
            color: #4a5568;
            font-weight: 500;
        }}

        .controls {{
            background: #f7f8fc;
            border-bottom: 2px solid #d1d5e0;
            padding: 12px 28px;
            display: flex;
            gap: 18px;
            align-items: center;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }}

        .search-box {{
            flex: 1;
            max-width: 320px;
            position: relative;
        }}

        .search-box input {{
            width: 100%;
            padding: 8px 36px 8px 12px;
            border: 2px solid #c5cae0;
            border-radius: 6px;
            font-size: 13px;
            outline: none;
            transition: border-color 0.2s;
            background: white;
            font-weight: 500;
        }}

        .search-box input:focus {{
            border-color: #5568d3;
            box-shadow: 0 0 0 3px rgba(85,104,211,0.1);
        }}

        .search-icon {{
            position: absolute;
            right: 12px;
            top: 50%;
            transform: translateY(-50%);
            color: #6b7280;
            font-size: 15px;
        }}

        .stats {{
            display: flex;
            gap: 20px;
            margin-left: auto;
        }}

        .stat-item {{
            text-align: center;
            padding: 0 16px;
            border-right: 2px solid #d1d5e0;
        }}

        .stat-item:last-child {{
            border-right: none;
        }}

        .stat-value {{
            font-size: 18px;
            font-weight: 700;
            color: #0a0d1a;
            display: block;
        }}

        .stat-label {{
            font-size: 10px;
            color: #6b7280;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            font-weight: 600;
            margin-top: 2px;
        }}

        .action-buttons {{
            display: flex;
            gap: 8px;
        }}

        .btn-group {{
            display: flex;
            gap: 0;
            border: 2px solid #c5cae0;
            border-radius: 6px;
            overflow: hidden;
            background: white;
        }}

        .action-btn {{
            background: white;
            color: #1a202c;
            border: none;
            padding: 8px 14px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 600;
            transition: all 0.15s;
            white-space: nowrap;
        }}

        .btn-group .action-btn {{
            border-radius: 0;
            border-right: 2px solid #c5cae0;
        }}

        .btn-group .action-btn:last-child {{
            border-right: none;
        }}

        .action-btn:hover {{
            background: #e8eaf0;
        }}

        .action-btn.primary {{
            background: #5568d3;
            color: white;
            border: 2px solid #5568d3;
            border-radius: 6px;
        }}

        .action-btn.primary:hover {{
            background: #4556b8;
            border-color: #4556b8;
        }}

        .action-btn.filters {{
            background: white;
            color: #1a202c;
            border: 2px solid #c5cae0;
            border-radius: 6px;
        }}

        .action-btn.filters:hover {{
            background: #e8eaf0;
        }}

        .filters-panel {{
            background: #f0f2f8;
            padding: 14px 28px;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.05);
            border-bottom: 2px solid #c5cae0;
            display: none;
        }}

        .filters-container {{
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
            justify-content: flex-start;
            align-items: center;
        }}

        .filter-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 13px;
            cursor: pointer;
            padding: 6px 14px;
            border-radius: 6px;
            background: white;
            transition: all 0.2s;
            border: 2px solid #c5cae0;
            font-weight: 600;
        }}

        .filter-item:hover {{
            transform: translateY(-1px);
            box-shadow: 0 2px 6px rgba(0,0,0,0.12);
        }}

        .filter-item.inactive {{
            opacity: 0.4;
            background: #e8eaf0;
            border-color: #d1d5e0;
        }}

        .filter-color {{
            width: 14px;
            height: 14px;
            border-radius: 50%;
            border: 2px solid rgba(0,0,0,0.3);
        }}

        .filter-label {{
            font-weight: 600;
            color: #1a202c;
        }}

        #tree-container {{
            width: 100%;
            height: calc(100vh - 116px);
            background: #ffffff;
            overflow: hidden;
            position: relative;
            border-top: 1px solid #e8eaf0;
        }}

        .node circle {{
            cursor: pointer;
            stroke-width: 2px;
            transition: r 0.2s, stroke-width 0.2s;
        }}

        .node:hover circle {{
            stroke-width: 3px;
        }}

        .node text {{
            font-size: 12px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            fill: #0a0d1a;
            pointer-events: none;
            font-weight: 500;
        }}

        .link {{
            fill: none;
            stroke: #b0b5c8;
            stroke-width: 1.5px;
            opacity: 0.7;
        }}

        .tooltip {{
            position: absolute;
            background: rgba(10,13,26,0.92);
            color: white;
            padding: 10px 14px;
            border-radius: 6px;
            font-size: 12px;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.2s;
            z-index: 1000;
            max-width: 320px;
            font-weight: 500;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }}

        .highlight {{
            stroke: #5568d3 !important;
            stroke-width: 4px !important;
        }}

        .zoom-controls {{
            position: fixed;
            bottom: 28px;
            right: 28px;
            background: white;
            border: 2px solid #c5cae0;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }}

        .zoom-btn {{
            width: 44px;
            height: 44px;
            border: none;
            background: white;
            color: #1a202c;
            font-size: 20px;
            font-weight: 700;
            cursor: pointer;
            transition: background 0.15s;
            display: flex;
            align-items: center;
            justify-content: center;
            border-bottom: 2px solid #c5cae0;
        }}

        .zoom-btn:last-child {{
            border-bottom: none;
        }}

        .zoom-btn:hover {{
            background: #e8eaf0;
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
            border-radius: 12px;
            padding: 28px;
            max-width: 540px;
            width: 90%;
            box-shadow: 0 12px 40px rgba(0,0,0,0.3);
            border: 2px solid #c5cae0;
        }}

        .file-detail-content h2 {{
            margin: 0 0 18px 0;
            color: #0a0d1a;
            font-size: 18px;
            font-weight: 700;
            word-break: break-all;
        }}

        .file-detail-info {{
            display: flex;
            flex-direction: column;
            gap: 14px;
            margin-bottom: 22px;
        }}

        .file-detail-info div {{
            display: flex;
            flex-direction: column;
            gap: 6px;
        }}

        .file-detail-info strong {{
            color: #6b7280;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.8px;
        }}

        .file-detail-info span {{
            color: #0a0d1a;
            word-break: break-all;
            font-size: 13px;
            font-weight: 500;
        }}

        .modal-buttons {{
            display: flex;
            gap: 10px;
        }}

        .close-modal, .open-file-btn {{
            flex: 1;
            border: none;
            padding: 11px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: background 0.15s;
        }}

        .close-modal {{
            background: #e8eaf0;
            color: #1a202c;
            border: 2px solid #c5cae0;
        }}

        .close-modal:hover {{
            background: #d1d5e0;
        }}

        .open-file-btn {{
            background: #5568d3;
            color: white;
            border: 2px solid #5568d3;
        }}

        .open-file-btn:hover {{
            background: #4556b8;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="header-title">
            <h1>{folder.name}</h1>
            <span class="header-info">• {datetime.now().strftime('%d/%m/%Y %H:%M')}</span>
        </div>
    </div>

    <div class="controls">
        <div class="search-box">
            <input type="text" id="searchInput" placeholder="Rechercher...">
            <span class="search-icon">⌕</span>
        </div>

        <div class="btn-group">
            <button class="action-btn" onclick="decreaseDepth()" title="Réduire la profondeur">−</button>
            <button class="action-btn" onclick="increaseDepth()" title="Augmenter la profondeur">+</button>
        </div>

        <div class="btn-group">
            <button class="action-btn" onclick="collapseAll()">Replier</button>
            <button class="action-btn" onclick="expandAll()">Déplier</button>
        </div>

        <button class="action-btn filters" onclick="toggleFilters()">🎯 Filtres</button>
        <button class="action-btn" onclick="exportToHTML()">📥 Export</button>
        <button class="action-btn primary" onclick="resetView()">Réinitialiser</button>

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
                <span class="stat-label">Taille</span>
            </div>
        </div>
    </div>

    <div class="filters-panel" id="filtersPanel">
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
        <button class="zoom-btn" onclick="zoomIn()" title="Zoom avant">+</button>
        <button class="zoom-btn" onclick="resetZoom()" title="Réinitialiser le zoom">⟲</button>
        <button class="zoom-btn" onclick="zoomOut()" title="Zoom arrière">−</button>
    </div>

    <div class="tooltip" id="tooltip"></div>

    <div class="file-detail-modal" id="fileDetailModal" onclick="closeModal()">
        <div class="file-detail-content" onclick="event.stopPropagation()">
            <h2 id="modalFileName"></h2>
            <div class="file-detail-info">
                <div>
                    <strong>Type</strong>
                    <span id="modalFileType"></span>
                </div>
                <div>
                    <strong>Taille</strong>
                    <span id="modalFileSize"></span>
                </div>
                <div>
                    <strong>Date de modification</strong>
                    <span id="modalFileDate"></span>
                </div>
                <div>
                    <strong>Chemin</strong>
                    <span id="modalFilePath"></span>
                </div>
            </div>
            <div class="modal-buttons">
                <button class="close-modal" onclick="closeModal()">Fermer</button>
                <button class="open-file-btn" onclick="openFile()">Ouvrir le fichier</button>
            </div>
        </div>
    </div>

    <script>
        const treeData = {tree_json};

        // Configuration - Espacement réduit
        const margin = {{top: 20, right: 200, bottom: 20, left: 100}};
        const width = 5000;
        const height = 3000;

        const container = d3.select("#tree-container");

        const svg = container
            .append("svg")
            .attr("width", width)
            .attr("height", height);

        const g = svg.append("g")
            .attr("transform", `translate(${{margin.left}},${{margin.top}})`);

        // Zoom avec filtre pour Ctrl+Scroll
        const zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .filter((event) => {{
                // Bloquer le zoom par défaut si Ctrl est pressé (pour gérer le scroll vertical)
                if (event.type === 'wheel' && event.ctrlKey) {{
                    return false;
                }}
                return true;
            }})
            .on("zoom", (event) => {{
                g.attr("transform", event.transform);
            }});

        svg.call(zoom);

        // Ctrl+Scroll pour défilement vertical
        svg.on('wheel', function(event) {{
            if (event.ctrlKey) {{
                event.preventDefault();
                event.stopPropagation();

                const transform = d3.zoomTransform(svg.node());
                const delta = event.deltaY * 1.5; // Vitesse de défilement

                // Déplacer verticalement
                svg.transition()
                    .duration(100)
                    .call(zoom.transform, d3.zoomIdentity
                        .translate(transform.x, transform.y - delta)
                        .scale(transform.k));
            }}
        }}, {{ passive: false }});

        // Hiérarchie
        const root = d3.hierarchy(treeData);

        // Initialiser _children pour permettre le contrôle de profondeur
        // mais garder tout déplié au départ (children n'est pas null)
        root.descendants().forEach(d => {{
            if (d.children && d.children.length > 0) {{
                d._children = d.children; // Sauvegarder une référence
            }}
        }});

        const treeLayout = d3.tree()
            .size([height - margin.top - margin.bottom, width - margin.left - margin.right])
            .nodeSize([15, 450]); // Espacement: 15px vertical, 450px horizontal - très compact

        let currentFilePath = null;
        let currentDepthLevel = 999; // Max par défaut

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

        // Créer les groupes pour les liens et nœuds
        const linksGroup = g.append("g").attr("class", "links-group");
        const nodesGroup = g.append("g").attr("class", "nodes-group");

        // Dessiner l'arbre initial (tout déplié)
        update(root);

        // Mise à jour de l'arbre
        function update(source) {{
            treeLayout(root);

            // Appliquer les filtres après mise à jour
            applyFiltersToNodes();

            // Liens
            const links = linksGroup.selectAll(".link")
                .data(root.links(), d => d.target.data.path);

            links.exit().remove();

            links.attr("d", d3.linkHorizontal()
                .x(d => d.y)
                .y(d => d.x));

            links.enter()
                .append("path")
                .attr("class", "link")
                .attr("d", d3.linkHorizontal()
                    .x(d => d.y)
                    .y(d => d.x));

            // Nœuds
            const nodes = nodesGroup.selectAll(".node")
                .data(root.descendants(), d => d.data.path);

            nodes.exit().remove();

            const nodeUpdate = nodes.attr("transform", d => `translate(${{d.y}},${{d.x}})`);

            nodeUpdate.select("circle")
                .attr("r", d => d.data.type === 'folder' ? 5 : 3)
                .style("fill", d => getColor(d))
                .style("stroke", d => d3.rgb(getColor(d)).darker(0.8));

            nodeUpdate.select("text")
                .attr("x", d => (d.children || d._children) ? -8 : 8)
                .attr("text-anchor", d => (d.children || d._children) ? "end" : "start")
                .text(d => d.data.name.length > 48 ? d.data.name.substring(0, 48) + '...' : d.data.name);

            const nodeEnter = nodes.enter()
                .append("g")
                .attr("class", "node")
                .attr("transform", d => `translate(${{d.y}},${{d.x}})`);

            nodeEnter.append("circle")
                .attr("r", d => d.data.type === 'folder' ? 5 : 3)
                .style("fill", d => getColor(d))
                .style("stroke", d => d3.rgb(getColor(d)).darker(0.8))
                .on("mouseover", showTooltip)
                .on("mouseout", hideTooltip)
                .on("click", click)
                .on("dblclick", (event) => {{ event.stopPropagation(); event.preventDefault(); }});

            nodeEnter.append("text")
                .attr("dy", "0.31em")
                .attr("x", d => (d.children || d._children) ? -8 : 8)
                .attr("text-anchor", d => (d.children || d._children) ? "end" : "start")
                .text(d => d.data.name.length > 48 ? d.data.name.substring(0, 48) + '...' : d.data.name)
                .on("click", click)
                .on("dblclick", (event) => {{ event.stopPropagation(); event.preventDefault(); }});
        }}

        function getColor(node) {{
            if (node.data.type === 'folder') return '#667eea';
            const ext = node.data.ext || '';
            if (['.pdf', '.doc', '.docx', '.odt'].includes(ext)) return '#e74c3c';
            if (['.xls', '.xlsx', '.csv', '.ods'].includes(ext)) return '#27ae60';
            if (['.msg', '.eml'].includes(ext)) return '#3498db';
            if (['.jpg', '.png', '.gif', '.bmp'].includes(ext)) return '#9b59b6';
            if (['.zip', '.rar', '.7z'].includes(ext)) return '#f39c12';
            if (['.dwg', '.dxf'].includes(ext)) return '#e67e22';
            return '#95a5a6';
        }}

        function click(event, d) {{
            event.stopPropagation();
            if (d.data.type === 'file') {{
                // Ctrl+clic sur fichier : ouvrir directement dans un onglet
                if (event.ctrlKey || event.metaKey) {{
                    const fileUrl = 'file:///' + d.data.path.replace(/\\\\/g, '/');
                    window.open(fileUrl, '_blank');
                }} else {{
                    // Clic simple : afficher les détails
                    showFileDetails(d);
                }}
            }} else {{
                // INVERSÉ: Ctrl+clic pour déplier/replier, clic simple pour surbrillance
                if (event.ctrlKey || event.metaKey) {{
                    // Ctrl+clic : toggle expand/collapse
                    if (d.children) {{
                        d._children = d.children;
                        d.children = null;
                    }} else if (d._children) {{
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
            g.selectAll(".node").style("opacity", 0.15); // Très faible opacité
            g.selectAll(".link").style("opacity", 0.1);

            // Trouver tous les descendants
            const descendants = d.descendants();

            // Trouver tous les ancêtres
            const ancestors = [];
            let parent = d.parent;
            while (parent) {{
                ancestors.push(parent);
                parent = parent.parent;
            }}

            // Combiner descendants et ancêtres
            const nodesToShow = new Set([...descendants, ...ancestors]);

            // Afficher les nœuds sélectionnés avec pleine opacité
            g.selectAll(".node")
                .filter(node => nodesToShow.has(node))
                .style("opacity", 1)
                .selectAll("circle")
                .classed("highlight", node => node === d);

            // Afficher les liens connectés avec bonne opacité
            g.selectAll(".link")
                .filter(link => nodesToShow.has(link.source) && nodesToShow.has(link.target))
                .style("opacity", 0.8);
        }}

        // Clic sur le fond pour désactiver la surbrillance
        svg.on("click", function(event) {{
            if (event.target === this || event.target.tagName === 'svg') {{
                clearHighlight();
            }}
        }});

        function clearHighlight() {{
            g.selectAll("circle").classed("highlight", false);
            g.selectAll(".node").style("opacity", 1);
            g.selectAll(".link").style("opacity", 0.7);
        }}

        const tooltip = d3.select("#tooltip");

        function showTooltip(event, d) {{
            let content = `<strong>${{d.data.name}}</strong><br>`;
            content += `Type: ${{d.data.type === 'folder' ? 'Dossier' : 'Fichier'}}<br>`;
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
                const fileUrl = 'file:///' + currentFilePath.replace(/\\\\/g, '/');
                window.open(fileUrl, '_blank');
            }}
        }}

        // Recherche avec meilleur contraste
        document.getElementById('searchInput').addEventListener('input', (e) => {{
            const searchTerm = e.target.value.toLowerCase();

            g.selectAll("circle").classed("highlight", false);
            g.selectAll(".node").style("opacity", 1);
            g.selectAll(".link").style("opacity", 0.7);

            if (searchTerm.length > 0) {{
                const matchingNodes = [];
                root.descendants().forEach(d => {{
                    if (d.data.name.toLowerCase().includes(searchTerm)) {{
                        matchingNodes.push(d);
                    }}
                }});

                if (matchingNodes.length > 0) {{
                    // Réduire l'opacité des non-correspondants
                    g.selectAll(".node").style("opacity", 0.15);
                    g.selectAll(".link").style("opacity", 0.1);

                    const nodesToShow = new Set();
                    matchingNodes.forEach(d => {{
                        nodesToShow.add(d);
                        let parent = d.parent;
                        while (parent) {{
                            nodesToShow.add(parent);
                            parent = parent.parent;
                        }}
                    }});

                    // Afficher les correspondants avec pleine opacité
                    g.selectAll(".node")
                        .filter(node => nodesToShow.has(node))
                        .style("opacity", 1)
                        .selectAll("circle")
                        .classed("highlight", d => matchingNodes.includes(d));

                    // Afficher les liens vers les correspondants
                    g.selectAll(".link")
                        .filter(link => nodesToShow.has(link.target))
                        .style("opacity", 0.8);
                }}
            }}
        }});

        // Contrôles de zoom - CORRIGÉS pour zoomer au centre du viewport
        function zoomIn() {{
            const transform = d3.zoomTransform(svg.node());
            const containerRect = container.node().getBoundingClientRect();

            // Centre du viewport visible
            const centerX = containerRect.width / 2;
            const centerY = containerRect.height / 2;

            // Point dans l'espace du graphique correspondant au centre du viewport
            const pointX = (centerX - transform.x) / transform.k;
            const pointY = (centerY - transform.y) / transform.k;

            const newScale = transform.k * 1.3;

            // Nouvelles coordonnées pour garder le même point au centre
            const newX = centerX - pointX * newScale;
            const newY = centerY - pointY * newScale;

            svg.transition()
                .duration(300)
                .call(zoom.transform, d3.zoomIdentity
                    .translate(newX, newY)
                    .scale(newScale));
        }}

        function zoomOut() {{
            const transform = d3.zoomTransform(svg.node());
            const containerRect = container.node().getBoundingClientRect();

            // Centre du viewport visible
            const centerX = containerRect.width / 2;
            const centerY = containerRect.height / 2;

            // Point dans l'espace du graphique correspondant au centre du viewport
            const pointX = (centerX - transform.x) / transform.k;
            const pointY = (centerY - transform.y) / transform.k;

            const newScale = transform.k * 0.77;

            // Nouvelles coordonnées pour garder le même point au centre
            const newX = centerX - pointX * newScale;
            const newY = centerY - pointY * newScale;

            svg.transition()
                .duration(300)
                .call(zoom.transform, d3.zoomIdentity
                    .translate(newX, newY)
                    .scale(newScale));
        }}

        function resetZoom() {{
            fitToScreen();
        }}

        function fitToScreen() {{
            const bounds = g.node().getBBox();
            const containerRect = container.node().getBoundingClientRect();

            const scale = 0.9 / Math.max(bounds.width / containerRect.width, bounds.height / containerRect.height);
            const translateX = containerRect.width / 2 - scale * (bounds.x + bounds.width / 2);
            const translateY = containerRect.height / 2 - scale * (bounds.y + bounds.height / 2);

            svg.transition()
                .duration(750)
                .call(zoom.transform, d3.zoomIdentity
                    .translate(translateX, translateY)
                    .scale(scale));
        }}

        function expandAll() {{
            // CORRECTION: vraiment tout déplier
            root.each(d => {{
                if (d._children) {{
                    d.children = d._children;
                    d._children = null;
                }}
            }});
            currentDepthLevel = 999;
            update(root);
        }}

        function collapseAll() {{
            root.descendants().forEach(d => {{
                if (d.depth > 0 && d.children) {{
                    d._children = d.children;
                    d.children = null;
                }}
            }});
            currentDepthLevel = 1;
            update(root);
        }}

        function getMaxDepth() {{
            let maxDepth = 0;
            root.each(d => {{
                if (d.depth > maxDepth) maxDepth = d.depth;
            }});
            return maxDepth;
        }}

        function expandToLevel(level) {{
            root.descendants().forEach(d => {{
                if (d.children || d._children) {{
                    if (d.depth < level) {{
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
                }}
            }});
            currentDepthLevel = level;
            update(root);
        }}

        function increaseDepth() {{
            const maxDepth = getMaxDepth();
            if (currentDepthLevel <= maxDepth) {{
                currentDepthLevel++;
                expandToLevel(currentDepthLevel);
            }}
        }}

        function decreaseDepth() {{
            const maxDepth = getMaxDepth();

            // Si on est au niveau Max (999), passer au niveau réel maximum
            if (currentDepthLevel >= maxDepth) {{
                currentDepthLevel = maxDepth;
            }}

            // Puis décrémenter normalement si > 1
            if (currentDepthLevel > 1) {{
                currentDepthLevel--;
                expandToLevel(currentDepthLevel);
            }}
        }}

        function toggleFilters() {{
            const panel = document.getElementById('filtersPanel');
            if (panel.style.display === 'none' || panel.style.display === '') {{
                panel.style.display = 'block';
            }} else {{
                panel.style.display = 'none';
            }}
        }}

        function toggleFilter(filterType, element) {{
            activeFilters[filterType] = !activeFilters[filterType];

            if (activeFilters[filterType]) {{
                element.classList.add('active');
                element.classList.remove('inactive');
            }} else {{
                element.classList.remove('active');
                element.classList.add('inactive');
            }}

            applyFiltersToNodes();
        }}

        function applyFiltersToNodes() {{
            const nodesToHide = new Set();

            root.descendants().forEach(d => {{
                let shouldHide = false;

                if (d.data.type === 'folder') {{
                    shouldHide = !activeFilters.folder;
                }} else {{
                    const ext = d.data.ext || '';
                    if (['.pdf', '.doc', '.docx', '.odt'].includes(ext)) shouldHide = !activeFilters.doc;
                    else if (['.xls', '.xlsx', '.csv', '.ods'].includes(ext)) shouldHide = !activeFilters.sheet;
                    else if (['.msg', '.eml'].includes(ext)) shouldHide = !activeFilters.email;
                    else if (['.jpg', '.png', '.gif', '.bmp'].includes(ext)) shouldHide = !activeFilters.image;
                    else if (['.zip', '.rar', '.7z'].includes(ext)) shouldHide = !activeFilters.archive;
                    else if (['.dwg', '.dxf'].includes(ext)) shouldHide = !activeFilters.cad;
                    else shouldHide = !activeFilters.other;
                }}

                if (shouldHide) {{
                    nodesToHide.add(d);
                }}
            }});

            // Appliquer le filtrage visuel
            g.selectAll(".node")
                .style("display", function(d) {{
                    return nodesToHide.has(d) ? "none" : "block";
                }});

            g.selectAll(".link")
                .style("display", function(d) {{
                    return nodesToHide.has(d.target) ? "none" : "block";
                }});
        }}

        function resetView() {{
            document.getElementById('searchInput').value = '';
            g.selectAll("circle").classed("highlight", false);
            g.selectAll(".node").style("opacity", 1).style("display", "block");
            g.selectAll(".link").style("opacity", 0.7).style("display", "block");

            // Réactiver tous les filtres
            Object.keys(activeFilters).forEach(key => {{
                activeFilters[key] = true;
            }});
            document.querySelectorAll('.filter-item').forEach(item => {{
                item.classList.add('active');
                item.classList.remove('inactive');
            }});

            expandAll();
            setTimeout(fitToScreen, 100);
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

        // Initialiser la vue (tout déplié)
        setTimeout(() => {{
            fitToScreen();
        }}, 100);
    </script>
</body>
</html>"""
