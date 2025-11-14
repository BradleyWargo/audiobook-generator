"""
Main audiobook conversion engine
Orchestrates parsing, TTS, and file management
"""
import logging
from pathlib import Path
from .parser import EbookParser
from .tts_client import TTSClient
from .config import ConfigManager

logger = logging.getLogger(__name__)


class AudiobookEngine:
    """Main engine for audiobook conversion"""

    def __init__(self, config_manager=None):
        """
        Initialize the audiobook engine

        Args:
            config_manager: Optional ConfigManager instance
        """
        self.config = config_manager or ConfigManager()
        self.parser = EbookParser(
            max_sentence_length=self.config.get_max_sentence_length(),
            max_chunk_length=self.config.get_max_chunk_length()
        )
        self.tts_client = None

    def initialize_tts(self):
        """
        Initialize Google Cloud TTS client
        Returns (success, message)
        """
        if not self.config.is_google_cloud_configured():
            return False, "Google Cloud is not configured. Please run setup wizard."

        try:
            self.tts_client = TTSClient(
                project_id=self.config.get_project_id(),
                bucket_name=self.config.get_bucket_name(),
                location=self.config.get_location(),
                retry_attempts=self.config.get_retry_attempts()
            )

            # Set credentials environment variable
            self.config.set_credentials_path(self.config.get_credentials_path())

            # Initialize clients
            success = self.tts_client.initialize()
            if not success:
                return False, "Failed to initialize Google Cloud clients"

            return True, "Google Cloud initialized successfully"

        except Exception as e:
            logger.error(f"Failed to initialize TTS: {e}")
            return False, f"Initialization failed: {str(e)}"

    def test_google_cloud_connection(self):
        """
        Test connection to Google Cloud
        Returns (success, message)
        """
        try:
            # Initialize if not already done
            if not self.tts_client:
                success, msg = self.initialize_tts()
                if not success:
                    return False, msg

            # Test connection
            return self.tts_client.test_connection()

        except Exception as e:
            return False, f"Connection test failed: {str(e)}"

    def extract_chapters(self, file_path, heading_style='Heading 1'):
        """
        Extract chapters from an ebook file

        Args:
            file_path: Path to ebook file
            heading_style: Heading style for DOCX files

        Returns:
            List of (title, text, chapter_num, original_title) tuples

        Raises:
            ValueError: If file type is unsupported or no chapters found
        """
        try:
            chapters = list(self.parser.extract_chapters(file_path, heading_style))
            logger.info(f"Extracted {len(chapters)} chapters from {file_path}")
            return chapters
        except Exception as e:
            logger.error(f"Failed to extract chapters: {e}")
            raise

    def process_chapters(self, chapters):
        """
        Process chapter text for TTS conversion

        Args:
            chapters: List of (title, text, chapter_num, original_title) tuples

        Returns:
            List of processed chapters
        """
        processed = []
        for title, text, chapter_num, original_title in chapters:
            processed_text = self.parser.process_text(text)
            processed.append((title, processed_text, chapter_num, original_title))

        return processed

    def estimate_cost(self, chapters, voice_name=None):
        """
        Estimate cost and duration for converting chapters

        Args:
            chapters: List of chapter tuples
            voice_name: Voice name (or use configured voice)

        Returns:
            Dict with cost estimate details
        """
        if voice_name is None:
            voice_name = self.config.get_voice_name()

        return self.parser.estimate_cost(chapters, voice_name)

    def convert_chapters(self, chapters, selected_indices=None,
                        output_base_name=None, progress_callback=None):
        """
        Convert selected chapters to audiobook

        Args:
            chapters: List of all chapter tuples
            selected_indices: List of indices to convert (or None for all)
            output_base_name: Base name for output files
            progress_callback: Optional callback(chapter_idx, total, status, progress, message)

        Returns:
            List of (local_file_path, chapter_info) tuples for successful conversions
        """
        # Initialize TTS if needed
        if not self.tts_client:
            success, msg = self.initialize_tts()
            if not success:
                raise RuntimeError(f"Failed to initialize TTS: {msg}")

        # Determine which chapters to convert
        if selected_indices is None:
            selected_indices = list(range(len(chapters)))

        if not selected_indices:
            return []

        # Get voice settings
        voice_language = self.config.get_voice_language()
        voice_name = self.config.get_voice_name()

        # Get output settings
        output_dir = Path(self.config.get_output_directory())
        output_dir.mkdir(parents=True, exist_ok=True)

        if output_base_name is None:
            output_base_name = self.config.get_output_base_name()

        # Process chapters
        successful_files = []
        total_chapters = len(selected_indices)

        for processing_order, chapter_idx in enumerate(selected_indices, 1):
            title, text, chapter_num, original_title = chapters[chapter_idx]

            logger.info(f"Converting chapter {processing_order}/{total_chapters}: {original_title}")

            # Update progress
            if progress_callback:
                progress_callback(
                    processing_order - 1,
                    total_chapters,
                    "starting",
                    0,
                    f"Starting '{original_title}'..."
                )

            # Generate filename
            if self.config.get_number_chapters():
                output_filename = f"{output_base_name}_{processing_order:03d}"
            else:
                safe_title = self.parser.sanitize_filename(original_title)
                output_filename = f"{output_base_name}_{safe_title}"

            # Create progress callback for this chapter
            def chapter_progress(status, progress, message):
                if progress_callback:
                    progress_callback(
                        processing_order - 1,
                        total_chapters,
                        status,
                        progress,
                        message
                    )

            # Synthesize chapter
            gcs_uri, final_filename = self.tts_client.synthesize_chapter(
                chapter_title=title,
                chapter_text=text,
                chapter_number=chapter_num,
                original_title=original_title,
                voice_name=voice_name,
                voice_language_code=voice_language,
                output_filename=output_filename,
                progress_callback=chapter_progress
            )

            if not gcs_uri:
                logger.error(f"Failed to synthesize chapter: {original_title}")
                if progress_callback:
                    progress_callback(
                        processing_order - 1,
                        total_chapters,
                        "failed",
                        0,
                        f"Failed to synthesize '{original_title}'"
                    )
                continue

            # Download from GCS
            local_file = self.tts_client.download_from_gcs(
                gcs_uri,
                output_dir,
                final_filename,
                progress_callback=chapter_progress
            )

            if local_file:
                successful_files.append((local_file, {
                    'title': original_title,
                    'chapter_num': chapter_num,
                    'index': chapter_idx
                }))

                # Cleanup GCS file if configured
                if self.config.get_auto_cleanup_gcs():
                    self.tts_client.cleanup_gcs_file(gcs_uri)

                if progress_callback:
                    progress_callback(
                        processing_order - 1,
                        total_chapters,
                        "completed",
                        100,
                        f"Completed '{original_title}'"
                    )
            else:
                logger.error(f"Failed to download: {original_title}")
                if progress_callback:
                    progress_callback(
                        processing_order - 1,
                        total_chapters,
                        "failed",
                        0,
                        f"Failed to download '{original_title}'"
                    )

        logger.info(f"Conversion complete: {len(successful_files)}/{total_chapters} chapters successful")
        return successful_files

    def get_available_voices(self, language_code=None):
        """Get list of available TTS voices"""
        if not self.tts_client:
            success, msg = self.initialize_tts()
            if not success:
                return []

        return self.tts_client.get_available_voices(language_code)
