"""
Voice selector widget for choosing TTS voice
"""
from PySide6.QtWidgets import (QWidget, QComboBox, QPushButton, QHBoxLayout,
                               QVBoxLayout, QLabel, QGroupBox)
from PySide6.QtCore import Signal


class VoiceSelector(QWidget):
    """Widget for selecting TTS voice settings"""

    voice_changed = Signal(str, str)  # Emits (language_code, voice_name)

    # Voice library
    VOICES = {
        'English (US)': {
            'language_code': 'en-US',
            'voices': {
                'Male - Umbriel (Chirp3-HD)': 'en-US-Chirp3-HD-Umbriel',
                'Female - Despina (Chirp3-HD)': 'en-US-Chirp3-HD-Despina',
                'Male - D (Neural2)': 'en-US-Neural2-D',
                'Female - F (Neural2)': 'en-US-Neural2-F',
            }
        },
        'English (UK)': {
            'language_code': 'en-GB',
            'voices': {
                'Male - Umbriel (Chirp3-HD)': 'en-GB-Chirp3-HD-Umbriel',
                'Female - Despina (Chirp3-HD)': 'en-GB-Chirp3-HD-Despina',
                'Male - Alnilam (Chirp3-HD)': 'en-GB-Chirp3-HD-Alnilam',
            }
        },
        'Spanish (US)': {
            'language_code': 'es-US',
            'voices': {
                'Male - Enceladus (Chirp3-HD)': 'es-US-Chirp3-HD-Enceladus',
            }
        },
        'Korean': {
            'language_code': 'ko-KR',
            'voices': {
                'Male - Umbriel (Chirp3-HD)': 'ko-KR-Chirp3-HD-Umbriel',
            }
        },
        'Japanese': {
            'language_code': 'ja-JP',
            'voices': {
                'Male - Umbriel (Chirp3-HD)': 'ja-JP-Chirp3-HD-Umbriel',
            }
        },
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface"""
        layout = QVBoxLayout()

        # Create group box
        group = QGroupBox("🎙️ Voice Settings")
        group_layout = QVBoxLayout()

        # Language selector
        lang_layout = QHBoxLayout()
        lang_label = QLabel("Language:")
        lang_label.setMinimumWidth(80)
        self.language_combo = QComboBox()
        self.language_combo.addItems(self.VOICES.keys())
        self.language_combo.setCurrentText('English (UK)')  # Default
        self.language_combo.currentTextChanged.connect(self.on_language_changed)
        lang_layout.addWidget(lang_label)
        lang_layout.addWidget(self.language_combo, 1)
        group_layout.addLayout(lang_layout)

        # Voice selector
        voice_layout = QHBoxLayout()
        voice_label = QLabel("Voice:")
        voice_label.setMinimumWidth(80)
        self.voice_combo = QComboBox()
        self.voice_combo.currentTextChanged.connect(self.on_voice_changed)
        voice_layout.addWidget(voice_label)
        voice_layout.addWidget(self.voice_combo, 1)

        # Preview button (disabled for now - would require API call)
        self.preview_btn = QPushButton("🔊 Preview")
        self.preview_btn.setEnabled(False)
        self.preview_btn.setToolTip("Voice preview requires Google Cloud credentials")
        voice_layout.addWidget(self.preview_btn)
        group_layout.addLayout(voice_layout)

        # Info label
        self.info_label = QLabel("💡 Uses Google Cloud Text-to-Speech Chirp3-HD voices")
        self.info_label.setStyleSheet("color: #666; font-size: 11px; padding: 5px;")
        group_layout.addWidget(self.info_label)

        group.setLayout(group_layout)
        layout.addWidget(group)
        self.setLayout(layout)

        # Initialize voices for default language
        self.on_language_changed(self.language_combo.currentText())

    def on_language_changed(self, language: str):
        """Handle language selection change"""
        if language not in self.VOICES:
            return

        # Update voice combo box
        self.voice_combo.clear()
        voices = self.VOICES[language]['voices']
        self.voice_combo.addItems(voices.keys())

        # Auto-select first voice
        if voices:
            self.on_voice_changed(list(voices.keys())[0])

    def on_voice_changed(self, voice_display_name: str):
        """Handle voice selection change"""
        language = self.language_combo.currentText()
        if language not in self.VOICES:
            return

        voices = self.VOICES[language]['voices']
        if voice_display_name not in voices:
            return

        language_code = self.VOICES[language]['language_code']
        voice_name = voices[voice_display_name]

        # Emit the change
        self.voice_changed.emit(language_code, voice_name)

    def get_selected_voice(self):
        """Get the currently selected voice settings"""
        language = self.language_combo.currentText()
        if language not in self.VOICES:
            return None, None

        language_code = self.VOICES[language]['language_code']
        voice_display_name = self.voice_combo.currentText()
        voice_name = self.VOICES[language]['voices'].get(voice_display_name)

        return language_code, voice_name

    def set_voice(self, language_code: str, voice_name: str):
        """Set the voice selection programmatically"""
        # Find matching language
        for lang_display, lang_data in self.VOICES.items():
            if lang_data['language_code'] == language_code:
                self.language_combo.setCurrentText(lang_display)

                # Find matching voice
                for voice_display, voice_id in lang_data['voices'].items():
                    if voice_id == voice_name:
                        self.voice_combo.setCurrentText(voice_display)
                        return
