"""
Main application window for Audiobook Generator
"""
import sys
from pathlib import Path
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QPushButton,
                               QLabel, QMessageBox, QProgressDialog, QMenuBar,
                               QStatusBar, QHBoxLayout, QGroupBox)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QAction

# Import components
from gui.components.file_uploader import FileUploader
from gui.components.voice_selector import VoiceSelector
from gui.components.chapter_list import ChapterList


class MainWindow(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()
        self.current_file = None
        self.chapters = []
        self.language_code = 'en-GB'
        self.voice_name = 'en-GB-Chirp3-HD-Despina'
        self.setup_ui()
        self.create_menu_bar()
        self.create_status_bar()

    def setup_ui(self):
        """Set up the user interface"""
        self.setWindowTitle("Audiobook Generator - PROTOTYPE")
        self.setMinimumSize(700, 800)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Title
        title_label = QLabel("🎧 Audiobook Generator")
        title_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #0066cc;
            padding: 10px;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # Subtitle
        subtitle = QLabel("Convert ebooks to audiobooks using Google Cloud Text-to-Speech")
        subtitle.setStyleSheet("color: #666; font-size: 12px;")
        subtitle.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(subtitle)

        # File uploader
        self.file_uploader = FileUploader()
        self.file_uploader.file_selected.connect(self.on_file_selected)
        main_layout.addWidget(self.file_uploader)

        # Voice selector
        self.voice_selector = VoiceSelector()
        self.voice_selector.voice_changed.connect(self.on_voice_changed)
        main_layout.addWidget(self.voice_selector)

        # Chapter list
        self.chapter_list = ChapterList()
        self.chapter_list.selection_changed.connect(self.on_selection_changed)
        main_layout.addWidget(self.chapter_list, 1)  # Give it more space

        # Cost estimator
        self.cost_group = QGroupBox("💰 Estimated Cost")
        cost_layout = QVBoxLayout()
        self.cost_label = QLabel("Select a file to see cost estimate")
        self.cost_label.setStyleSheet("font-size: 12px; color: #666;")
        self.cost_label.setAlignment(Qt.AlignCenter)
        cost_layout.addWidget(self.cost_label)
        self.cost_group.setLayout(cost_layout)
        main_layout.addWidget(self.cost_group)

        # Generate button
        self.generate_btn = QPushButton("▶️  Generate Audiobook")
        self.generate_btn.setEnabled(False)
        self.generate_btn.setMinimumHeight(50)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #0066cc;
                color: white;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #0052a3;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.generate_btn.clicked.connect(self.on_generate_clicked)
        main_layout.addWidget(self.generate_btn)

        # Setup notice
        setup_notice = QLabel(
            "⚠️ PROTOTYPE: This demo only extracts chapters. "
            "Full version requires Google Cloud API credentials."
        )
        setup_notice.setStyleSheet("""
            background-color: #fff3cd;
            color: #856404;
            padding: 10px;
            border-radius: 5px;
            font-size: 11px;
        """)
        setup_notice.setWordWrap(True)
        main_layout.addWidget(setup_notice)

        central_widget.setLayout(main_layout)

    def create_menu_bar(self):
        """Create the application menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        open_action = QAction("Open Ebook...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.file_uploader.mousePressEvent)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        quit_action = QAction("Quit", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # Help menu
        help_menu = menubar.addMenu("Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_status_bar(self):
        """Create the status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready. Drop an ebook file to begin.")

    def on_file_selected(self, file_path: str):
        """Handle file selection"""
        self.current_file = file_path
        self.status_bar.showMessage(f"Loading: {Path(file_path).name}...")

        try:
            # Import the chapter extraction functions
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from audiobook_generator import extract_chapters, get_file_type

            # Extract chapters
            file_type = get_file_type(file_path)
            self.chapters = list(extract_chapters(file_path, file_type))

            if not self.chapters:
                QMessageBox.warning(
                    self,
                    "No Chapters Found",
                    f"Could not find any chapters in the selected {file_type.upper()} file."
                )
                self.status_bar.showMessage("No chapters found.")
                return

            # Load chapters into list
            self.chapter_list.load_chapters(self.chapters)

            # Update cost estimate
            self.update_cost_estimate()

            # Enable generate button
            self.generate_btn.setEnabled(True)

            self.status_bar.showMessage(
                f"Loaded {len(self.chapters)} chapters from {Path(file_path).name}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Loading File",
                f"Failed to load file:\n\n{str(e)}"
            )
            self.status_bar.showMessage("Error loading file.")

    def on_voice_changed(self, language_code: str, voice_name: str):
        """Handle voice selection change"""
        self.language_code = language_code
        self.voice_name = voice_name
        self.update_cost_estimate()
        self.status_bar.showMessage(f"Voice changed to: {voice_name}")

    def on_selection_changed(self, selected_indices: list):
        """Handle chapter selection change"""
        self.update_cost_estimate()
        count = len(selected_indices)
        self.status_bar.showMessage(f"{count} chapter(s) selected")

    def update_cost_estimate(self):
        """Update the cost estimate display"""
        if not self.chapters:
            return

        selected_chapters = self.chapter_list.get_selected_chapters()
        if not selected_chapters:
            self.cost_label.setText("No chapters selected")
            return

        # Calculate total characters
        total_chars = sum(len(text) for _, text, _, _ in selected_chapters)

        # Pricing (per million characters)
        voice_type = "Chirp3-HD" if "Chirp3-HD" in self.voice_name else "Neural2"
        price_per_million = 16.00  # Both Chirp3-HD and Neural2

        # Calculate cost
        estimated_cost = (total_chars / 1_000_000) * price_per_million

        # Estimate duration (rough: ~1000 chars per minute of audio)
        duration_minutes = total_chars / 1000
        duration_hours = duration_minutes / 60

        # Format duration
        if duration_hours >= 1:
            hours = int(duration_hours)
            minutes = int((duration_hours - hours) * 60)
            duration_str = f"~{hours}h {minutes}m"
        else:
            duration_str = f"~{int(duration_minutes)}m"

        # Update label
        self.cost_label.setText(
            f"💰 Estimated cost: ${estimated_cost:.2f} | "
            f"⏱️ Duration: {duration_str} | "
            f"📝 {total_chars:,} characters"
        )

    def on_generate_clicked(self):
        """Handle generate button click"""
        selected = self.chapter_list.get_selected_chapters()

        if not selected:
            QMessageBox.warning(
                self,
                "No Chapters Selected",
                "Please select at least one chapter to convert."
            )
            return

        # Show info dialog (prototype)
        QMessageBox.information(
            self,
            "Prototype Limitation",
            f"🎉 Great! This prototype successfully:\n\n"
            f"✅ Loaded your ebook\n"
            f"✅ Extracted {len(self.chapters)} chapters\n"
            f"✅ You selected {len(selected)} chapters\n"
            f"✅ Calculated cost estimate\n\n"
            f"🚀 Full Version Features:\n"
            f"• Google Cloud API integration\n"
            f"• Batch audiobook generation\n"
            f"• Progress tracking\n"
            f"• Audio file download\n\n"
            f"💡 Selected voice: {self.voice_name}\n"
            f"💰 Estimated cost: See above\n\n"
            f"To enable full conversion, you'll need:\n"
            f"1. Google Cloud account (free tier available)\n"
            f"2. Text-to-Speech API enabled\n"
            f"3. Service account credentials\n\n"
            f"The full app will guide you through setup!"
        )

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About Audiobook Generator",
            "🎧 <b>Audiobook Generator (Prototype)</b><br><br>"
            "Convert ebooks (EPUB, DOCX) to audiobooks using<br>"
            "Google Cloud Text-to-Speech API.<br><br>"
            "<b>Business Model:</b> BYOK (Bring Your Own Key)<br>"
            "• You purchase the app ($39-49)<br>"
            "• You use your own Google Cloud account<br>"
            "• You pay Google directly for usage (~$5-20/book)<br><br>"
            "<b>Features:</b><br>"
            "• Drag-and-drop file upload<br>"
            "• Multiple high-quality voices<br>"
            "• Chapter-by-chapter selection<br>"
            "• Cost estimation<br>"
            "• Privacy-first (your data, your cloud)<br><br>"
            "<b>Version:</b> 0.1.0 (Prototype)<br>"
            "<b>Built with:</b> Python, PySide6<br><br>"
            "© 2025 - Educational Prototype"
        )

    def closeEvent(self, event):
        """Handle window close event"""
        reply = QMessageBox.question(
            self,
            "Confirm Exit",
            "Are you sure you want to quit?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()
