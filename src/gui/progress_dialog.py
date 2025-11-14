"""
Progress dialog for audiobook conversion
Shows real-time progress during conversion
"""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QProgressBar,
                               QPushButton, QHBoxLayout, QListWidget,
                               QListWidgetItem, QTextEdit)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont
import time


class ProgressDialog(QDialog):
    """Dialog showing conversion progress"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Generating Audiobook...")
        self.setModal(True)
        self.setMinimumSize(600, 500)

        self.setup_ui()

        # Track state
        self.is_cancelled = False
        self.is_paused = False

    def setup_ui(self):
        """Set up the user interface"""
        layout = QVBoxLayout()

        # Current chapter label
        self.current_chapter_label = QLabel("Preparing...")
        self.current_chapter_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self.current_chapter_label)

        # Overall progress bar
        overall_layout = QHBoxLayout()
        overall_layout.addWidget(QLabel("Overall Progress:"))
        self.overall_progress = QProgressBar()
        self.overall_progress.setMinimum(0)
        self.overall_progress.setMaximum(100)
        overall_layout.addWidget(self.overall_progress)
        self.overall_percent_label = QLabel("0%")
        self.overall_percent_label.setMinimumWidth(40)
        overall_layout.addWidget(self.overall_percent_label)
        layout.addLayout(overall_layout)

        # Current chapter progress bar
        chapter_layout = QHBoxLayout()
        chapter_layout.addWidget(QLabel("Current Chapter:"))
        self.chapter_progress = QProgressBar()
        self.chapter_progress.setMinimum(0)
        self.chapter_progress.setMaximum(100)
        chapter_layout.addWidget(self.chapter_progress)
        self.chapter_percent_label = QLabel("0%")
        self.chapter_percent_label.setMinimumWidth(40)
        chapter_layout.addWidget(self.chapter_percent_label)
        layout.addLayout(chapter_layout)

        # Status label
        self.status_label = QLabel("Status: Initializing...")
        self.status_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.status_label)

        # Time info
        time_layout = QHBoxLayout()
        self.time_elapsed_label = QLabel("Time elapsed: 0:00")
        time_layout.addWidget(self.time_elapsed_label)
        time_layout.addStretch()
        self.time_remaining_label = QLabel("Est. remaining: --")
        time_layout.addWidget(self.time_remaining_label)
        layout.addLayout(time_layout)

        # Chapter list
        list_label = QLabel("Chapters:")
        list_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(list_label)

        self.chapter_list = QListWidget()
        self.chapter_list.setMaximumHeight(150)
        layout.addWidget(self.chapter_list)

        # Log output (collapsible)
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(100)
        self.log_output.setStyleSheet("font-family: monospace; font-size: 10px;")
        self.log_output.setVisible(False)
        layout.addWidget(self.log_output)

        show_log_btn = QPushButton("Show Details")
        show_log_btn.setCheckable(True)
        show_log_btn.toggled.connect(self.toggle_log)
        layout.addWidget(show_log_btn)

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # self.pause_btn = QPushButton("❚❚ Pause")
        # self.pause_btn.clicked.connect(self.pause_conversion)
        # self.pause_btn.setEnabled(False)
        # button_layout.addWidget(self.pause_btn)

        self.cancel_btn = QPushButton("■ Cancel")
        self.cancel_btn.clicked.connect(self.cancel_conversion)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Timing
        self.start_time = None
        self.chapter_times = []

    def toggle_log(self, show):
        """Toggle log visibility"""
        self.log_output.setVisible(show)
        if show:
            self.resize(self.width(), self.height() + 100)
        else:
            self.resize(self.width(), self.height() - 100)

    def start_conversion(self, chapter_titles):
        """
        Initialize progress tracking

        Args:
            chapter_titles: List of chapter title strings
        """
        self.start_time = time.time()
        self.total_chapters = len(chapter_titles)
        self.completed_chapters = 0
        self.chapter_times = []

        # Populate chapter list
        self.chapter_list.clear()
        for i, title in enumerate(chapter_titles):
            item = QListWidgetItem(f"⏳ {title}")
            item.setData(Qt.UserRole, "pending")
            self.chapter_list.addItem(item)

        self.overall_progress.setMaximum(self.total_chapters)
        self.overall_progress.setValue(0)
        self.overall_percent_label.setText("0%")

        self.is_cancelled = False
        self.is_paused = False

    def update_progress(self, chapter_idx, total, status, progress, message):
        """
        Update progress

        Args:
            chapter_idx: Current chapter index
            total: Total chapters
            status: Status string ("starting", "uploading", "processing", "downloading", "completed", "failed")
            progress: Progress percentage (0-100)
            message: Status message
        """
        # Update current chapter
        self.current_chapter_label.setText(f"Chapter {chapter_idx + 1} of {total}")

        # Update chapter progress
        self.chapter_progress.setValue(int(progress))
        self.chapter_percent_label.setText(f"{int(progress)}%")

        # Update status
        status_icons = {
            "starting": "🔄",
            "uploading": "⬆️",
            "processing": "⚙️",
            "downloading": "⬇️",
            "completed": "✅",
            "failed": "❌"
        }
        icon = status_icons.get(status, "•")
        self.status_label.setText(f"Status: {icon} {message}")

        # Update chapter list item
        if chapter_idx < self.chapter_list.count():
            item = self.chapter_list.item(chapter_idx)
            if status == "completed":
                item.setText(f"✅ {item.text()[2:]}")
                item.setData(Qt.UserRole, "completed")
                self.chapter_list.scrollToItem(item)
                self.completed_chapters += 1

                # Track timing
                chapter_time = time.time()
                self.chapter_times.append(chapter_time)

            elif status == "failed":
                item.setText(f"❌ {item.text()[2:]}")
                item.setData(Qt.UserRole, "failed")
                self.chapter_list.scrollToItem(item)

            elif status == "starting":
                item.setText(f"🔄 {item.text()[2:]}")
                item.setData(Qt.UserRole, "in_progress")
                self.chapter_list.scrollToItem(item)

        # Update overall progress
        overall = int((self.completed_chapters / total) * 100)
        self.overall_progress.setValue(self.completed_chapters)
        self.overall_percent_label.setText(f"{overall}%")

        # Update time estimates
        self.update_time_estimates()

        # Log message
        self.log_output.append(f"[{time.strftime('%H:%M:%S')}] {message}")

    def update_time_estimates(self):
        """Update elapsed and remaining time"""
        if not self.start_time:
            return

        elapsed = time.time() - self.start_time
        elapsed_str = self.format_time(elapsed)
        self.time_elapsed_label.setText(f"Time elapsed: {elapsed_str}")

        # Estimate remaining
        if self.completed_chapters > 0:
            avg_time_per_chapter = elapsed / self.completed_chapters
            remaining_chapters = self.total_chapters - self.completed_chapters
            estimated_remaining = avg_time_per_chapter * remaining_chapters
            remaining_str = self.format_time(estimated_remaining)
            self.time_remaining_label.setText(f"Est. remaining: {remaining_str}")

    @staticmethod
    def format_time(seconds):
        """Format seconds to human-readable time"""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours}h {minutes}m"

    def pause_conversion(self):
        """Pause the conversion"""
        if not self.is_paused:
            self.is_paused = True
            self.pause_btn.setText("▶️ Resume")
            self.status_label.setText("Status: ⏸️ Paused")
        else:
            self.is_paused = False
            self.pause_btn.setText("❚❚ Pause")

    def cancel_conversion(self):
        """Cancel the conversion"""
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self,
            "Cancel Conversion",
            "Are you sure you want to cancel the conversion?\n\n"
            "Progress will be lost for incomplete chapters.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.is_cancelled = True
            self.status_label.setText("Status: ❌ Cancelling...")
            self.cancel_btn.setEnabled(False)
            # The conversion thread should check self.is_cancelled periodically

    def conversion_complete(self, successful, failed):
        """
        Called when conversion finishes

        Args:
            successful: Number of successful chapters
            failed: Number of failed chapters
        """
        total_time = time.time() - self.start_time
        time_str = self.format_time(total_time)

        if failed == 0:
            self.status_label.setText(f"Status: ✅ Complete! ({successful}/{self.total_chapters} chapters in {time_str})")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.status_label.setText(f"Status: ⚠️ Partial success: {successful} succeeded, {failed} failed ({time_str})")
            self.status_label.setStyleSheet("color: orange; font-weight: bold;")

        self.cancel_btn.setText("Close")
        self.cancel_btn.setEnabled(True)
        self.cancel_btn.clicked.disconnect()
        self.cancel_btn.clicked.connect(self.accept)


class ConversionThread(QThread):
    """Thread for running conversion in background"""

    # Signals
    progress = Signal(int, int, str, int, str)  # chapter_idx, total, status, progress, message
    finished = Signal(int, int)  # successful, failed
    error = Signal(str)

    def __init__(self, engine, chapters, selected_indices, output_base_name, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.chapters = chapters
        self.selected_indices = selected_indices
        self.output_base_name = output_base_name
        self.should_cancel = False

    def run(self):
        """Run the conversion"""
        try:
            successful = 0
            failed = 0

            def progress_callback(chapter_idx, total, status, progress_val, message):
                """Callback for progress updates"""
                if self.should_cancel:
                    raise InterruptedError("Conversion cancelled by user")
                self.progress.emit(chapter_idx, total, status, progress_val, message)

            # Run conversion
            results = self.engine.convert_chapters(
                chapters=self.chapters,
                selected_indices=self.selected_indices,
                output_base_name=self.output_base_name,
                progress_callback=progress_callback
            )

            successful = len(results)
            failed = len(self.selected_indices) - successful

            self.finished.emit(successful, failed)

        except InterruptedError as e:
            self.error.emit(str(e))
        except Exception as e:
            self.error.emit(f"Conversion error: {str(e)}")

    def cancel(self):
        """Request cancellation"""
        self.should_cancel = True
