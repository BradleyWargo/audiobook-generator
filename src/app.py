#!/usr/bin/env python3
"""
Audiobook Generator - Mac App
Main entry point for the GUI application
"""
import sys
import logging
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt

from gui.main_window import MainWindow


def setup_logging():
    """Set up application logging"""
    # Get project root directory
    project_dir = Path(__file__).parent.parent
    logs_dir = project_dir / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(logs_dir / 'audiobook_generator.log'),
            logging.StreamHandler()
        ]
    )

    logger = logging.getLogger(__name__)
    logger.info("="*60)
    logger.info("Audiobook Generator Starting")
    logger.info("="*60)


def main():
    """Main application entry point"""
    # Set up logging
    setup_logging()

    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Audiobook Generator")
    app.setOrganizationName("AudiobookGenerator")
    app.setApplicationVersion("1.0.0")

    # Set application style
    app.setStyle("Fusion")  # Modern cross-platform style

    # Create and show main window
    window = MainWindow()
    window.show()

    # Run application event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
