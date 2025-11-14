"""
File uploader widget with drag-and-drop support
"""
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QFileDialog, QHBoxLayout
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QPalette
from pathlib import Path


class FileUploader(QWidget):
    """Drag-and-drop file upload widget"""

    file_selected = Signal(str)  # Emits file path when file is selected

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_file = None
        self.setup_ui()
        self.apply_styles()

    def setup_ui(self):
        """Set up the user interface"""
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)

        # Drop zone label
        self.drop_label = QLabel("📖 Drop EPUB or DOCX file here\nor click to browse")
        self.drop_label.setAlignment(Qt.AlignCenter)
        self.drop_label.setMinimumHeight(150)

        # File info label (hidden initially)
        self.file_info_label = QLabel()
        self.file_info_label.setAlignment(Qt.AlignCenter)
        self.file_info_label.setVisible(False)

        layout.addWidget(self.drop_label)
        layout.addWidget(self.file_info_label)

        self.setLayout(layout)
        self.setAcceptDrops(True)

    def apply_styles(self):
        """Apply styling to the widget"""
        self.setStyleSheet("""
            FileUploader {
                border: 2px dashed #999;
                border-radius: 10px;
                background-color: #f5f5f5;
            }
            FileUploader:hover {
                border-color: #0066cc;
                background-color: #e8f4ff;
            }
            QLabel {
                font-size: 14px;
                color: #666;
            }
        """)

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and self.is_valid_file(urls[0].toLocalFile()):
                event.acceptProposedAction()
                self.setStyleSheet("""
                    FileUploader {
                        border: 2px solid #0066cc;
                        border-radius: 10px;
                        background-color: #d4e9ff;
                    }
                """)

    def dragLeaveEvent(self, event):
        """Handle drag leave event"""
        self.apply_styles()

    def dropEvent(self, event: QDropEvent):
        """Handle file drop event"""
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files and self.is_valid_file(files[0]):
            self.set_file(files[0])
        self.apply_styles()

    def mousePressEvent(self, event):
        """Handle mouse click to open file dialog"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Ebook File",
            str(Path.home()),
            "Ebook Files (*.epub *.docx);;EPUB Files (*.epub);;Word Documents (*.docx)"
        )
        if file_path:
            self.set_file(file_path)

    def is_valid_file(self, file_path: str) -> bool:
        """Check if file is a valid ebook format"""
        return file_path.lower().endswith(('.epub', '.docx'))

    def set_file(self, file_path: str):
        """Set the selected file and update UI"""
        if not self.is_valid_file(file_path):
            return

        self.current_file = file_path
        file_name = Path(file_path).name
        file_size = Path(file_path).stat().st_size
        file_size_mb = file_size / (1024 * 1024)

        # Update UI to show selected file
        self.drop_label.setText(f"✅ {file_name}")
        self.file_info_label.setText(f"📊 Size: {file_size_mb:.1f} MB")
        self.file_info_label.setVisible(True)

        # Emit signal
        self.file_selected.emit(file_path)

    def get_file(self) -> str:
        """Get the currently selected file path"""
        return self.current_file

    def clear(self):
        """Clear the selected file"""
        self.current_file = None
        self.drop_label.setText("📖 Drop EPUB or DOCX file here\nor click to browse")
        self.file_info_label.setVisible(False)
