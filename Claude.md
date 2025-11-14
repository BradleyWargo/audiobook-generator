# Mac App Development Plan - Audiobook Generator

## Project Overview
Transform the CLI-based audiobook generator into a native macOS application with drag-and-drop file upload, GUI controls, and modern UX.

---

## Current State Analysis

### ✅ What We Have
- **Core Engine**: Fully functional TTS conversion (`audiobook_generator.py`)
- **Format Support**: EPUB and DOCX parsing
- **Google Cloud Integration**: TTS API with long-form audio synthesis
- **Chapter Management**: Smart chapter extraction and selection
- **Error Handling**: Comprehensive logging and retry logic
- **Cost Estimation**: Built-in cost calculator (lines 702-771)
- **Progress Tracking**: tqdm-based progress bars

### ❌ What's Missing for Mac App
- No graphical user interface
- No drag-and-drop file handling
- No real-time progress visualization
- Manual configuration editing required
- No app bundle/installer
- No macOS integration (menu bar, notifications, etc.)

---

## Mac App Development Roadmap

## Phase 1: Architecture Refactoring (2-3 days)

### 1.1 Separate Business Logic from CLI Code
**Current Problem**: All logic is in one monolithic file with print statements and CLI interactions

**Solution**: Create a clean separation

```
src/
├── audiobook_generator.py        # Original CLI (keep for backwards compatibility)
├── core/
│   ├── __init__.py
│   ├── engine.py                 # Core TTS processing logic
│   ├── parser.py                 # EPUB/DOCX chapter extraction
│   ├── tts_client.py             # Google Cloud TTS wrapper
│   └── utils.py                  # Sanitization, cost estimation, etc.
├── gui/
│   ├── __init__.py
│   ├── main_window.py            # Main application window
│   ├── components/
│   │   ├── file_uploader.py      # Drag-and-drop widget
│   │   ├── voice_selector.py     # Voice selection UI
│   │   ├── chapter_list.py       # Chapter selection widget
│   │   └── progress_panel.py     # Real-time progress display
│   └── config_manager.py         # Settings/preferences GUI
└── app.py                        # macOS app entry point
```

**Key Changes**:
- Extract all processing logic into `core/engine.py`
- Remove all `print()` and `input()` statements from core logic
- Use callbacks/signals for progress updates
- Make all functions return values instead of printing

**Example Refactor**:
```python
# Before (in audiobook_generator.py):
def synthesize_audio(chapter_text):
    print(f"Processing chapter...")
    # process
    print(f"✅ Done!")

# After (in core/engine.py):
class AudiobookEngine:
    def synthesize_audio(self, chapter_text, progress_callback=None):
        if progress_callback:
            progress_callback("processing", 0)
        # process
        if progress_callback:
            progress_callback("completed", 100)
        return result
```

### 1.2 Async/Threading Architecture
**Why**: GUI must never freeze during long operations

**Implementation**:
```python
# gui/main_window.py
import threading
from queue import Queue

class MainWindow:
    def __init__(self):
        self.progress_queue = Queue()
        self.worker_thread = None

    def start_conversion(self):
        self.worker_thread = threading.Thread(
            target=self._run_conversion,
            daemon=True
        )
        self.worker_thread.start()
        self.after(100, self._check_progress)

    def _run_conversion(self):
        # Runs in background thread
        engine.synthesize_all_chapters(
            progress_callback=self.progress_queue.put
        )

    def _check_progress(self):
        # Runs in main thread, updates GUI
        while not self.progress_queue.empty():
            status = self.progress_queue.get()
            self.update_progress_bar(status)
        self.after(100, self._check_progress)
```

---

## Phase 2: GUI Framework Selection (1 day)

### Recommendation: **PyQt6** or **PySide6**

**Why PyQt6/PySide6**:
- ✅ Native-looking macOS UI
- ✅ Drag-and-drop support built-in
- ✅ Professional appearance
- ✅ Good documentation
- ✅ Easy to package with py2app
- ✅ Supports macOS dark mode automatically

