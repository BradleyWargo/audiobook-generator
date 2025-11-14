"""
Chapter list widget for selecting which chapters to convert
"""
from PySide6.QtWidgets import (QWidget, QListWidget, QListWidgetItem, QPushButton,
                               QVBoxLayout, QHBoxLayout, QGroupBox, QLabel)
from PySide6.QtCore import Qt, Signal


class ChapterList(QWidget):
    """Widget for displaying and selecting chapters"""

    selection_changed = Signal(list)  # Emits list of selected chapter indices

    def __init__(self, parent=None):
        super().__init__(parent)
        self.chapters = []
        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface"""
        layout = QVBoxLayout()

        # Create group box
        group = QGroupBox("📚 Chapters")
        group_layout = QVBoxLayout()

        # Chapter count label
        self.count_label = QLabel("No chapters loaded")
        self.count_label.setStyleSheet("color: #666; font-size: 11px;")
        group_layout.addWidget(self.count_label)

        # List widget
        self.list_widget = QListWidget()
        self.list_widget.setMinimumHeight(200)
        self.list_widget.itemChanged.connect(self.on_item_changed)
        group_layout.addWidget(self.list_widget)

        # Button row
        btn_layout = QHBoxLayout()
        self.select_all_btn = QPushButton("☑ Select All")
        self.select_all_btn.clicked.connect(self.select_all)
        self.select_all_btn.setEnabled(False)

        self.deselect_all_btn = QPushButton("☐ Deselect All")
        self.deselect_all_btn.clicked.connect(self.deselect_all)
        self.deselect_all_btn.setEnabled(False)

        btn_layout.addWidget(self.select_all_btn)
        btn_layout.addWidget(self.deselect_all_btn)
        group_layout.addLayout(btn_layout)

        group.setLayout(group_layout)
        layout.addWidget(group)
        self.setLayout(layout)

    def load_chapters(self, chapters):
        """
        Load chapters into the list
        chapters: list of (title, text, chapter_num, original_title) tuples
        """
        self.chapters = chapters
        self.list_widget.clear()

        for i, (title, text, chapter_num, original_title) in enumerate(chapters):
            word_count = len(text.split()) if text else 0
            item_text = f"{original_title} ({word_count:,} words)"

            item = QListWidgetItem(item_text)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)  # Default: all selected
            item.setData(Qt.UserRole, i)  # Store index
            self.list_widget.addItem(item)

        # Update count label
        total_words = sum(len(text.split()) if text else 0 for _, text, _, _ in chapters)
        self.count_label.setText(
            f"{len(chapters)} chapters found • {total_words:,} total words"
        )

        # Enable buttons
        self.select_all_btn.setEnabled(True)
        self.deselect_all_btn.setEnabled(True)

        # Emit initial selection
        self.on_item_changed()

    def get_selected_indices(self):
        """Get list of selected chapter indices"""
        selected = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.Checked:
                selected.append(item.data(Qt.UserRole))
        return selected

    def get_selected_chapters(self):
        """Get list of selected chapter data"""
        selected_indices = self.get_selected_indices()
        return [self.chapters[i] for i in selected_indices]

    def select_all(self):
        """Select all chapters"""
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setCheckState(Qt.Checked)

    def deselect_all(self):
        """Deselect all chapters"""
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setCheckState(Qt.Unchecked)

    def on_item_changed(self):
        """Handle item check state change"""
        selected = self.get_selected_indices()
        self.selection_changed.emit(selected)

    def clear(self):
        """Clear the chapter list"""
        self.chapters = []
        self.list_widget.clear()
        self.count_label.setText("No chapters loaded")
        self.select_all_btn.setEnabled(False)
        self.deselect_all_btn.setEnabled(False)
