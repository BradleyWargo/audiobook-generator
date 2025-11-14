"""
Main application window for Audiobook Generator
"""
import sys
import logging
from pathlib import Path
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QPushButton,
                               QLabel, QMessageBox, QMenuBar,
                               QStatusBar, QHBoxLayout, QGroupBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction

# Import components
from gui.components.file_uploader import FileUploader
from gui.components.voice_selector import VoiceSelector
from gui.components.chapter_list import ChapterList
from gui.setup_wizard import SetupWizard
from gui.progress_dialog import ProgressDialog, ConversionThread

# Import core
from core.config import ConfigManager
from core.engine import AudiobookEngine
from core.parser import EbookParser

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()

        # Initialize configuration and engine
        self.config = ConfigManager()
        self.engine = AudiobookEngine(self.config)
        self.parser = EbookParser()

        # State
        self.current_file = None
        self.chapters = []

        # UI setup
        self.setup_ui()
        self.create_menu_bar()
        self.create_status_bar()

        # Restore window geometry
        geometry = self.config.get_window_geometry()
        if geometry:
            self.restoreGeometry(geometry)

        # Show setup wizard if needed
        if self.config.get_show_setup_wizard_on_start():
            if not self.config.is_google_cloud_configured():
                self.show_setup_wizard()

    def setup_ui(self):
        """Set up the user interface"""
        self.setWindowTitle("Audiobook Generator")
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

        # Setup status notice
        self.setup_notice = QLabel("")
        self.setup_notice.setWordWrap(True)
        self.setup_notice.setVisible(False)
        main_layout.addWidget(self.setup_notice)

        # Update setup notice based on configuration
        self.update_setup_notice()

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

        # Edit menu
        edit_menu = menubar.addMenu("Edit")

        settings_action = QAction("Preferences...", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self.show_preferences)
        edit_menu.addAction(settings_action)

        # Tools menu
        tools_menu = menubar.addMenu("Tools")

        setup_action = QAction("Run Setup Wizard...", self)
        setup_action.triggered.connect(self.show_setup_wizard)
        tools_menu.addAction(setup_action)

        test_connection_action = QAction("Test Google Cloud Connection", self)
        test_connection_action.triggered.connect(self.test_connection)
        tools_menu.addAction(test_connection_action)

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

        # Save last used directory
        self.config.set_last_input_directory(str(Path(file_path).parent))

        try:
            # Extract chapters using engine
            self.chapters = self.engine.extract_chapters(file_path)

            if not self.chapters:
                QMessageBox.warning(
                    self,
                    "No Chapters Found",
                    f"Could not find any chapters in the selected file.\n\n"
                    f"For DOCX files, make sure chapters use 'Heading 1' style."
                )
                self.status_bar.showMessage("No chapters found.")
                return

            # Load chapters into list
            self.chapter_list.load_chapters(self.chapters)

            # Update cost estimate
            self.update_cost_estimate()

            # Enable generate button only if Google Cloud is configured
            if self.config.is_google_cloud_configured():
                self.generate_btn.setEnabled(True)
            else:
                self.generate_btn.setEnabled(False)
                self.update_setup_notice()

            self.status_bar.showMessage(
                f"Loaded {len(self.chapters)} chapters from {Path(file_path).name}"
            )

        except Exception as e:
            logger.error(f"Error loading file: {e}")
            QMessageBox.critical(
                self,
                "Error Loading File",
                f"Failed to load file:\n\n{str(e)}"
            )
            self.status_bar.showMessage("Error loading file.")

    def on_voice_changed(self, language_code: str, voice_name: str):
        """Handle voice selection change"""
        # Save to config
        self.config.set_voice_language(language_code)
        self.config.set_voice_name(voice_name)

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

        # Use engine to estimate cost
        voice_name = self.config.get_voice_name()
        estimate = self.engine.estimate_cost(selected_chapters, voice_name)

        # Format duration
        duration_hours = estimate['duration_hours']
        if duration_hours >= 1:
            hours = int(duration_hours)
            minutes = int((duration_hours - hours) * 60)
            duration_str = f"~{hours}h {minutes}m"
        else:
            duration_str = f"~{int(estimate['duration_minutes'])}m"

        # Update label
        self.cost_label.setText(
            f"💰 Estimated cost: ${estimate['estimated_cost']:.2f} | "
            f"⏱️ Duration: {duration_str} | "
            f"📝 {estimate['total_characters']:,} characters"
        )

    def on_generate_clicked(self):
        """Handle generate button click"""
        # Check if Google Cloud is configured
        if not self.config.is_google_cloud_configured():
            reply = QMessageBox.question(
                self,
                "Setup Required",
                "Google Cloud is not configured yet.\n\n"
                "Would you like to run the setup wizard now?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.show_setup_wizard()
            return

        selected_indices = self.chapter_list.get_selected_indices()

        if not selected_indices:
            QMessageBox.warning(
                self,
                "No Chapters Selected",
                "Please select at least one chapter to convert."
            )
            return

        # Get selected chapters info for display
        selected_chapters = self.chapter_list.get_selected_chapters()
        chapter_titles = [original_title for _, _, _, original_title in selected_chapters]

        # Determine output base name
        output_base_name = self.config.get_output_base_name()
        if self.config.get_use_book_title() and self.current_file:
            # Use book filename as base
            output_base_name = Path(self.current_file).stem

        # Show confirmation dialog with cost estimate
        estimate = self.engine.estimate_cost(selected_chapters)
        reply = QMessageBox.question(
            self,
            "Confirm Conversion",
            f"Ready to generate audiobook!\n\n"
            f"📚 Chapters: {len(selected_indices)} selected\n"
            f"💰 Estimated cost: ${estimate['estimated_cost']:.2f}\n"
            f"⏱️ Estimated duration: {int(estimate['duration_hours'])}h {int((estimate['duration_hours'] % 1) * 60)}m of audio\n\n"
            f"This will use your Google Cloud account.\n"
            f"Continue?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        # Create and show progress dialog
        progress_dialog = ProgressDialog(self)
        progress_dialog.start_conversion(chapter_titles)

        # Create conversion thread
        self.conversion_thread = ConversionThread(
            engine=self.engine,
            chapters=self.chapters,
            selected_indices=selected_indices,
            output_base_name=output_base_name,
            parent=self
        )

        # Connect signals
        self.conversion_thread.progress.connect(progress_dialog.update_progress)
        self.conversion_thread.finished.connect(
            lambda succ, fail: self.on_conversion_complete(progress_dialog, succ, fail)
        )
        self.conversion_thread.error.connect(
            lambda msg: self.on_conversion_error(progress_dialog, msg)
        )

        # Start conversion
        self.conversion_thread.start()
        progress_dialog.exec()

    def on_conversion_complete(self, dialog, successful, failed):
        """Handle conversion completion"""
        dialog.conversion_complete(successful, failed)

        if successful > 0:
            output_dir = self.config.get_output_directory()
            QMessageBox.information(
                self,
                "Conversion Complete",
                f"🎉 Audiobook generation complete!\n\n"
                f"✅ Success: {successful} chapters\n"
                f"❌ Failed: {failed} chapters\n\n"
                f"📁 Files saved to:\n{output_dir}"
            )

    def on_conversion_error(self, dialog, error_msg):
        """Handle conversion error"""
        QMessageBox.critical(
            dialog,
            "Conversion Error",
            f"An error occurred during conversion:\n\n{error_msg}"
        )
        dialog.accept()

    def show_setup_wizard(self):
        """Show Google Cloud setup wizard"""
        wizard = SetupWizard(self.config, self)
        if wizard.exec():
            # Setup complete, update UI
            self.update_setup_notice()
            if self.chapters:
                self.generate_btn.setEnabled(True)
            QMessageBox.information(
                self,
                "Setup Complete",
                "Google Cloud has been configured successfully!\n\n"
                "You can now convert ebooks to audiobooks."
            )

    def show_preferences(self):
        """Show preferences window"""
        # TODO: Implement preferences window
        QMessageBox.information(
            self,
            "Preferences",
            "Preferences window coming soon!\n\n"
            "For now, you can:\n"
            "• Run Setup Wizard (Tools menu)\n"
            "• Test Connection (Tools menu)"
        )

    def test_connection(self):
        """Test Google Cloud connection"""
        if not self.config.is_google_cloud_configured():
            QMessageBox.warning(
                self,
                "Not Configured",
                "Google Cloud is not configured yet.\n\n"
                "Please run the setup wizard first."
            )
            return

        self.status_bar.showMessage("Testing connection...")
        success, message = self.engine.test_google_cloud_connection()

        if success:
            QMessageBox.information(
                self,
                "Connection Successful",
                f"✅ {message}\n\nYour Google Cloud setup is working correctly!"
            )
            self.status_bar.showMessage("Connection test passed")
        else:
            QMessageBox.critical(
                self,
                "Connection Failed",
                f"❌ {message}\n\n"
                f"Please check your configuration in the setup wizard."
            )
            self.status_bar.showMessage("Connection test failed")

    def update_setup_notice(self):
        """Update the setup notice based on configuration status"""
        if self.config.is_google_cloud_configured():
            self.setup_notice.setVisible(False)
        else:
            self.setup_notice.setText(
                "⚠️ Google Cloud is not configured. "
                "Click here or use Tools > Run Setup Wizard to get started."
            )
            self.setup_notice.setStyleSheet("""
                background-color: #fff3cd;
                color: #856404;
                padding: 10px;
                border-radius: 5px;
                font-size: 11px;
            """)
            self.setup_notice.setVisible(True)
            self.setup_notice.mousePressEvent = lambda e: self.show_setup_wizard()
            self.setup_notice.setCursor(Qt.PointingHandCursor)

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About Audiobook Generator",
            "🎧 <b>Audiobook Generator</b><br><br>"
            "Convert ebooks (EPUB, DOCX) to audiobooks using<br>"
            "Google Cloud Text-to-Speech API.<br><br>"
            "<b>Business Model:</b> BYOK (Bring Your Own Key)<br>"
            "• One-time purchase<br>"
            "• You use your own Google Cloud account<br>"
            "• You pay Google directly for usage (~$5-20/book)<br><br>"
            "<b>Features:</b><br>"
            "• Drag-and-drop file upload<br>"
            "• 100+ premium voices in 40+ languages<br>"
            "• Chapter-by-chapter selection<br>"
            "• Real-time cost estimation<br>"
            "• Privacy-first (your data, your cloud)<br>"
            "• Batch processing<br><br>"
            "<b>Version:</b> 1.0.0<br>"
            "<b>Built with:</b> Python, PySide6, Google Cloud<br><br>"
            "© 2025"
        )

    def closeEvent(self, event):
        """Handle window close event"""
        # Save window geometry
        self.config.set_window_geometry(self.saveGeometry())

        # Confirm exit if conversion is running
        if hasattr(self, 'conversion_thread') and self.conversion_thread.isRunning():
            reply = QMessageBox.question(
                self,
                "Conversion in Progress",
                "A conversion is currently running.\n\n"
                "Are you sure you want to quit? Progress will be lost.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                self.conversion_thread.cancel()
                self.conversion_thread.wait()  # Wait for thread to finish
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