**Alternative Options**:

| Framework | Pros | Cons | Recommendation |
|-----------|------|------|----------------|
| **Tkinter** | Built-in, simple | Looks dated, limited widgets | ❌ Not for professional app |
| **PyQt6/PySide6** | Professional, native look | Larger package size | ✅ **Best choice** |
| **Kivy** | Modern, touch-friendly | Non-native look | ❌ Not Mac-like |
| **SwiftUI + Python** | True native Mac | Requires Swift rewrite | ❌ Too much work |
| **Electron + Python** | Modern web UI | Huge bundle size | ⚠️ Only if web-based |

**Decision: Go with PySide6** (LGPL license, Qt for Python official)

```bash
pip install PySide6
```

---

## Phase 3: GUI Components Design (3-4 days)

### 3.1 Main Window Layout

```
┌─────────────────────────────────────────────────────────────┐
│ Audiobook Generator                          ☐  ▭  ✕        │
├─────────────────────────────────────────────────────────────┤
│ File  Edit  View  Help                                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  📖 DROP EBOOK FILE HERE                                    │
│     or click to browse                                       │
│     ┌───────────────────────────────────────────┐           │
│     │  🎯  my-book.epub                         │           │
│     │  📊  250,000 characters • ~4.2 hours      │           │
│     └───────────────────────────────────────────┘           │
│                                                              │
│  🎙️ Voice Settings                                          │
│     Language:  [English (US)      ▼]                        │
│     Gender:    [Female            ▼]                        │
│     Voice:     [Chirp3-HD-Despina ▼] [🔊 Preview]          │
│                                                              │
│  📚 Chapters (12 found)                                     │
│     ┌───────────────────────────────────────────┐           │
│     │ ☑ Prologue (1,200 words)                 │           │
│     │ ☑ Chapter 1: The Beginning (3,500 words) │           │
│     │ ☑ Chapter 2: Discovery (4,100 words)     │           │
│     │ ☐ Chapter 3: The Journey (3,800 words)   │ ▲         │
│     │ ...                                       │ █         │
│     └───────────────────────────────────────────┘ ▼         │
│     [☑ Select All]  [☐ Deselect All]                       │
│                                                              │
│  💰 Cost Estimate: $4.28  •  ⏱️ Duration: ~4h 15m          │
│                                                              │
│  [⚙️ Settings]            [▶️  Generate Audiobook]          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Progress Window (appears during processing)

```
┌─────────────────────────────────────────┐
│ Generating Audiobook...        ☐  ▭  ✕ │
├─────────────────────────────────────────┤
│                                         │
│  Chapter 3 of 12: "The Journey"        │
│  ████████████░░░░░░░░░░  65%           │
│                                         │
│  Status: Uploading to Google Cloud...  │
│  Time elapsed: 12m 34s                  │
│  Estimated remaining: 6m 12s            │
│                                         │
│  ✅ Prologue                            │
│  ✅ Chapter 1: The Beginning            │
│  ✅ Chapter 2: Discovery                │
│  🔄 Chapter 3: The Journey              │
│  ⏳ Chapter 4: ...                      │
│  ⏳ Chapter 5: ...                      │
│                                         │
│         [❚❚ Pause]    [■ Cancel]       │
│                                         │
└─────────────────────────────────────────┘
```

### 3.3 Settings/Preferences Window

```
┌─────────────────────────────────────────────────┐
│ Preferences                         ☐  ▭  ✕    │
├─────────────────────────────────────────────────┤
│ [General] [Google Cloud] [Advanced] [About]    │
├─────────────────────────────────────────────────┤
│                                                 │
│  🔐 Google Cloud Configuration                 │
│                                                 │
│  Project ID:                                    │
│  ┌───────────────────────────────────────────┐ │
│  │ your-project-id                           │ │
│  └───────────────────────────────────────────┘ │
│                                                 │
│  Storage Bucket:                                │
│  ┌───────────────────────────────────────────┐ │
│  │ your-bucket-name                          │ │
│  └───────────────────────────────────────────┘ │
│                                                 │
│  Service Account Key:                           │
│  ┌───────────────────────────────────────────┐ │
│  │ /credentials/audiobook-tts-key.json       │ │
│  └───────────────────────────────────────────┘ │
│  [Browse...]  [Test Connection]                │
│                                                 │
│  📁 Output Settings                            │
│                                                 │
│  Output Directory:                              │
│  ┌───────────────────────────────────────────┐ │
│  │ ~/Documents/Audiobooks                    │ │
│  └───────────────────────────────────────────┘ │
│  [Browse...]                                    │
│                                                 │
│  File Naming:                                   │
│  ☑ Use book title as prefix                   │
│  ☑ Number chapters sequentially                │
│  ☐ Include chapter names in filenames          │
│                                                 │
│  [Cancel]                      [Save Settings] │
│                                                 │
└─────────────────────────────────────────────────┘
```

### 3.4 Component Implementation Details

#### File Upload Widget
```python
# gui/components/file_uploader.py
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent

