"""
Setup wizard for Google Cloud configuration
Guides users through BYOK setup step-by-step
"""
from PySide6.QtWidgets import (QWizard, QWizardPage, QVBoxLayout, QLabel,
                               QLineEdit, QPushButton, QTextBrowser, QFileDialog,
                               QHBoxLayout, QProgressBar, QMessageBox, QCheckBox)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont
from pathlib import Path


class SetupWizard(QWizard):
    """Wizard for setting up Google Cloud for BYOK"""

    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config = config_manager

        self.setWindowTitle("Google Cloud Setup Wizard")
        self.setWizardStyle(QWizard.ModernStyle)
        self.setMinimumSize(700, 550)

        # Add pages
        self.addPage(WelcomePage(self.config))
        self.addPage(ProjectIDPage(self.config))
        self.addPage(BucketNamePage(self.config))
        self.addPage(CredentialsPage(self.config))
        self.addPage(TestConnectionPage(self.config))
        self.addPage(CompletionPage(self.config))

        # Style
        self.setStyleSheet("""
            QWizard {
                background-color: #f5f5f5;
            }
            QLabel {
                font-size: 13px;
            }
            QLabel[heading="true"] {
                font-size: 18px;
                font-weight: bold;
                color: #0066cc;
            }
            QTextBrowser {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-size: 13px;
            }
            QPushButton {
                padding: 8px 16px;
                background-color: #0066cc;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #0052a3;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)


class WelcomePage(QWizardPage):
    """Welcome page explaining the setup process"""

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.setTitle("Welcome to Audiobook Generator!")
        self.setSubTitle("Let's set up your Google Cloud account for text-to-speech")

        layout = QVBoxLayout()

        # Welcome message
        welcome = QTextBrowser()
        welcome.setOpenExternalLinks(True)
        welcome.setHtml("""
            <h2>🎧 Ready to Create Audiobooks?</h2>

            <p>This wizard will help you set up Google Cloud Text-to-Speech in about <b>10 minutes</b>.</p>

            <h3>What You'll Need:</h3>
            <ul>
                <li>💳 <b>Google account</b> (free to create)</li>
                <li>💰 <b>Credit card</b> for verification (won't be charged without approval)</li>
                <li>⏱️ <b>10 minutes</b> of your time</li>
            </ul>

            <h3>Costs:</h3>
            <ul>
                <li>✅ <b>$300 free credits</b> for new Google Cloud accounts (~150-200 books worth!)</li>
                <li>💵 After credits: <b>~$5-20 per typical book</b></li>
                <li>🎯 <b>You're in control</b> – only pay for what you use</li>
            </ul>

            <h3>Privacy:</h3>
            <ul>
                <li>🔒 Your books go to <b>YOUR</b> Google Cloud account</li>
                <li>👁️ We <b>never</b> see your content</li>
                <li>✅ Complete control over your data</li>
            </ul>

            <p><i>Click "Next" to begin setup, or "Cancel" to set this up later.</i></p>
        """)
        layout.addWidget(welcome)

        # Don't show again checkbox
        self.dont_show = QCheckBox("Don't show this wizard on startup (you can run it from Settings)")
        if not self.config.get_show_setup_wizard_on_start():
            self.dont_show.setChecked(True)
        self.dont_show.toggled.connect(self.on_dont_show_toggled)
        layout.addWidget(self.dont_show)

        self.setLayout(layout)

    def on_dont_show_toggled(self, checked):
        """Handle don't show checkbox"""
        self.config.set_show_setup_wizard_on_start(not checked)


class ProjectIDPage(QWizardPage):
    """Page for entering Google Cloud project ID"""

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.setTitle("Step 1: Google Cloud Project")
        self.setSubTitle("Create a project and enter your Project ID")

        layout = QVBoxLayout()

        # Instructions
        instructions = QTextBrowser()
        instructions.setOpenExternalLinks(True)
        instructions.setMaximumHeight(300)
        instructions.setHtml("""
            <h3>📋 Instructions:</h3>
            <ol>
                <li><b>Go to:</b> <a href="https://console.cloud.google.com">console.cloud.google.com</a></li>
                <li>Sign in with your Google account (or create one)</li>
                <li>Click <b>"Select a project"</b> at the top</li>
                <li>Click <b>"NEW PROJECT"</b></li>
                <li>Enter a name like <b>"Audiobook Generator"</b></li>
                <li>Click <b>"CREATE"</b></li>
                <li>Wait for project creation (~30 seconds)</li>
                <li>Copy your <b>Project ID</b> (shown below the project name)</li>
                <li>Paste it below 👇</li>
            </ol>

            <p><b>💡 Tip:</b> The Project ID looks like <code>audiobook-generator-12345</code></p>
        """)
        layout.addWidget(instructions)

        # Input field
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("Project ID:"))
        self.project_id_input = QLineEdit()
        self.project_id_input.setPlaceholderText("e.g., audiobook-generator-12345")

        # Load existing value
        existing = self.config.get_project_id()
        if existing:
            self.project_id_input.setText(existing)

        self.project_id_input.textChanged.connect(self.validate_input)
        self.registerField("project_id*", self.project_id_input)
        input_layout.addWidget(self.project_id_input)
        layout.addLayout(input_layout)

        # Validation label
        self.validation_label = QLabel("")
        self.validation_label.setStyleSheet("color: red; font-style: italic;")
        layout.addWidget(self.validation_label)

        self.setLayout(layout)

    def validate_input(self):
        """Validate project ID format"""
        text = self.project_id_input.text().strip()
        if text and not re.match(r'^[a-z][a-z0-9-]*[a-z0-9]$', text):
            self.validation_label.setText("⚠️ Project ID should be lowercase letters, numbers, and hyphens")
            return False
        else:
            self.validation_label.setText("")
            return True

    def validatePage(self):
        """Validate before moving to next page"""
        project_id = self.project_id_input.text().strip()
        if project_id:
            self.config.set_project_id(project_id)
            return True
        return False


class BucketNamePage(QWizardPage):
    """Page for entering Google Cloud Storage bucket name"""

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.setTitle("Step 2: Cloud Storage Bucket")
        self.setSubTitle("Create a storage bucket for temporary audio files")

        layout = QVBoxLayout()

        # Instructions
        instructions = QTextBrowser()
        instructions.setOpenExternalLinks(True)
        instructions.setMaximumHeight(300)
        instructions.setHtml("""
            <h3>📦 Instructions:</h3>
            <ol>
                <li><b>Go to:</b> <a href="https://console.cloud.google.com/storage">console.cloud.google.com/storage</a></li>
                <li>Make sure your project is selected at the top</li>
                <li>Click <b>"CREATE BUCKET"</b></li>
                <li>Enter a unique name (e.g., <code>audiobook-generator-yourname-12345</code>)</li>
                <li>Choose a <b>Region</b> closest to you</li>
                <li>Keep default settings for everything else</li>
                <li>Click <b>"CREATE"</b></li>
                <li>Copy the bucket name and paste it below 👇</li>
            </ol>

            <p><b>💡 Tip:</b> Bucket names must be globally unique and lowercase.</p>
        """)
        layout.addWidget(instructions)

        # Input field
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("Bucket Name:"))
        self.bucket_input = QLineEdit()
        self.bucket_input.setPlaceholderText("e.g., audiobook-generator-yourname-12345")

        # Load existing value
        existing = self.config.get_bucket_name()
        if existing:
            self.bucket_input.setText(existing)

        self.bucket_input.textChanged.connect(self.validate_input)
        self.registerField("bucket_name*", self.bucket_input)
        input_layout.addWidget(self.bucket_input)
        layout.addLayout(input_layout)

        # Validation label
        self.validation_label = QLabel("")
        self.validation_label.setStyleSheet("color: red; font-style: italic;")
        layout.addWidget(self.validation_label)

        self.setLayout(layout)

    def validate_input(self):
        """Validate bucket name format"""
        text = self.bucket_input.text().strip()
        if text and not re.match(r'^[a-z0-9][a-z0-9-_]*[a-z0-9]$', text):
            self.validation_label.setText("⚠️ Bucket name should be lowercase letters, numbers, hyphens, and underscores")
            return False
        else:
            self.validation_label.setText("")
            return True

    def validatePage(self):
        """Validate before moving to next page"""
        bucket_name = self.bucket_input.text().strip()
        if bucket_name:
            self.config.set_bucket_name(bucket_name)
            return True
        return False


