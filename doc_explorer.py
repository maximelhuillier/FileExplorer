#!/usr/bin/env python3
"""
DOC EXPLORER pour ARGOS
Interface Moderne et Esthétique
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk
import threading
import os
import sys
import webbrowser
import re
import time
import subprocess
from pathlib import Path


class RoundedButton(tk.Canvas):
    """Bouton avec bords arrondis"""

    def __init__(self, parent, text, command, bg_color, hover_color, text_color='white', **kwargs):
        super().__init__(parent, height=55, bd=0, highlightthickness=0, bg=parent['bg'], **kwargs)
        self.command = command
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.text = text
        self.is_enabled = True

        self.draw_button(bg_color)

        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)
        self.bind('<Button-1>', self.on_click)

    def draw_button(self, color):
        """Dessine le bouton arrondi"""
        self.delete('all')
        width = self.winfo_reqwidth() or 400

        # Bouton arrondi
        self.create_rounded_rect(5, 5, width-5, 50, radius=15, fill=color, outline='')

        # Texte
        self.create_text(width/2, 27, text=self.text, fill=self.text_color,
                        font=('Segoe UI', 12, 'bold'))

    def create_rounded_rect(self, x1, y1, x2, y2, radius=25, **kwargs):
        """Crée un rectangle arrondi"""
        points = [x1+radius, y1,
                 x1+radius, y1,
                 x2-radius, y1,
                 x2-radius, y1,
                 x2, y1,
                 x2, y1+radius,
                 x2, y1+radius,
                 x2, y2-radius,
                 x2, y2-radius,
                 x2, y2,
                 x2-radius, y2,
                 x2-radius, y2,
                 x1+radius, y2,
                 x1+radius, y2,
                 x1, y2,
                 x1, y2-radius,
                 x1, y2-radius,
                 x1, y1+radius,
                 x1, y1+radius,
                 x1, y1]
        return self.create_polygon(points, smooth=True, **kwargs)

    def on_enter(self, event):
        if self.is_enabled:
            self.draw_button(self.hover_color)
            self.config(cursor='hand2')

    def on_leave(self, event):
        if self.is_enabled:
            self.draw_button(self.bg_color)
            self.config(cursor='')

    def on_click(self, event):
        if self.is_enabled and self.command:
            self.command()

    def set_state(self, state):
        self.is_enabled = (state == 'normal')
        if not self.is_enabled:
            self.draw_button('#e0e0e0')
        else:
            self.draw_button(self.bg_color)


class DocExplorerGUI:
    """DOC EXPLORER pour ARGOS - Interface Moderne"""

    # Regex compilé une seule fois au niveau de la classe
    NON_ASCII_PATTERN = re.compile(r'[^\x00-\x7F]+')

    def __init__(self, root):
        self.root = root
        self.root.title("DOC EXPLORER pour ARGOS")
        self.root.geometry("1000x900")
        self.root.resizable(True, True)

        # Variables pour nettoyage
        self._last_update = 0
        self._mousewheel_bound = False
        self._stop_analysis = threading.Event()

        # Palette de couleurs douces et modernes
        self.colors = {
            'primary': '#6B9BD1',        # Bleu doux
            'primary_light': '#A8C5E8',  # Bleu très clair
            'primary_dark': '#5683BC',   # Bleu un peu plus foncé
            'accent': '#7FB3D5',         # Bleu accent
            'success': '#82C4A6',        # Vert menthe doux
            'success_light': '#B8E6D5',  # Vert très clair
            'danger': '#E74C3C',         # Rouge pour décocher
            'info': '#8BB4D9',           # Bleu info doux
            'background': '#F8FAFB',     # Fond très clair
            'card': '#FFFFFF',           # Blanc pur
            'text': '#4A5568',           # Gris foncé doux
            'text_light': '#A0AEC0',     # Gris clair
            'border': '#E2E8F0',         # Bordure douce
            'shadow': '#CBD5E0',         # Ombre douce
        }

        # Configuration
        self.root.configure(bg=self.colors['background'])

        # Variables
        self.folder_path = tk.StringVar()
        self.output_folder_path = tk.StringVar()
        self.use_custom_output = tk.BooleanVar(value=False)
        self.banner_image = None
        self.icon_image = None

        # Variables pour les fonctionnalités activées/désactivées
        self.feature_vars = {
            'scan_recursif': tk.BooleanVar(value=True),
            'renommage_emails': tk.BooleanVar(value=True),
            'extraction_pj': tk.BooleanVar(value=True),
            'classification': tk.BooleanVar(value=True),
            'export_excel': tk.BooleanVar(value=True),
            'rapport_html': tk.BooleanVar(value=True),
            'arborescence': tk.BooleanVar(value=True),
        }

        # Option pour forcer le retraitement
        self.force_reprocess = tk.BooleanVar(value=False)

        # Charger l'icône
        self.load_logo_icon()

        # Créer l'interface
        self.create_widgets()
        self.center_window()

        # Configurer la fermeture propre
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def center_window(self):
        """Centre la fenêtre"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def load_banner(self, parent):
        """Charge la bannière à gauche"""
        try:
            banner_path = Path(__file__).parent / "Banière.png"
            if banner_path.exists():
                img = Image.open(banner_path)
                # Garder les proportions, hauteur max 100px
                aspect_ratio = img.width / img.height
                new_height = 100
                new_width = int(new_height * aspect_ratio)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                self.banner_image = ImageTk.PhotoImage(img)

                banner_label = tk.Label(parent, image=self.banner_image, bg=self.colors['card'], bd=0)
                banner_label.pack(side='left', padx=20)
                return True
        except Exception as e:
            print(f"Erreur banniere: {e}")
        return False

    def load_logo_icon(self):
        """Charge l'icône de fenêtre"""
        try:
            logo_path = Path(__file__).parent / "logo.png"
            if logo_path.exists():
                img = Image.open(logo_path)
                img = img.resize((64, 64), Image.Resampling.LANCZOS)
                self.icon_image = ImageTk.PhotoImage(img)
                self.root.iconphoto(True, self.icon_image)
        except Exception as e:
            print(f"Erreur icone: {e}")

    def create_rounded_frame(self, parent):
        """Crée un cadre avec bords arrondis simulés"""
        # Conteneur avec ombre
        shadow = tk.Frame(parent, bg=self.colors['shadow'])

        # Frame principal avec background blanc
        card = tk.Frame(shadow, bg=self.colors['card'])
        card.pack(padx=2, pady=2, fill='both', expand=True)

        # Frame pour le contenu avec padding
        content = tk.Frame(card, bg=self.colors['card'])
        content.pack(fill='both', expand=True, padx=30, pady=25)

        return shadow, content

    def create_widgets(self):
        """Crée l'interface"""

        # ===== EN-TÊTE MODERNE =====
        header_container = tk.Frame(self.root, bg=self.colors['card'], height=130)
        header_container.pack(fill='x', padx=0, pady=0)
        header_container.pack_propagate(False)

        # Ajouter une ombre subtile en bas
        tk.Frame(self.root, bg=self.colors['shadow'], height=1).pack(fill='x')

        header_content = tk.Frame(header_container, bg=self.colors['card'])
        header_content.pack(fill='both', expand=True, padx=20, pady=15)

        # Bannière à gauche
        self.load_banner(header_content)

        # Texte à droite de la bannière
        text_container = tk.Frame(header_content, bg=self.colors['card'])
        text_container.pack(side='left', fill='both', expand=True, padx=(20, 0))

        tk.Label(
            text_container,
            text="Analyse Intelligente de Documents",
            font=('Segoe UI', 14, 'bold'),
            bg=self.colors['card'],
            fg=self.colors['text'],
            wraplength=700
        ).pack(anchor='w', pady=(10, 5))

        tk.Label(
            text_container,
            text="Classification automatique • Extraction PJ • Rapports détaillés",
            font=('Segoe UI', 9),
            bg=self.colors['card'],
            fg=self.colors['text_light'],
            wraplength=700
        ).pack(anchor='w')

        # ===== CONTENEUR PRINCIPAL AVEC SCROLLBAR =====
        # Créer un canvas avec scrollbar
        canvas_container = tk.Frame(self.root, bg=self.colors['background'])
        canvas_container.pack(fill='both', expand=True)

        canvas = tk.Canvas(canvas_container, bg=self.colors['background'], highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_container, orient='vertical', command=canvas.yview)

        main_container = tk.Frame(canvas, bg=self.colors['background'])

        # Configurer le canvas
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)

        # Créer une fenêtre dans le canvas
        canvas_window = canvas.create_window((0, 0), window=main_container, anchor='nw')

        # Fonction pour mettre à jour la zone scrollable
        def configure_scroll_region(event=None):
            canvas.configure(scrollregion=canvas.bbox('all'))
            # Ajuster la largeur du frame au canvas
            canvas.itemconfig(canvas_window, width=canvas.winfo_width())

        main_container.bind('<Configure>', configure_scroll_region)
        canvas.bind('<Configure>', configure_scroll_region)

        # Permettre le scroll avec la molette
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        if not self._mousewheel_bound:
            canvas.bind_all("<MouseWheel>", on_mousewheel)
            self._mousewheel_bound = True

        # Padding du conteneur
        tk.Frame(main_container, bg=self.colors['background'], height=30).pack()
        content_frame = tk.Frame(main_container, bg=self.colors['background'])
        content_frame.pack(fill='both', expand=True, padx=40)
        tk.Frame(main_container, bg=self.colors['background'], height=30).pack()

        # ===== CARD 1 : Sélection =====
        card1_shadow, card1 = self.create_rounded_frame(content_frame)
        card1_shadow.pack(fill='x', pady=(0, 20))

        tk.Label(
            card1,
            text="Selectionner un dossier",
            font=('Segoe UI', 13, 'bold'),
            bg=self.colors['card'],
            fg=self.colors['text']
        ).pack(anchor='w', pady=(0, 15))

        # Entry container arrondi
        entry_container = tk.Frame(card1, bg=self.colors['border'], bd=0)
        entry_container.pack(fill='x', pady=(0, 10))

        entry_inner = tk.Frame(entry_container, bg='white')
        entry_inner.pack(fill='both', expand=True, padx=1, pady=1)

        self.folder_entry = tk.Entry(
            entry_inner,
            textvariable=self.folder_path,
            font=('Segoe UI', 11),
            relief='flat',
            bg='white',
            fg=self.colors['text'],
            bd=0
        )
        self.folder_entry.pack(fill='both', padx=15, pady=12)

        # Bouton parcourir arrondi
        browse_container = tk.Frame(card1, bg=self.colors['card'])
        browse_container.pack(fill='x')

        self.browse_btn = RoundedButton(
            browse_container,
            text="Parcourir",
            command=self.browse_folder,
            bg_color=self.colors['info'],
            hover_color=self.colors['primary'],
            width=150
        )
        self.browse_btn.pack(anchor='e')

        # ===== CARD 2 : Fonctionnalités =====
        card2_shadow, card2 = self.create_rounded_frame(content_frame)
        card2_shadow.pack(fill='x', pady=(0, 20))

        # Header avec titre et boutons
        header_frame = tk.Frame(card2, bg=self.colors['card'])
        header_frame.pack(fill='x', pady=(0, 15))

        tk.Label(
            header_frame,
            text="Fonctionnalites",
            font=('Segoe UI', 13, 'bold'),
            bg=self.colors['card'],
            fg=self.colors['text']
        ).pack(side='left')

        # Liens discrets pour tout cocher / décocher
        links_frame = tk.Frame(header_frame, bg=self.colors['card'])
        links_frame.pack(side='right')

        check_all_link = tk.Label(
            links_frame,
            text="Tout cocher",
            font=('Segoe UI', 9, 'underline'),
            fg=self.colors['primary'],
            bg=self.colors['card'],
            cursor="hand2"
        )
        check_all_link.pack(side='left', padx=(0, 10))
        check_all_link.bind("<Button-1>", lambda e: self.check_all_features())
        check_all_link.bind("<Enter>", lambda e: check_all_link.config(fg=self.colors['primary_dark']))
        check_all_link.bind("<Leave>", lambda e: check_all_link.config(fg=self.colors['primary']))

        separator = tk.Label(
            links_frame,
            text="|",
            font=('Segoe UI', 9),
            fg=self.colors['text_light'],
            bg=self.colors['card']
        )
        separator.pack(side='left', padx=(0, 10))

        uncheck_all_link = tk.Label(
            links_frame,
            text="Tout decocher",
            font=('Segoe UI', 9, 'underline'),
            fg=self.colors['text_light'],
            bg=self.colors['card'],
            cursor="hand2"
        )
        uncheck_all_link.pack(side='left')
        uncheck_all_link.bind("<Button-1>", lambda e: self.uncheck_all_features())
        uncheck_all_link.bind("<Enter>", lambda e: uncheck_all_link.config(fg=self.colors['text']))
        uncheck_all_link.bind("<Leave>", lambda e: uncheck_all_link.config(fg=self.colors['text_light']))

        features = [
            ("scan_recursif", "Scan récursif", "Analyse tous fichiers et sous-dossiers"),
            ("renommage_emails", "Renommage emails", "Date, expéditeur, destinataire"),
            ("extraction_pj", "Extraction PJ", "Pièces jointes + emails imbriqués"),
            ("classification", "Classification auto", "Dossier technique / Correspondance / Autres"),
            ("export_excel", "Export Excel", "Traçabilité complète"),
            ("rapport_html", "Rapport HTML", "Visualisation interactive"),
            ("arborescence", "Arborescence source", "Structure des données sources"),
        ]

        for var_name, title, desc in features:
            feature = tk.Frame(card2, bg=self.colors['card'])
            feature.pack(fill='x', pady=3)

            # Checkbox
            cb = tk.Checkbutton(
                feature,
                variable=self.feature_vars[var_name],
                bg=self.colors['card'],
                activebackground=self.colors['card'],
                highlightthickness=0,
                bd=0
            )
            cb.pack(side='left', padx=(0, 5))

            text_frame = tk.Frame(feature, bg=self.colors['card'])
            text_frame.pack(side='left', fill='x', expand=True)

            tk.Label(
                text_frame,
                text=title,
                font=('Segoe UI', 10, 'bold'),
                bg=self.colors['card'],
                fg=self.colors['text'],
                anchor='w'
            ).pack(fill='x')

            tk.Label(
                text_frame,
                text=desc,
                font=('Segoe UI', 9),
                bg=self.colors['card'],
                fg=self.colors['text_light'],
                anchor='w'
            ).pack(fill='x')

        # Séparateur
        tk.Frame(card2, bg=self.colors['border'], height=1).pack(fill='x', pady=10)

        # Option forcer retraitement
        force_frame = tk.Frame(card2, bg=self.colors['card'])
        force_frame.pack(fill='x', pady=5)

        self.force_cb = tk.Checkbutton(
            force_frame,
            variable=self.force_reprocess,
            bg=self.colors['card'],
            activebackground=self.colors['card'],
            highlightthickness=0,
            bd=0
        )
        self.force_cb.pack(side='left', padx=(0, 5))

        force_text_frame = tk.Frame(force_frame, bg=self.colors['card'])
        force_text_frame.pack(side='left', fill='x', expand=True)

        tk.Label(
            force_text_frame,
            text="Forcer le retraitement",
            font=('Segoe UI', 10, 'bold'),
            bg=self.colors['card'],
            fg=self.colors['danger'],
            anchor='w'
        ).pack(fill='x')

        tk.Label(
            force_text_frame,
            text="Ignorer l'historique et retraiter tous les fichiers",
            font=('Segoe UI', 9),
            bg=self.colors['card'],
            fg=self.colors['text_light'],
            anchor='w'
        ).pack(fill='x')

        # ===== CARD 2b : Dossier de sortie =====
        card2b_shadow, card2b = self.create_rounded_frame(content_frame)
        card2b_shadow.pack(fill='x', pady=(0, 20))

        # Checkbox pour activer dossier personnalisé
        custom_output_frame = tk.Frame(card2b, bg=self.colors['card'])
        custom_output_frame.pack(fill='x', pady=(0, 10))

        self.custom_output_cb = tk.Checkbutton(
            custom_output_frame,
            text="Utiliser un dossier de sortie personnalise",
            variable=self.use_custom_output,
            command=self.toggle_custom_output,
            font=('Segoe UI', 11, 'bold'),
            bg=self.colors['card'],
            fg=self.colors['text'],
            activebackground=self.colors['card'],
            highlightthickness=0,
            bd=0
        )
        self.custom_output_cb.pack(side='left')

        # Entry pour le dossier de sortie (désactivé par défaut)
        self.output_entry_container = tk.Frame(card2b, bg=self.colors['border'], bd=0)
        self.output_entry_container.pack(fill='x', pady=(0, 10))

        output_entry_inner = tk.Frame(self.output_entry_container, bg='white')
        output_entry_inner.pack(fill='both', expand=True, padx=1, pady=1)

        self.output_folder_entry = tk.Entry(
            output_entry_inner,
            textvariable=self.output_folder_path,
            font=('Segoe UI', 11),
            relief='flat',
            bg='white',
            fg=self.colors['text'],
            bd=0,
            state='disabled'
        )
        self.output_folder_entry.pack(fill='both', padx=15, pady=12)

        # Bouton parcourir pour sortie
        output_browse_container = tk.Frame(card2b, bg=self.colors['card'])
        output_browse_container.pack(fill='x')

        self.output_browse_btn = RoundedButton(
            output_browse_container,
            text="Parcourir",
            command=self.browse_output_folder,
            bg_color=self.colors['info'],
            hover_color=self.colors['primary'],
            width=150
        )
        self.output_browse_btn.pack(anchor='e')
        self.output_browse_btn.set_state('disabled')

        # ===== BOUTON PRINCIPAL =====
        button_container = tk.Frame(content_frame, bg=self.colors['background'])
        button_container.pack(fill='x', pady=(0, 20))

        self.start_button = RoundedButton(
            button_container,
            text="Lancer l'Analyse",
            command=self.start_analysis,
            bg_color=self.colors['primary'],
            hover_color=self.colors['primary_dark'],
            width=400
        )
        self.start_button.pack(fill='x')

        # ===== CARD 3 : Progression =====
        card3_shadow, card3 = self.create_rounded_frame(content_frame)
        card3_shadow.pack(fill='both', expand=True, pady=(0, 20))

        tk.Label(
            card3,
            text="Progression",
            font=('Segoe UI', 13, 'bold'),
            bg=self.colors['card'],
            fg=self.colors['text']
        ).pack(anchor='w', pady=(0, 15))

        # Barre de progression
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Soft.Horizontal.TProgressbar",
                       troughcolor=self.colors['border'],
                       background=self.colors['primary'],
                       borderwidth=0,
                       thickness=8)

        self.progress_bar = ttk.Progressbar(
            card3,
            mode='indeterminate',
            style="Soft.Horizontal.TProgressbar"
        )
        self.progress_bar.pack(fill='x', pady=(0, 15))

        # Log arrondi
        log_container = tk.Frame(card3, bg=self.colors['border'])
        log_container.pack(fill='both', expand=True)

        log_inner = tk.Frame(log_container, bg='#2C3E50')
        log_inner.pack(fill='both', expand=True, padx=1, pady=1)

        self.log_text = scrolledtext.ScrolledText(
            log_inner,
            height=8,
            font=('Consolas', 9),
            bg='#2C3E50',
            fg='#A8E6CF',
            insertbackground='#A8E6CF',
            relief='flat',
            bd=0,
            padx=15,
            pady=15
        )
        self.log_text.pack(fill='both', expand=True)
        self.log_text.config(state='disabled')

        # ===== BOUTONS RÉSULTATS =====
        result_frame = tk.Frame(content_frame, bg=self.colors['background'])
        result_frame.pack(fill='x')

        self.open_excel_button = RoundedButton(
            result_frame,
            text="Excel",
            command=self.open_excel,
            bg_color=self.colors['success'],
            hover_color=self.colors['success_light'],
            width=150
        )
        self.open_excel_button.pack(side='left', fill='x', expand=True, padx=(0, 10))
        self.open_excel_button.set_state('disabled')

        self.open_report_button = RoundedButton(
            result_frame,
            text="HTML",
            command=self.open_report,
            bg_color=self.colors['info'],
            hover_color=self.colors['primary_light'],
            width=150
        )
        self.open_report_button.pack(side='left', fill='x', expand=True, padx=(0, 10))
        self.open_report_button.set_state('disabled')

        self.open_folder_button = RoundedButton(
            result_frame,
            text="Dossier",
            command=self.open_folder,
            bg_color=self.colors['primary_light'],
            hover_color=self.colors['primary'],
            width=150
        )
        self.open_folder_button.pack(side='left', fill='x', expand=True)
        self.open_folder_button.set_state('disabled')

    def browse_folder(self):
        folder = filedialog.askdirectory(title="Sélectionner le dossier à analyser")
        if folder:
            self.folder_path.set(folder)

    def browse_output_folder(self):
        folder = filedialog.askdirectory(title="Sélectionner le dossier de sortie")
        if folder:
            self.output_folder_path.set(folder)

    def toggle_custom_output(self):
        """Active/désactive le dossier de sortie personnalisé"""
        if self.use_custom_output.get():
            self.output_folder_entry.config(state='normal')
            self.output_browse_btn.set_state('normal')
        else:
            self.output_folder_entry.config(state='disabled')
            self.output_browse_btn.set_state('disabled')
            self.output_folder_path.set('')

    def check_all_features(self):
        """Coche toutes les fonctionnalités"""
        for var in self.feature_vars.values():
            var.set(True)

    def uncheck_all_features(self):
        """Décoche toutes les fonctionnalités"""
        for var in self.feature_vars.values():
            var.set(False)

    def log(self, message):
        """Log un message avec gestion d'encodage et throttling des updates"""
        self.log_text.config(state='normal')
        # Utiliser le pattern compilé au niveau de la classe
        message_clean = self.NON_ASCII_PATTERN.sub('', message)
        self.log_text.insert('end', f"{message_clean}\n")
        self.log_text.see('end')
        self.log_text.config(state='disabled')

        # Throttling: mise à jour max 10 fois par seconde
        current_time = time.time()
        if current_time - self._last_update > 0.1:
            self.root.update()
            self._last_update = current_time

    def start_analysis(self):
        # Validation améliorée des entrées
        folder_path_str = self.folder_path.get()
        if not folder_path_str or not folder_path_str.strip():
            messagebox.showerror("Erreur", "Veuillez sélectionner un dossier")
            return

        input_folder = Path(folder_path_str)
        if not input_folder.is_dir():
            messagebox.showerror("Erreur", "Le dossier n'existe pas")
            return

        # Vérifier les permissions de lecture
        if not os.access(input_folder, os.R_OK):
            messagebox.showerror("Erreur", "Pas de permission de lecture sur ce dossier")
            return

        # Vérifier le dossier de sortie personnalisé
        if self.use_custom_output.get():
            output_path_str = self.output_folder_path.get()
            if not output_path_str or not output_path_str.strip():
                messagebox.showerror("Erreur", "Veuillez sélectionner un dossier de sortie")
                return

            output_folder = Path(output_path_str)
            if not output_folder.is_dir():
                messagebox.showerror("Erreur", "Le dossier de sortie n'existe pas")
                return

            # Vérifier les permissions d'écriture
            if not os.access(output_folder, os.W_OK):
                messagebox.showerror("Erreur", "Pas de permission d'écriture sur le dossier de sortie")
                return

        # Vérifier qu'au moins une fonctionnalité est activée
        any_feature_enabled = any(var.get() for var in self.feature_vars.values())
        if not any_feature_enabled:
            messagebox.showerror(
                "Erreur",
                "Veuillez activer au moins une fonctionnalite !\n\n"
                "Cochez au moins une case dans la section Fonctionnalites."
            )
            return

        # Construire le message de confirmation
        message_parts = [f"Dossier source :\n{self.folder_path.get()}\n"]

        if self.use_custom_output.get():
            message_parts.append(f"Dossier de sortie :\n{self.output_folder_path.get()}\n")

        message_parts.append("Fonctionnalites activees :")

        if self.feature_vars['scan_recursif'].get():
            message_parts.append("- Scan recursif (sous-dossiers)")
        else:
            message_parts.append("- Scan niveau 1 uniquement")

        if self.feature_vars['classification'].get():
            message_parts.append("- Classification (Dossier technique / Correspondance / Autres fichiers)")
        else:
            message_parts.append("- Tout dans dossier Donnees")

        if self.feature_vars['renommage_emails'].get():
            message_parts.append("- Renommage emails")

        if self.feature_vars['extraction_pj'].get():
            message_parts.append("- Extraction pieces jointes")

        if self.feature_vars['export_excel'].get():
            message_parts.append("- Export Excel")

        if self.feature_vars['rapport_html'].get():
            message_parts.append("- Rapport HTML")

        if self.feature_vars['arborescence'].get():
            message_parts.append("- Arborescence source")

        message_parts.append("\nContinuer ?")

        result = messagebox.askyesno(
            "Confirmation",
            "\n".join(message_parts)
        )

        if not result:
            return

        self.start_button.set_state('disabled')
        self.open_excel_button.set_state('disabled')
        self.open_report_button.set_state('disabled')
        self.open_folder_button.set_state('disabled')

        self.progress_bar.start()

        self.log_text.config(state='normal')
        self.log_text.delete('1.0', 'end')
        self.log_text.config(state='disabled')

        # Réinitialiser le flag d'arrêt
        self._stop_analysis.clear()

        # Thread non-daemon pour éviter l'arrêt brutal
        thread = threading.Thread(target=self.run_analysis)
        thread.start()

    def run_analysis(self):
        try:
            from pathlib import Path
            import shutil
            from datetime import datetime
            import json

            input_folder = Path(self.folder_path.get())

            # Déterminer le dossier de sortie
            if self.use_custom_output.get() and self.output_folder_path.get():
                output_folder = Path(self.output_folder_path.get())
            else:
                output_folder = input_folder

            # Générer un timestamp unique pour cette exécution
            timestamp = datetime.now().strftime('%y%m%d_%H%M%S')
            date_only = datetime.now().strftime('%y%m%d')

            self.log("=" * 70)
            self.log("DOC EXPLORER - DEMARRAGE")
            self.log("=" * 70)
            self.log(f"Dossier source : {input_folder}")
            if self.use_custom_output.get():
                self.log(f"Dossier sortie : {output_folder}")
            self.log("")

            # Afficher les fonctionnalités activées
            self.log("Fonctionnalites activees :")
            for key, var in self.feature_vars.items():
                status = "OUI" if var.get() else "NON"
                self.log(f"   {key}: {status}")
            self.log("")

            # Récupérer les options
            enable_classification = self.feature_vars['classification'].get()
            enable_rename = self.feature_vars['renommage_emails'].get()
            enable_extract_pj = self.feature_vars['extraction_pj'].get()
            enable_excel = self.feature_vars['export_excel'].get()
            enable_html = self.feature_vars['rapport_html'].get()
            enable_arborescence = self.feature_vars['arborescence'].get()
            recursive = self.feature_vars['scan_recursif'].get()

            self.log("Initialisation...")

            # Fichier de traçabilité caché
            trace_file = output_folder / ".docexplorer_history.json"
            processed_files_set = set()

            # Préparer la configuration actuelle pour comparaison
            current_config = {
                'scan_recursif': self.feature_vars['scan_recursif'].get(),
                'renommage_emails': self.feature_vars['renommage_emails'].get(),
                'extraction_pj': self.feature_vars['extraction_pj'].get(),
                'classification': self.feature_vars['classification'].get(),
            }

            # Charger l'historique des fichiers déjà traités
            if trace_file.exists() and not self.force_reprocess.get():
                try:
                    with open(trace_file, 'r', encoding='utf-8') as f:
                        history = json.load(f)

                        # Ne charger les fichiers traités QUE si la config est identique à la dernière exécution
                        if history.get('executions'):
                            last_execution = history['executions'][-1]
                            last_features = last_execution.get('features', {})

                            # Comparer les fonctionnalités importantes
                            config_changed = (
                                last_features.get('scan_recursif') != current_config['scan_recursif'] or
                                last_features.get('renommage_emails') != current_config['renommage_emails'] or
                                last_features.get('extraction_pj') != current_config['extraction_pj'] or
                                last_features.get('classification') != current_config['classification']
                            )

                            if config_changed:
                                self.log("Configuration changee - Retraitement de tous les fichiers")
                            else:
                                # Configuration identique : charger les fichiers traités
                                for execution in history.get('executions', []):
                                    processed_files_set.update(execution.get('processed_files', []))
                                self.log(f"Historique charge : {len(processed_files_set)} fichiers deja traites")

                except Exception as e:
                    self.log(f"Impossible de charger l'historique : {e}")
                    history = {'executions': []}
            elif self.force_reprocess.get():
                self.log("Retraitement force - Tous les fichiers seront traites")
                history = {'executions': []}
            else:
                history = {'executions': []}

            # Préparer l'entrée d'historique pour cette exécution
            current_execution = {
                'timestamp': timestamp,
                'date': datetime.now().isoformat(),
                'features': {k: v.get() for k, v in self.feature_vars.items()},
                'input_folder': str(input_folder),
                'output_folder': str(output_folder),
                'processed_files': []
            }

            # Déterminer les catégories selon les options
            # Ne créer les dossiers QUE si on fait du traitement de fichiers (copie/classification)
            # Ne pas inclure arborescence car elle ne fait que lire, pas copier
            need_file_processing = (enable_classification or enable_rename or enable_extract_pj or
                                   recursive)

            if need_file_processing:
                if enable_classification:
                    categories = {
                        "Dossier technique": ['.pdf', '.dwg', '.dxf', '.doc', '.docx', '.xls', '.xlsx',
                                            '.ppt', '.pptx', '.odt', '.ods', '.odp', '.zip', '.rar'],
                        "Correspondance": ['.msg', '.eml'],
                        "Autres fichiers": []  # Pour les fichiers non classés
                    }
                else:
                    # Si classification désactivée, tout va dans "Données"
                    categories = {
                        "Donnees": []
                    }

                category_folders = {}
                for category in categories.keys():
                    cat_folder = output_folder / category
                    cat_folder.mkdir(parents=True, exist_ok=True)
                    category_folders[category] = cat_folder
            else:
                # Pas de traitement de fichiers, juste rapports
                categories = {}
                category_folders = {}

            processed = []
            stats = {
                'total_files': 0,
                'total_emails': 0,
                'total_attachments': 0,
                'by_category': {cat: 0 for cat in categories.keys()}
            }

            # Ne traiter les fichiers que si nécessaire
            if need_file_processing:
                self.log("\n" + "=" * 70)
                self.log("TRAITEMENT DES FICHIERS")
                self.log("=" * 70)

                # Scanner les fichiers
                if recursive:
                    files_to_process = list(input_folder.rglob('*'))
                else:
                    files_to_process = list(input_folder.glob('*'))

                total_files_count = len([f for f in files_to_process if f.is_file()])
                self.log(f"Fichiers a traiter : {total_files_count}\n")

                # Compteur pour afficher la progression
                files_processed_count = 0

                for file_path in files_to_process:
                    if not file_path.is_file():
                        continue

                    # Ignorer les fichiers cachés
                    if file_path.name.startswith('.'):
                        continue

                    # Vérifier si déjà traité
                    file_path_str = str(file_path.resolve())
                    if file_path_str in processed_files_set:
                        continue

                    # Ignorer les fichiers dans les dossiers de catégories (sortie)
                    skip = False
                    for cat_name in categories.keys():
                        try:
                            file_path.relative_to(output_folder / cat_name)
                            skip = True
                            break
                        except ValueError:
                            pass

                    if skip:
                        continue

                    # Déterminer la catégorie
                    if enable_classification:
                        category = "Autres fichiers"  # Par défaut en mode classification
                        for cat, extensions in categories.items():
                            if file_path.suffix.lower() in extensions:
                                category = cat
                                break
                    else:
                        category = "Donnees"  # Tout va dans "Données" si classification désactivée

                    # Traiter les emails
                    if file_path.suffix.lower() in ['.msg', '.eml']:
                        stats['total_emails'] += 1

                        # Renommer si activé
                        if enable_rename:
                            try:
                                from analyst_helper import EmailRenamer
                                renamer = EmailRenamer()
                                new_name, _ = renamer.rename_msg_file(str(file_path))
                                # Log uniquement si erreur (pas pour chaque email)
                            except Exception as e:
                                new_name = file_path.name
                                self.log(f"ERREUR renommage {file_path.name}")
                        else:
                            new_name = file_path.name

                        # Copier l'email
                        dest_folder = category_folders[category]
                        dest_path = dest_folder / new_name
                        dest_path = self._get_unique_path(dest_path)
                        shutil.copy2(file_path, dest_path)

                        stats['total_files'] += 1
                        stats['by_category'][category] += 1

                        # Extraire les PJ si activé
                        if enable_extract_pj:
                            msg = None
                            temp_dir = None
                            try:
                                import extract_msg
                                msg = extract_msg.Message(str(dest_path))
                                temp_dir = dest_path.parent / ".temp_attachments"
                                temp_dir.mkdir(exist_ok=True)

                                for att in msg.attachments:
                                    # Ignorer les images intégrées
                                    filename = att.longFilename or att.shortFilename
                                    if not filename:
                                        continue

                                    # Nettoyer le nom de fichier pour sécurité (éviter path traversal)
                                    filename = os.path.basename(filename)
                                    filename = "".join(c for c in filename if c.isalnum() or c in (' ', '.', '_', '-'))
                                    if not filename:
                                        filename = f"attachment_{id(att)}.dat"

                                    # Sauvegarder la PJ
                                    temp_path = temp_dir / filename
                                    temp_path = self._get_unique_path(temp_path)

                                    att.save(customPath=str(temp_dir), customFilename=temp_path.name)

                                    # Classifier la PJ
                                    if enable_classification:
                                        pj_category = "Autres fichiers"  # Par défaut en mode classification
                                        for cat, extensions in categories.items():
                                            if temp_path.suffix.lower() in extensions:
                                                pj_category = cat
                                                break
                                    else:
                                        pj_category = "Donnees"  # Tout va dans "Données" si classification désactivée

                                    pj_dest = category_folders[pj_category] / temp_path.name
                                    pj_dest = self._get_unique_path(pj_dest)
                                    shutil.copy2(temp_path, pj_dest)

                                    stats['total_attachments'] += 1
                                    stats['total_files'] += 1
                                    stats['by_category'][pj_category] += 1

                                    temp_path.unlink(missing_ok=True)

                            except Exception as e:
                                self.log(f"ERREUR extraction PJ de {new_name}: {e}")
                            finally:
                                # Garantir la fermeture du message
                                if msg:
                                    try:
                                        msg.close()
                                    except:
                                        pass
                                # Nettoyer le dossier temp
                                if temp_dir and temp_dir.exists():
                                    try:
                                        if not any(temp_dir.iterdir()):
                                            temp_dir.rmdir()
                                    except:
                                        pass

                    else:
                        # Fichier normal
                        dest_folder = category_folders[category]
                        dest_path = dest_folder / file_path.name
                        dest_path = self._get_unique_path(dest_path)
                        shutil.copy2(file_path, dest_path)

                        stats['total_files'] += 1
                        stats['by_category'][category] += 1

                    # Enregistrer le fichier comme traité
                    current_execution['processed_files'].append(file_path_str)

                    # Incrémenter et afficher progression (adaptée au nombre total)
                    files_processed_count += 1
                    log_interval = max(10, total_files_count // 100)  # 1% ou min 10
                    if files_processed_count % log_interval == 0 or files_processed_count == total_files_count:
                        self.log(f"Progression : {files_processed_count}/{total_files_count} fichiers traites")

            self.log(f"\n" + "=" * 70)
            self.log("TRAITEMENT TERMINE")
            self.log("=" * 70)
            self.log(f"   Fichiers : {stats['total_files']}")
            self.log(f"   Emails : {stats['total_emails']}")
            self.log(f"   PJ extraites : {stats['total_attachments']}")

            self.log("\nRepartition :")
            for cat, count in stats['by_category'].items():
                if count > 0:
                    self.log(f"   - {cat}: {count}")

            # Export Excel si activé
            excel_filename = None
            if enable_excel:
                self.log("")
                self.log("Export Excel...")
                try:
                    from analyst_helper import ExcelExporter
                    excel_filename = f"DocExplorer_{date_only}_Liste.xlsx"
                    excel_path = output_folder / excel_filename
                    exporter = ExcelExporter(str(excel_path))
                    exporter.export(processed, stats)
                    self.log(f"   OK - {excel_filename}")
                    current_execution['excel_file'] = excel_filename
                except Exception as e:
                    self.log("   ERREUR - Echec creation Excel")

            # Rapport HTML si activé
            html_filename = None
            if enable_html:
                self.log("")
                self.log("Generation rapport HTML...")
                try:
                    from analyst_helper import FolderScanner
                    from analyst_helper.core.reporter import HTMLReporter

                    scanner = FolderScanner(str(input_folder))
                    files = scanner.scan(exclude_folders=list(categories.keys()))

                    html_filename = f"DocExplorer_{date_only}_Rapport.html"
                    html_path = output_folder / html_filename
                    reporter = HTMLReporter(str(html_path))
                    reporter.generate_report(
                        files=files,
                        stats=scanner.stats,
                        title=f"DOC EXPLORER - {input_folder.name}"
                    )
                    self.log(f"   OK - {html_filename}")
                    current_execution['html_file'] = html_filename
                except Exception as e:
                    self.log("   ERREUR - Echec creation rapport HTML")

            # Arborescence source si activé
            tree_filename = None
            if enable_arborescence:
                self.log("")
                self.log("Generation arborescence source...")
                try:
                    tree_filename = f"DocExplorer_{date_only}_Arborescence.html"
                    tree_path = output_folder / tree_filename
                    self._generate_tree(input_folder, tree_path, categories.keys())
                    self.log(f"   OK - {tree_filename}")
                    current_execution['tree_file'] = tree_filename
                except Exception as e:
                    self.log("   ERREUR - Echec creation arborescence")

            # Sauvegarder l'historique
            current_execution['stats'] = stats
            history['executions'].append(current_execution)

            try:
                # Sauvegarder avec backup
                if trace_file.exists():
                    backup_file = trace_file.with_suffix('.json.bak')
                    shutil.copy2(trace_file, backup_file)

                with open(trace_file, 'w', encoding='utf-8') as f:
                    json.dump(history, f, indent=2, ensure_ascii=False)

                # Rendre le fichier caché sur Windows uniquement
                if sys.platform == 'win32':
                    try:
                        import ctypes
                        ctypes.windll.kernel32.SetFileAttributesW(str(trace_file), 2)
                    except (AttributeError, OSError) as e:
                        self.log(f"Info: Impossible de masquer le fichier historique")

                self.log("")
                self.log("Historique sauvegarde")
            except Exception as e:
                self.log(f"ERREUR sauvegarde historique : {e}")

            self.log("\n" + "=" * 70)
            self.log("ANALYSE TERMINEE AVEC SUCCES")
            self.log("=" * 70)
            self.log(f"\nResultats disponibles dans :")
            self.log(f"{output_folder}")

            self.root.after(0, self.analysis_complete)

        except Exception as e:
            self.log(f"\nERREUR : {e}")
            import traceback
            self.log(traceback.format_exc())
            self.root.after(0, self.analysis_failed)

    def _generate_tree(self, folder: Path, output_file: Path, exclude_folders: list):
        """Génère une arborescence HTML interactive du dossier source"""
        from pathlib import Path
        from datetime import datetime

        def get_file_type_color(extension):
            """Retourne une couleur selon le type de fichier"""
            ext = extension.lower()
            if ext in ['.pdf', '.doc', '.docx', '.odt']:
                return '#e74c3c'  # Rouge pour documents
            elif ext in ['.xls', '.xlsx', '.csv', '.ods']:
                return '#27ae60'  # Vert pour tableurs
            elif ext in ['.msg', '.eml']:
                return '#3498db'  # Bleu pour emails
            elif ext in ['.jpg', '.png', '.gif', '.bmp']:
                return '#9b59b6'  # Violet pour images
            elif ext in ['.zip', '.rar', '.7z']:
                return '#f39c12'  # Orange pour archives
            elif ext in ['.dwg', '.dxf']:
                return '#e67e22'  # Orange foncé pour CAD
            else:
                return '#95a5a6'  # Gris pour autres

        def get_file_icon(extension):
            """Retourne une icône selon le type de fichier"""
            ext = extension.lower()
            if ext in ['.pdf', '.doc', '.docx', '.odt']:
                return '📄'
            elif ext in ['.xls', '.xlsx', '.csv', '.ods']:
                return '📊'
            elif ext in ['.msg', '.eml']:
                return '📧'
            elif ext in ['.jpg', '.png', '.gif', '.bmp']:
                return '🖼️'
            elif ext in ['.zip', '.rar', '.7z']:
                return '📦'
            elif ext in ['.dwg', '.dxf']:
                return '📐'
            else:
                return '📎'

        def tree_html(directory, exclude_dirs=None, depth=0):
            """Génère récursivement l'arborescence HTML"""
            if exclude_dirs is None:
                exclude_dirs = set()

            html = []
            try:
                items = sorted(directory.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            except PermissionError:
                return ['<li class="file error">❌ [ACCES REFUSE]</li>']

            for item in items:
                # Ignorer les fichiers cachés
                if item.name.startswith('.'):
                    continue

                # Ignorer les dossiers exclus
                if item.is_dir() and item.name in exclude_dirs:
                    continue

                if item.is_dir():
                    folder_id = f"folder_{id(item)}"
                    html.append(f'<li class="folder">')
                    html.append(f'<span class="folder-toggle" onclick="toggleFolder(\'{folder_id}\')">▶</span>')
                    html.append(f'<span class="folder-name">📁 {item.name}/</span>')
                    html.append(f'<ul id="{folder_id}" class="nested">')
                    # Récursion dans les sous-dossiers
                    sub_html = tree_html(item, exclude_dirs, depth + 1)
                    html.extend(sub_html)
                    html.append('</ul>')
                    html.append('</li>')
                else:
                    # Afficher le fichier avec taille et couleur
                    try:
                        size_kb = item.stat().st_size / 1024
                        if size_kb < 1024:
                            size_str = f"{size_kb:.1f} KB"
                        else:
                            size_str = f"{size_kb/1024:.1f} MB"

                        color = get_file_type_color(item.suffix)
                        icon = get_file_icon(item.suffix)
                        html.append(f'<li class="file">')
                        html.append(f'<span style="color: {color}">{icon} {item.name}</span>')
                        html.append(f'<span class="file-size">{size_str}</span>')
                        html.append('</li>')
                    except:
                        html.append(f'<li class="file">📎 {item.name}</li>')

            return html

        # Calculer les statistiques
        try:
            total_files = sum(1 for _ in folder.rglob('*') if _.is_file() and not _.name.startswith('.'))
            total_dirs = sum(1 for _ in folder.rglob('*') if _.is_dir() and not _.name.startswith('.'))
            total_size = sum(_.stat().st_size for _ in folder.rglob('*') if _.is_file() and not _.name.startswith('.'))
            total_size_mb = total_size / (1024 * 1024)
        except:
            total_files = 0
            total_dirs = 0
            total_size_mb = 0

        # Créer la structure JSON pour la mindmap
        def build_tree_json(directory, exclude_dirs=None):
            """Construit récursivement la structure JSON pour la mindmap"""
            if exclude_dirs is None:
                exclude_dirs = set()

            node = {
                'name': directory.name,
                'path': str(directory),
                'type': 'folder',
                'children': []
            }

            try:
                items = sorted(directory.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            except PermissionError:
                return node

            for item in items:
                if item.name.startswith('.'):
                    continue
                if item.is_dir() and item.name in exclude_dirs:
                    continue

                if item.is_dir():
                    child = build_tree_json(item, exclude_dirs)
                    node['children'].append(child)
                else:
                    try:
                        size = item.stat().st_size / 1024
                        size_str = f"{size:.1f} KB" if size < 1024 else f"{size/1024:.1f} MB"
                    except:
                        size_str = "?"

                    node['children'].append({
                        'name': item.name,
                        'path': str(item),
                        'type': 'file',
                        'ext': item.suffix.lower(),
                        'size': size_str
                    })

            return node

        tree_data = build_tree_json(folder, exclude_folders)
        import json as json_lib
        tree_json = json_lib.dumps(tree_data)

        # Générer le HTML complet avec mindmap
        html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Arborescence - {{folder.name}}</title>
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
        }}

        .stat-item {{
            background: white;
            padding: 8px 15px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}

        .stat-value {{
            font-size: 18px;
            font-weight: bold;
            color: #667eea;
        }}

        .stat-label {{
            font-size: 11px;
            color: #6c757d;
        }}

        #mindmap {{
            width: 100%;
            height: calc(100vh - 160px);
            background: white;
        }}

        .node circle {{
            cursor: pointer;
            stroke-width: 2px;
        }}

        .node text {{
            font-size: 12px;
            font-family: 'Segoe UI', sans-serif;
        }}

        .link {{
            fill: none;
            stroke: #ccc;
            stroke-width: 2px;
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
            position: absolute;
            top: 180px;
            right: 20px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            padding: 5px;
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
        <h1>Arborescence - {{folder.name}}</h1>
        <p>{{folder}} - Genere le {{datetime.now().strftime('%Y-%m-%d a %H:%M:%S')}}</p>
    </div>

    <div class="controls">
        <div class="search-box">
            <input type="text" id="searchInput" placeholder="Rechercher un fichier ou dossier...">
            <span class="search-icon">🔍</span>
        </div>
        <div class="stats">
            <div class="stat-item">
                <div class="stat-value">{{total_files}}</div>
                <div class="stat-label">Fichiers</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{{total_dirs}}</div>
                <div class="stat-label">Dossiers</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{{total_size_mb:.1f}} MB</div>
                <div class="stat-label">Taille</div>
            </div>
        </div>
    </div>

    <div id="mindmap"></div>

    <div class="zoom-controls">
        <button class="zoom-btn" onclick="zoomIn()">+</button>
        <button class="zoom-btn" onclick="resetZoom()">⟲</button>
        <button class="zoom-btn" onclick="zoomOut()">−</button>
    </div>

    <div class="tooltip" id="tooltip"></div>

    <script>
        const treeData = {tree_json};

        // Configuration
        const width = window.innerWidth;
        const height = window.innerHeight - 160;
        const margin = {{top: 20, right: 120, bottom: 20, left: 120}};

        // Créer le SVG
        const svg = d3.select("#mindmap")
            .append("svg")
            .attr("width", width)
            .attr("height", height);

        const g = svg.append("g")
            .attr("transform", `translate(${{width/2}},${{height/2}})`);

        // Zoom
        const zoom = d3.zoom()
            .scaleExtent([0.1, 3])
            .on("zoom", (event) => {{
                g.attr("transform", event.transform);
            }});

        svg.call(zoom);

        // Créer la hiérarchie
        const root = d3.hierarchy(treeData);
        const treeLayout = d3.tree()
            .size([2 * Math.PI, Math.min(width, height) / 2 - 100])
            .separation((a, b) => (a.parent == b.parent ? 1 : 2) / a.depth);

        treeLayout(root);

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

        // Dessiner les liens
        const link = g.selectAll(".link")
            .data(root.links())
            .enter().append("path")
            .attr("class", "link")
            .attr("d", d3.linkRadial()
                .angle(d => d.x)
                .radius(d => d.y));

        // Dessiner les noeuds
        const node = g.selectAll(".node")
            .data(root.descendants())
            .enter().append("g")
            .attr("class", "node")
            .attr("transform", d => `
                rotate(${{d.x * 180 / Math.PI - 90}})
                translate(${{d.y}},0)
            `);

        node.append("circle")
            .attr("r", d => d.data.type === 'folder' ? 6 : 4)
            .style("fill", d => getColor(d))
            .style("stroke", d => d3.rgb(getColor(d)).darker())
            .on("mouseover", showTooltip)
            .on("mouseout", hideTooltip)
            .on("click", toggleChildren);

        node.append("text")
            .attr("dy", ".31em")
            .attr("x", d => d.x < Math.PI === !d.children ? 6 : -6)
            .attr("text-anchor", d => d.x < Math.PI === !d.children ? "start" : "end")
            .attr("transform", d => d.x >= Math.PI ? "rotate(180)" : null)
            .text(d => d.data.name.length > 20 ? d.data.name.substring(0, 20) + '...' : d.data.name)
            .style("font-size", "11px")
            .style("fill", "#2c3e50");

        // Tooltip
        const tooltip = d3.select("#tooltip");

        function showTooltip(event, d) {{
            let content = `<strong>${{d.data.name}}</strong><br>`;
            content += `Type: ${{d.data.type === 'folder' ? 'Dossier' : 'Fichier'}}<br>`;
            if (d.data.size) content += `Taille: ${{d.data.size}}`;

            tooltip
                .style("opacity", 1)
                .html(content)
                .style("left", (event.pageX + 10) + "px")
                .style("top", (event.pageY - 10) + "px");
        }}

        function hideTooltip() {{
            tooltip.style("opacity", 0);
        }}

        // Recherche
        const searchInput = document.getElementById('searchInput');
        searchInput.addEventListener('input', (e) => {{
            const searchTerm = e.target.value.toLowerCase();

            node.selectAll("circle").classed("highlight", false);

            if (searchTerm.length > 0) {{
                node.filter(d => d.data.name.toLowerCase().includes(searchTerm))
                    .selectAll("circle")
                    .classed("highlight", true);
            }}
        }});

        // Contrôles zoom
        function zoomIn() {{
            svg.transition().call(zoom.scaleBy, 1.3);
        }}

        function zoomOut() {{
            svg.transition().call(zoom.scaleBy, 0.7);
        }}

        function resetZoom() {{
            svg.transition().call(zoom.transform, d3.zoomIdentity.translate(width/2, height/2));
        }}

        // Toggle enfants
        function toggleChildren(event, d) {{
            if (d.children) {{
                d._children = d.children;
                d.children = null;
            }} else if (d._children) {{
                d.children = d._children;
                d._children = null;
            }}
            update(d);
        }}

        function update(source) {{
            treeLayout(root);

            link.transition()
                .duration(750)
                .attr("d", d3.linkRadial()
                    .angle(d => d.x)
                    .radius(d => d.y));

            node.transition()
                .duration(750)
                .attr("transform", d => `
                    rotate(${{d.x * 180 / Math.PI - 90}})
                    translate(${{d.y}},0)
                `);
        }}
    </script>
</body>
</html>"""

        # Écrire le fichier HTML
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

    def _get_unique_path(self, path: Path) -> Path:
        """Génère un chemin unique"""
        if not path.exists():
            return path

        stem = path.stem
        suffix = path.suffix
        parent = path.parent
        counter = 1

        while True:
            new_path = parent / f"{stem}_{counter}{suffix}"
            if not new_path.exists():
                return new_path
            counter += 1

    def analysis_complete(self):
        self.progress_bar.stop()
        self.start_button.set_state('normal')

        # Activer les boutons selon ce qui a été généré
        if self.feature_vars['export_excel'].get():
            self.open_excel_button.set_state('normal')
        if self.feature_vars['rapport_html'].get():
            self.open_report_button.set_state('normal')
        self.open_folder_button.set_state('normal')

        # Message selon les fonctionnalités activées
        message_parts = ["Analyse terminee !\n"]
        message_parts.append("- Fichiers classes")
        if self.feature_vars['renommage_emails'].get():
            message_parts.append("- Emails renommes")
        if self.feature_vars['extraction_pj'].get():
            message_parts.append("- PJ extraites")
        if self.feature_vars['export_excel'].get():
            message_parts.append("- Excel genere")
        if self.feature_vars['rapport_html'].get():
            message_parts.append("- Rapport HTML cree")
        if self.feature_vars['arborescence'].get():
            message_parts.append("- Arborescence creee")

        messagebox.showinfo("Succes", "\n".join(message_parts))

    def analysis_failed(self):
        self.progress_bar.stop()
        self.start_button.set_state('normal')
        messagebox.showerror("Erreur", "L'analyse a échoué.\n\nConsultez les logs.")

    def open_excel(self):
        # Utiliser le dossier de sortie si défini
        if self.use_custom_output.get() and self.output_folder_path.get():
            output_folder = Path(self.output_folder_path.get())
        else:
            output_folder = Path(self.folder_path.get())

        # Trouver le fichier Excel le plus récent
        excel_files = list(output_folder.glob("DocExplorer_*_Liste.xlsx"))
        if excel_files:
            # Trier par date de modification, prendre le plus récent
            excel_path = max(excel_files, key=lambda p: p.stat().st_mtime)
            self._open_file(excel_path)
        else:
            messagebox.showerror("Erreur", "Le fichier Excel n'existe pas")

    def open_report(self):
        # Utiliser le dossier de sortie si défini
        if self.use_custom_output.get() and self.output_folder_path.get():
            output_folder = Path(self.output_folder_path.get())
        else:
            output_folder = Path(self.folder_path.get())

        # Trouver le fichier HTML de rapport le plus récent
        report_files = list(output_folder.glob("DocExplorer_*_Rapport.html"))
        if report_files:
            # Trier par date de modification, prendre le plus récent
            report_path = max(report_files, key=lambda p: p.stat().st_mtime)
            webbrowser.open(f'file://{report_path.resolve()}')
        else:
            messagebox.showerror("Erreur", "Le rapport n'existe pas")

    def open_folder(self):
        # Utiliser le dossier de sortie si défini
        if self.use_custom_output.get() and self.output_folder_path.get():
            folder = Path(self.output_folder_path.get())
        else:
            folder = Path(self.folder_path.get())

        if folder.exists():
            self._open_file(folder)
        else:
            messagebox.showerror("Erreur", "Le dossier n'existe pas")

    def _open_file(self, path):
        """Ouvre un fichier ou dossier de manière portable (Windows/Mac/Linux)"""
        try:
            if sys.platform == 'win32':
                os.startfile(path)
            elif sys.platform == 'darwin':
                subprocess.run(['open', str(path)], check=True)
            else:
                subprocess.run(['xdg-open', str(path)], check=True)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir le fichier:\n{e}")

    def on_closing(self):
        """Fermeture propre de l'application"""
        # Signaler au thread d'analyse de s'arrêter
        self._stop_analysis.set()

        # Détacher les event handlers
        if self._mousewheel_bound:
            try:
                self.root.unbind_all("<MouseWheel>")
            except:
                pass

        # Fermer la fenêtre
        self.root.destroy()


def main():
    root = tk.Tk()
    app = DocExplorerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