class FileUploader(QWidget):
    file_dropped = Signal(str)  # Emits file path

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        self.label = QLabel("📖 Drop EPUB/DOCX here\nor click to browse")
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)
        self.setLayout(layout)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            self.file_dropped.emit(files[0])

    def mousePressEvent(self, event):
        # Open file dialog
        from PySide6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Ebook",
            "", "Ebooks (*.epub *.docx)"
        )
        if file_path:
            self.file_dropped.emit(file_path)
```

#### Voice Selector
```python
# gui/components/voice_selector.py
from PySide6.QtWidgets import (QWidget, QComboBox, QPushButton,
                               QHBoxLayout, QVBoxLayout, QLabel)
from PySide6.QtCore import Signal

class VoiceSelector(QWidget):
    voice_changed = Signal(str, str)  # language_code, voice_name
    preview_requested = Signal()

    def __init__(self):
        super().__init__()
        self.voices = self.load_voice_library()
        self.setup_ui()

    def load_voice_library(self):
        return {
            'en-US': {
                'Male': ['en-US-Chirp3-HD-Umbriel', 'en-US-Neural2-D'],
                'Female': ['en-US-Chirp3-HD-Despina', 'en-US-Neural2-F']
            },
            'en-GB': {
                'Male': ['en-GB-Chirp3-HD-Umbriel', 'en-GB-Chirp3-HD-Alnilam'],
                'Female': ['en-GB-Chirp3-HD-Despina']
            },
            # Add more languages...
        }

    def setup_ui(self):
        layout = QVBoxLayout()

        # Language selector
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel("Language:"))
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(self.voices.keys())
        self.lang_combo.currentTextChanged.connect(self.on_language_changed)
        lang_layout.addWidget(self.lang_combo)
        layout.addLayout(lang_layout)

        # Gender selector
        gender_layout = QHBoxLayout()
        gender_layout.addWidget(QLabel("Gender:"))
        self.gender_combo = QComboBox()
        self.gender_combo.currentTextChanged.connect(self.on_gender_changed)
        gender_layout.addWidget(self.gender_combo)
        layout.addLayout(gender_layout)

        # Voice selector with preview button
        voice_layout = QHBoxLayout()
        voice_layout.addWidget(QLabel("Voice:"))
        self.voice_combo = QComboBox()
        self.voice_combo.currentTextChanged.connect(self.on_voice_changed)
        voice_layout.addWidget(self.voice_combo)

        self.preview_btn = QPushButton("🔊 Preview")
        self.preview_btn.clicked.connect(self.preview_requested.emit)
        voice_layout.addWidget(self.preview_btn)
        layout.addLayout(voice_layout)

        self.setLayout(layout)
        self.on_language_changed(self.lang_combo.currentText())
