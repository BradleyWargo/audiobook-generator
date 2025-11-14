#!/usr/bin/env python3
"""
Audiobook Generator - Mac App (Prototype)
Main entry point for the GUI application
"""
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt

from gui.main_window import MainWindow


def main():
    """Main application entry point"""
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Audiobook Generator")
    app.setOrganizationName("AudiobookGenerator")
    app.setApplicationVersion("0.1.0")

    # Set application style
    app.setStyle("Fusion")  # Modern cross-platform style

    # Create and show main window
    window = MainWindow()
    window.show()

    # Run application event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
