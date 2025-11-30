"""
Shotgrid Manager - Application Entry Point

Main entry point for the Shotgrid Manager application.
Initializes the PySide6 application and main window.
"""

import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
import logging

from ui.main_window import MainWindow
from utils.logger import setup_logging


def check_environment():
    """
    Check that required environment variables are set.

    Returns:
        bool: True if environment is configured, False otherwise
    """
    logger = logging.getLogger(__name__)

    required_vars = ['SG_URL', 'SG_SCRIPT_NAME', 'SG_SCRIPT_KEY', 'KUKARI_USER_ID']
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logger.warning(f"Missing environment variables: {', '.join(missing_vars)}")
        logger.warning("Please set the following environment variables:")
        for var in required_vars:
            logger.warning(f"  - {var}")
        return False

    # Validate KUKARI_USER_ID is a number
    user_id = os.getenv('KUKARI_USER_ID')
    try:
        int(user_id)
    except (ValueError, TypeError):
        logger.error(f"KUKARI_USER_ID must be a number, got: {user_id}")
        return False

    # Check WORK_AREA (optional but recommended)
    if not os.getenv('WORK_AREA'):
        logger.warning("WORK_AREA environment variable not set")
        logger.warning("Path building functionality may be limited")

    return True


def setup_application():
    """
    Setup and configure the QApplication.

    Returns:
        QApplication: Configured application instance
    """
    # Create application
    app = QApplication(sys.argv)

    # Set application metadata
    app.setApplicationName("Shotgrid Manager")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Kukari Animation Studio")
    app.setOrganizationDomain("kukari.studio")

    # Set application style
    app.setStyle('Fusion')

    # Enable high DPI support
    app.setAttribute(Qt.AA_UseHighDpiPixmaps)

    return app


def main():
    """
    Main application entry point.

    Returns:
        int: Application exit code
    """
    # Setup logging first
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("=" * 60)
    logger.info("Shotgrid Manager - Starting Application")
    logger.info("=" * 60)

    # Check environment configuration
    if not check_environment():
        logger.error("Environment configuration incomplete")
        logger.error("Application cannot start without Shotgrid credentials")
        # Continue anyway - MainWindow will show proper error dialog
        # return 1

    # Create application
    app = setup_application()
    logger.info(" Application initialized")

    try:
        # Create and show main window
        window = MainWindow()
        window.show()
        logger.info(" Main window created")

        # Run application event loop
        logger.info("Application ready - entering event loop")
        exit_code = app.exec()

        logger.info("=" * 60)
        logger.info(f"Application exiting with code {exit_code}")
        logger.info("=" * 60)

        return exit_code

    except Exception as e:
        logger.exception(f"Fatal error during application startup: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
    