```

#### Chapter List Widget
```python
# gui/components/chapter_list.py
from PySide6.QtWidgets import (QWidget, QListWidget, QListWidgetItem,
                               QCheckBox, QPushButton, QVBoxLayout, QHBoxLayout)
from PySide6.QtCore import Qt, Signal

class ChapterList(QWidget):
    selection_changed = Signal(list)  # List of selected chapter indices

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        self.list_widget = QListWidget()
        self.list_widget.itemChanged.connect(self.on_selection_changed)
        layout.addWidget(self.list_widget)

        # Bulk selection buttons
        btn_layout = QHBoxLayout()
        select_all_btn = QPushButton("☑ Select All")
        select_all_btn.clicked.connect(self.select_all)
        deselect_all_btn = QPushButton("☐ Deselect All")
        deselect_all_btn.clicked.connect(self.deselect_all)
        btn_layout.addWidget(select_all_btn)
        btn_layout.addWidget(deselect_all_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def load_chapters(self, chapters):
        """
        chapters: list of (title, text, chapter_num, original_title)
        """
        self.list_widget.clear()
        for title, text, _, original_title in chapters:
            word_count = len(text.split())
            item_text = f"{original_title} ({word_count:,} words)"
            item = QListWidgetItem(item_text)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)
            self.list_widget.addItem(item)

    def get_selected_indices(self):
        selected = []
        for i in range(self.list_widget.count()):
            if self.list_widget.item(i).checkState() == Qt.Checked:
                selected.append(i)
        return selected

    def select_all(self):
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setCheckState(Qt.Checked)

    def deselect_all(self):
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setCheckState(Qt.Unchecked)
```

---

## Phase 4: macOS-Specific Integration (2-3 days)

### 4.1 App Bundle Structure
```
AudiobookGenerator.app/
└── Contents/
    ├── Info.plist              # App metadata
    ├── MacOS/
    │   └── AudiobookGenerator  # Executable
    ├── Resources/
    │   ├── icon.icns           # App icon
    │   ├── credentials/        # Service account keys
    │   └── lib/                # Python libraries
    └── Frameworks/             # Qt frameworks
```

### 4.2 Create Info.plist
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>AudiobookGenerator</string>

    <key>CFBundleIdentifier</key>
    <string>com.yourname.audiobookgenerator</string>

    <key>CFBundleName</key>
    <string>Audiobook Generator</string>

    <key>CFBundleVersion</key>
    <string>1.0.0</string>

    <key>CFBundleIconFile</key>
    <string>icon.icns</string>

    <key>CFBundleDocumentTypes</key>
    <array>
        <dict>
            <key>CFBundleTypeName</key>
            <string>EPUB Document</string>
            <key>CFBundleTypeExtensions</key>
            <array>
                <string>epub</string>
            </array>
            <key>CFBundleTypeRole</key>
            <string>Viewer</string>
        </dict>
        <dict>
            <key>CFBundleTypeName</key>
            <string>Word Document</string>
            <key>CFBundleTypeExtensions</key>
            <array>
                <string>docx</string>
            </array>
            <key>CFBundleTypeRole</key>
            <string>Viewer</string>
        </dict>
    </array>

    <key>NSHighResolutionCapable</key>
    <true/>

    <key>LSMinimumSystemVersion</key>
    <string>10.14</string>
</dict>
</plist>
```

### 4.3 Packaging with py2app

**Install py2app**:
```bash
pip install py2app
```