class CredentialsPage(QWizardPage):
    """Page for uploading service account credentials"""

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.setTitle("Step 3: Service Account Credentials")
        self.setSubTitle("Create and upload your API credentials")

        layout = QVBoxLayout()

        # Instructions
        instructions = QTextBrowser()
        instructions.setOpenExternalLinks(True)
        instructions.setMaximumHeight(350)
        instructions.setHtml("""
            <h3>🔑 Instructions:</h3>
            <ol>
                <li><b>Enable the API:</b> Go to <a href="https://console.cloud.google.com/apis/library/texttospeech.googleapis.com">Text-to-Speech API</a> and click <b>"ENABLE"</b></li>
                <li><b>Create Service Account:</b>
                    <ul>
                        <li>Go to: <a href="https://console.cloud.google.com/iam-admin/serviceaccounts">Service Accounts</a></li>
                        <li>Click <b>"CREATE SERVICE ACCOUNT"</b></li>
                        <li>Name: <code>audiobook-generator</code></li>
                        <li>Click <b>"CREATE AND CONTINUE"</b></li>
                        <li>Grant role: <b>"Editor"</b> (or "Storage Object Admin" + "Cloud Text-to-Speech User")</li>
                        <li>Click <b>"CONTINUE"</b>, then <b>"DONE"</b></li>
                    </ul>
                </li>
                <li><b>Download Key:</b>
                    <ul>
                        <li>Click on the service account you just created</li>
                        <li>Go to the <b>"KEYS"</b> tab</li>
                        <li>Click <b>"ADD KEY"</b> → <b>"Create new key"</b></li>
                        <li>Choose <b>"JSON"</b></li>
                        <li>Click <b>"CREATE"</b></li>
                        <li>A JSON file will download automatically</li>
                    </ul>
                </li>
                <li>Click "Browse" below and select the downloaded JSON file 👇</li>
            </ol>
        """)
        layout.addWidget(instructions)

        # File selection
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("Credentials File:"))
        self.file_path_display = QLineEdit()
        self.file_path_display.setReadOnly(True)
        self.file_path_display.setPlaceholderText("No file selected")

        # Load existing value
        existing = self.config.get_credentials_path()
        if existing:
            self.file_path_display.setText(existing)

        self.registerField("credentials_path*", self.file_path_display)
        file_layout.addWidget(self.file_path_display)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_credentials)
        file_layout.addWidget(browse_btn)
        layout.addLayout(file_layout)

        self.setLayout(layout)

    def browse_credentials(self):
        """Open file dialog to select credentials JSON"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Service Account Key JSON",
            str(Path.home()),
            "JSON Files (*.json)"
        )
        if file_path:
            self.file_path_display.setText(file_path)

    def validatePage(self):
        """Validate credentials file"""
        file_path = self.file_path_display.text()
        if file_path and Path(file_path).exists():
            self.config.set_credentials_path(file_path)
            return True
        else:
            QMessageBox.warning(self, "Invalid File", "Please select a valid JSON credentials file.")
            return False


class TestConnectionPage(QWizardPage):
    """Page for testing the Google Cloud connection"""

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.setTitle("Step 4: Test Connection")
        self.setSubTitle("Verify your Google Cloud setup")

        self.test_complete = False

        layout = QVBoxLayout()

        # Info
        info = QLabel("Click 'Test Connection' to verify your setup is working correctly.")
        info.setWordWrap(True)
        layout.addWidget(info)

        # Test button
        self.test_btn = QPushButton("🔌 Test Connection")
        self.test_btn.clicked.connect(self.test_connection)
        self.test_btn.setMinimumHeight(50)
        layout.addWidget(self.test_btn)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setTextVisible(False)
        layout.addWidget(self.progress)

        # Result label
        self.result_label = QLabel("")
        self.result_label.setWordWrap(True)
        self.result_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.result_label)

        layout.addStretch()
        self.setLayout(layout)

    def test_connection(self):
        """Test Google Cloud connection"""
        self.test_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)  # Indeterminate
        self.result_label.setText("Testing connection...")
        self.result_label.setStyleSheet("color: blue;")

        # Run test in thread to avoid freezing UI
        self.test_thread = TestConnectionThread(self.config)
        self.test_thread.finished.connect(self.on_test_complete)
        self.test_thread.start()

    def on_test_complete(self, success, message):
        """Handle test completion"""
        self.progress.setVisible(False)
        self.test_btn.setEnabled(True)

        if success:
            self.result_label.setText(f"✅ {message}\n\nYou're all set! Click 'Next' to finish.")
            self.result_label.setStyleSheet("color: green; font-weight: bold;")
            self.test_complete = True
            self.completeChanged.emit()
        else:
            self.result_label.setText(f"❌ {message}\n\nPlease check your settings and try again.")
            self.result_label.setStyleSheet("color: red;")
            self.test_complete = False

    def isComplete(self):
        """Page is complete when test passes"""
        return self.test_complete


class TestConnectionThread(QThread):
    """Thread for testing Google Cloud connection"""
    finished = Signal(bool, str)

    def __init__(self, config):
        super().__init__()
        self.config = config

    def run(self):
        """Run connection test"""
        try:
            from core.engine import AudiobookEngine
            engine = AudiobookEngine(self.config)
            success, message = engine.test_google_cloud_connection()
            self.finished.emit(success, message)
        except Exception as e:
            self.finished.emit(False, f"Test failed: {str(e)}")


class CompletionPage(QWizardPage):
    """Completion page"""

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.setTitle("🎉 Setup Complete!")
        self.setSubTitle("You're ready to create audiobooks")

        layout = QVBoxLayout()

        # Success message
        success = QTextBrowser()
        success.setHtml("""
            <h2>✅ All Set!</h2>

            <p>Your Google Cloud account is configured and ready to use.</p>

            <h3>What's Next?</h3>
            <ol>
                <li><b>Drop an ebook</b> file (EPUB or DOCX) into the app</li>
                <li><b>Select chapters</b> you want to convert</li>
                <li><b>Choose a voice</b> from 40+ languages</li>
                <li><b>Click "Generate"</b> and wait for your audiobook!</li>
            </ol>

            <h3>💰 Remember:</h3>
            <ul>
                <li>You have <b>$300 in free credits</b> (~150-200 books worth)</li>
                <li>After that, typical costs are <b>$5-20 per book</b></li>
                <li>Monitor usage at: <a href="https://console.cloud.google.com/billing">console.cloud.google.com/billing</a></li>
            </ul>

            <h3>Need Help?</h3>
            <ul>
                <li>📖 Check the Help menu for tutorials</li>
                <li>⚙️ Access Settings to adjust preferences</li>
                <li>📧 Email support (coming soon)</li>
            </ul>

            <p><b>Click "Finish" to start creating audiobooks!</b></p>
        """)
        layout.addWidget(success)

        self.setLayout(layout)


# Import re for validation
import re