**Create setup.py**:
```python
# setup.py
from setuptools import setup

APP = ['src/app.py']
DATA_FILES = [
    ('credentials', ['credentials/audiobook-generator-tts-service-account.json']),
]
OPTIONS = {
    'argv_emulation': True,
    'packages': [
        'google.cloud.texttospeech_v1',
        'google.cloud.storage',
        'ebooklib',
        'bs4',
        'docx',
        'nltk',
        'tqdm',
        'PySide6',
    ],
    'includes': ['nltk.tokenize.punkt'],
    'plist': {
        'CFBundleName': 'Audiobook Generator',
        'CFBundleDisplayName': 'Audiobook Generator',
        'CFBundleIdentifier': 'com.yourname.audiobookgenerator',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHumanReadableCopyright': '© 2025 Your Name',
        'NSHighResolutionCapable': True,
    },
    'iconfile': 'resources/icon.icns',
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
```

**Build the app**:
```bash
python setup.py py2app
```

### 4.4 Code Signing & Notarization

**For distribution outside Mac App Store, you need**:
1. Apple Developer account ($99/year)
2. Developer ID Application certificate
3. Code signing
4. Notarization

**Code Signing**:
```bash
# Sign the app
codesign --deep --force --verify --verbose \
  --sign "Developer ID Application: Your Name (TEAM_ID)" \
  --options runtime \
  dist/AudiobookGenerator.app

# Verify signature
codesign --verify --verbose dist/AudiobookGenerator.app
spctl --assess --verbose dist/AudiobookGenerator.app
```

**Notarization** (so macOS Gatekeeper allows it):
```bash
# Create a DMG
hdiutil create -volname "Audiobook Generator" \
  -srcfolder dist/AudiobookGenerator.app \
  -ov -format UDZO \
  AudiobookGenerator.dmg

# Upload for notarization
xcrun notarytool submit AudiobookGenerator.dmg \
  --apple-id "your@email.com" \
  --password "app-specific-password" \
  --team-id "TEAM_ID" \
  --wait

# Staple the notarization ticket
xcrun stapler staple AudiobookGenerator.dmg
```

### 4.5 macOS-Specific Features to Implement

**Menu Bar Integration**:
```python
# gui/main_window.py
from PySide6.QtWidgets import QMenuBar

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.create_menu_bar()

    def create_menu_bar(self):
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu('File')
        file_menu.addAction('Open Ebook...', self.open_file)
        file_menu.addAction('Preferences...', self.show_preferences)
        file_menu.addSeparator()
        file_menu.addAction('Quit', self.close)

        # Edit menu
        edit_menu = menubar.addMenu('Edit')
        edit_menu.addAction('Select All Chapters', self.select_all_chapters)
        edit_menu.addAction('Deselect All Chapters', self.deselect_all_chapters)

        # Help menu
        help_menu = menubar.addMenu('Help')
        help_menu.addAction('Documentation', self.open_docs)
        help_menu.addAction('About', self.show_about)
```

**Native macOS Notifications**:
```python
# When conversion completes
from PySide6.QtCore import QSystemTrayIcon
from PySide6.QtWidgets import QApplication

def notify_completion(self, book_title):
    if QSystemTrayIcon.isSystemTrayAvailable():
        tray = QSystemTrayIcon(self)
        tray.showMessage(
            "Audiobook Complete",
            f"'{book_title}' has been converted successfully!",
            QSystemTrayIcon.Information,
            3000  # Show for 3 seconds
        )
```

**Dark Mode Support**:
```python
# Automatically handled by Qt, but you can detect it:
from PySide6.QtGui import QPalette

def setup_theme(self):
    palette = self.palette()
    if palette.color(QPalette.Window).lightness() < 128:
        # Dark mode
        self.apply_dark_stylesheet()
    else:
        # Light mode
        self.apply_light_stylesheet()
```

---

## Phase 5: Configuration Management (1 day)

### 5.1 Store Preferences in macOS Standard Location
```python
# gui/config_manager.py
from pathlib import Path
import json
from PySide6.QtCore import QSettings

class ConfigManager:
    def __init__(self):
        # Uses ~/Library/Preferences/com.yourname.audiobookgenerator.plist
        self.settings = QSettings(
            'com.yourname.audiobookgenerator',
            'AudiobookGenerator'
        )

    def get(self, key, default=None):
        return self.settings.value(key, default)

    def set(self, key, value):
        self.settings.setValue(key, value)

    def get_google_cloud_config(self):
        return {
            'project_id': self.get('google_cloud/project_id', ''),
            'bucket_name': self.get('google_cloud/bucket_name', ''),
            'credentials_path': self.get('google_cloud/credentials_path', ''),
        }

    def save_google_cloud_config(self, config):
        self.set('google_cloud/project_id', config['project_id'])
        self.set('google_cloud/bucket_name', config['bucket_name'])
        self.set('google_cloud/credentials_path', config['credentials_path'])

    def get_voice_preferences(self):
        return {
            'language': self.get('voice/language', 'en-US'),
            'voice_name': self.get('voice/name', 'en-US-Chirp3-HD-Despina'),
            'favorite_voices': self.get('voice/favorites', []),
        }

    def save_voice_preferences(self, voice_config):
        self.set('voice/language', voice_config['language'])
        self.set('voice/name', voice_config['voice_name'])

    def get_output_settings(self):
        return {
            'directory': self.get('output/directory', str(Path.home() / 'Documents' / 'Audiobooks')),
            'use_book_title': self.get('output/use_book_title', True),
            'number_chapters': self.get('output/number_chapters', True),
        }
```

---

## Phase 6: Enhanced Features for GUI (2-3 days)

### 6.1 Voice Preview Feature
```python
# core/voice_preview.py
from google.cloud import texttospeech_v1

class VoicePreview:
    def __init__(self):
        self.client = texttospeech_v1.TextToSpeechClient()

    def generate_sample(self, voice_name, language_code, sample_text=None):
        if not sample_text:
            sample_text = "Hello! This is a preview of my voice. I will be narrating your audiobook with this tone and style."

        synthesis_input = texttospeech_v1.SynthesisInput(text=sample_text)
        voice = texttospeech_v1.VoiceSelectionParams(
            language_code=language_code,
            name=voice_name
        )
        audio_config = texttospeech_v1.AudioConfig(
            audio_encoding=texttospeech_v1.AudioEncoding.MP3
        )

        response = self.client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )

        # Return audio bytes that can be played
        return response.audio_content

# In GUI:
def preview_voice(self):
    voice_name = self.voice_selector.get_selected_voice()
    language_code = self.voice_selector.get_selected_language()

    # Show loading indicator
    self.show_loading("Generating preview...")

    # Generate in background thread
    audio_data = self.preview_generator.generate_sample(voice_name, language_code)

    # Play audio
    self.play_audio(audio_data)
```

### 6.2 Real-Time Cost Calculator
```python
# gui/components/cost_estimator.py
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Signal

class CostEstimator(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        self.cost_label = QLabel("💰 Cost: --")
        self.duration_label = QLabel("⏱️ Duration: --")
        layout.addWidget(self.cost_label)
        layout.addWidget(self.duration_label)
        self.setLayout(layout)

    def update_estimate(self, chapters, voice_type):
        total_chars = sum(len(text) for _, text, _, _ in chapters)

        pricing = {
            'Chirp3-HD': 16.00,
            'Neural2': 16.00,
            'WaveNet': 16.00,
            'Standard': 4.00,
        }

        price_per_million = pricing.get(voice_type, 16.00)
        cost = (total_chars / 1_000_000) * price_per_million
        duration_hours = total_chars / 60000  # ~60k chars per hour

        self.cost_label.setText(f"💰 Cost: ${cost:.2f}")

        hours = int(duration_hours)
        minutes = int((duration_hours - hours) * 60)
        self.duration_label.setText(f"⏱️ Duration: ~{hours}h {minutes}m")
```

### 6.3 Batch Processing Queue
```python
# gui/components/batch_queue.py
from PySide6.QtWidgets import QListWidget, QWidget, QVBoxLayout, QPushButton

class BatchQueue(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        self.queue_list = QListWidget()
        layout.addWidget(self.queue_list)

        add_btn = QPushButton("➕ Add Books to Queue")
        add_btn.clicked.connect(self.add_to_queue)
        layout.addWidget(add_btn)

        process_btn = QPushButton("▶️ Process Queue")
        process_btn.clicked.connect(self.process_queue)
        layout.addWidget(process_btn)

        self.setLayout(layout)

    def add_to_queue(self):
        # Open file dialog to select multiple books
        pass

    def process_queue(self):
        # Process all books in queue sequentially
        pass
```

---

## Phase 7: Testing & Debugging (2-3 days)

### 7.1 Unit Tests
```python
# tests/test_engine.py
import unittest
from core.engine import AudiobookEngine

class TestAudiobookEngine(unittest.TestCase):
    def setUp(self):
        self.engine = AudiobookEngine()

    def test_chapter_extraction_epub(self):
        chapters = self.engine.extract_chapters('test_data/sample.epub')
        self.assertGreater(len(chapters), 0)

    def test_cost_calculation(self):
        chapters = [('Ch1', 'a' * 100000, 1, 'Chapter 1')]
        cost = self.engine.estimate_cost(chapters, 'Chirp3-HD')
        self.assertGreater(cost['estimated_cost'], 0)
```

### 7.2 Integration Tests
```python
# tests/test_gui.py
import pytest
from PySide6.QtWidgets import QApplication
from gui.main_window import MainWindow

@pytest.fixture
def app(qtbot):
    test_app = QApplication.instance() or QApplication([])
    window = MainWindow()
    qtbot.addWidget(window)
    return window

def test_file_upload(app, qtbot):
    # Simulate file drop
    app.file_uploader.file_dropped.emit('test_data/sample.epub')
    # Verify chapters loaded
    assert app.chapter_list.list_widget.count() > 0
```

---

## Phase 8: Deployment & Distribution (1-2 days)

### 8.1 Create DMG Installer
```bash
# create_dmg.sh
#!/bin/bash

# Build the app
python setup.py py2app

# Create DMG with custom background
hdiutil create -volname "Audiobook Generator" \
  -srcfolder dist/AudiobookGenerator.app \
  -ov -format UDRW \
  temp.dmg

# Mount and customize
hdiutil attach temp.dmg
# Add Applications symlink, background image, etc.
hdiutil detach /Volumes/Audiobook\ Generator

# Convert to compressed DMG
hdiutil convert temp.dmg -format UDZO \
  -o AudiobookGenerator-v1.0.0.dmg

rm temp.dmg
```

### 8.2 Auto-Update System (Optional)
Use **Sparkle** framework for automatic updates:
```python
# Add to setup.py OPTIONS
'frameworks': ['Sparkle.framework'],
```

---

## Complete Implementation Checklist

### ✅ Pre-Development
- [ ] Decide on GUI framework (Recommend: PySide6)
- [ ] Set up development environment
- [ ] Create new git branch for GUI development
- [ ] Review macOS Human Interface Guidelines

### ✅ Phase 1: Refactoring (2-3 days)
- [ ] Create `core/` module structure
- [ ] Extract business logic to `core/engine.py`
- [ ] Remove all `print()` from core logic
- [ ] Implement callback-based progress reporting
- [ ] Create threading/async wrapper
- [ ] Write unit tests for core functions

### ✅ Phase 2: GUI Development (3-4 days)
- [ ] Install PySide6
- [ ] Create main window layout
- [ ] Implement file upload widget (drag-and-drop)
- [ ] Implement voice selector widget
- [ ] Implement chapter list widget
- [ ] Implement progress dialog
- [ ] Implement settings/preferences window
- [ ] Wire up all signals/slots

### ✅ Phase 3: Features (2-3 days)
- [ ] Add cost estimator display
- [ ] Implement voice preview feature
- [ ] Add batch processing queue
- [ ] Implement pause/resume functionality
- [ ] Add notification system
- [ ] Create menu bar
- [ ] Add keyboard shortcuts

### ✅ Phase 4: macOS Integration (2-3 days)
- [ ] Create app icon (.icns)
- [ ] Configure Info.plist
- [ ] Set up file associations (EPUB, DOCX)
- [ ] Implement dark mode support
- [ ] Add native notifications
- [ ] Create preferences storage (QSettings)
- [ ] Test on different macOS versions

### ✅ Phase 5: Packaging (1-2 days)
- [ ] Create setup.py for py2app
- [ ] Build .app bundle
- [ ] Get Apple Developer certificate
- [ ] Code sign the application
- [ ] Notarize the application
- [ ] Create DMG installer
- [ ] Test installation on clean macOS system

### ✅ Phase 6: Polish (1-2 days)
- [ ] Error handling and user-friendly messages
- [ ] Input validation
- [ ] Help documentation
- [ ] About dialog
- [ ] First-run tutorial/wizard
- [ ] Beta testing with users

### ✅ Phase 7: Release
- [ ] Write user manual
- [ ] Create release notes
- [ ] Upload to distribution platform (website, GitHub releases)
- [ ] Market the application

---

## Estimated Timeline

| Phase | Duration | Cumulative |
|-------|----------|------------|
| Architecture refactoring | 2-3 days | 2-3 days |
| GUI framework setup | 1 day | 3-4 days |
| Core GUI components | 3-4 days | 6-8 days |
| macOS integration | 2-3 days | 8-11 days |
| Configuration system | 1 day | 9-12 days |
| Enhanced features | 2-3 days | 11-15 days |
| Testing & debugging | 2-3 days | 13-18 days |
| Packaging & distribution | 1-2 days | 14-20 days |
| **Total** | **~3-4 weeks** | |

---

## Development Resources

### GUI Design
- [macOS Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/macos)
- [PySide6 Documentation](https://doc.qt.io/qtforpython/)
- [Qt Designer](https://doc.qt.io/qt-6/qtdesigner-manual.html) - Visual UI design tool

### Packaging
- [py2app Documentation](https://py2app.readthedocs.io/)
- [Code Signing Guide](https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution)
- [DMG Canvas](https://www.araelium.com/dmgcanvas) - Create beautiful DMG installers

### Icons & Assets
- [SF Symbols](https://developer.apple.com/sf-symbols/) - macOS system icons
- [Icon Slate](https://www.kodlian.com/apps/icon-slate) - Create .icns files

---

## Alternative Approaches

### Option 1: Electron + Python Backend (Web-based UI)
**Pros**: Modern UI, cross-platform, familiar web technologies
**Cons**: Large bundle size (~200MB), slower startup
**Time**: +1 week for web UI development

### Option 2: Web App (Django/Flask + React)
**Pros**: No installation, accessible anywhere, automatic updates
**Cons**: Requires server hosting, credentials security concerns
**Time**: +2-3 weeks for full web stack

### Option 3: SwiftUI + Python Bridge
**Pros**: True native macOS app, best performance
**Cons**: Swift learning curve, can't reuse Python GUI code
**Time**: +3-4 weeks (full rewrite)

---

## Recommended Approach

**Start with PySide6 desktop app** because:
1. ✅ Reuses existing Python codebase
2. ✅ Native macOS look and feel
3. ✅ No server hosting required
4. ✅ Credentials stay local (secure)
5. ✅ Reasonable development time (3-4 weeks)
6. ✅ Can create Windows/Linux versions later

---

## Next Steps

1. **Prototype**: Build a simple PySide6 window with file upload to validate approach
2. **Refactor**: Extract core logic from CLI script
3. **Iterate**: Build GUI components one by one
4. **Test**: Continuous testing on macOS
5. **Package**: Create distributable .dmg
6. **Launch**: Release to users

Would you like me to:
- Create the initial project structure?
- Build a PySide6 prototype?
- Start refactoring the core engine?
- Something else?
