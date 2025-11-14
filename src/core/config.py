"""
Configuration manager for Audiobook Generator
Handles Google Cloud credentials and app preferences
"""
import json
from pathlib import Path
from PySide6.QtCore import QSettings
import os


class ConfigManager:
    """Manages application configuration and Google Cloud credentials"""

    def __init__(self):
        # Use Qt's QSettings for platform-appropriate storage
        # macOS: ~/Library/Preferences/com.audiobookgenerator.plist
        self.settings = QSettings('com.audiobookgenerator', 'AudiobookGenerator')

        # Project directories
        self.project_dir = Path(__file__).parent.parent.parent
        self.credentials_dir = self.project_dir / "credentials"
        self.output_dir = self.project_dir / "output"
        self.input_dir = self.project_dir / "input"

        # Ensure directories exist
        for directory in [self.credentials_dir, self.output_dir, self.input_dir]:
            directory.mkdir(exist_ok=True)

    # Google Cloud Settings
    def get_project_id(self):
        """Get Google Cloud project ID"""
        return self.settings.value('google_cloud/project_id', '')

    def set_project_id(self, project_id: str):
        """Set Google Cloud project ID"""
        self.settings.setValue('google_cloud/project_id', project_id)

    def get_bucket_name(self):
        """Get Google Cloud Storage bucket name"""
        return self.settings.value('google_cloud/bucket_name', '')

    def set_bucket_name(self, bucket_name: str):
        """Set Google Cloud Storage bucket name"""
        self.settings.setValue('google_cloud/bucket_name', bucket_name)

    def get_credentials_path(self):
        """Get path to service account credentials file"""
        saved_path = self.settings.value('google_cloud/credentials_path', '')
        if saved_path and Path(saved_path).exists():
            return saved_path

        # Check default location
        default_path = self.credentials_dir / 'audiobook-generator-tts-service-account.json'
        if default_path.exists():
            return str(default_path)

        return ''

    def set_credentials_path(self, path: str):
        """Set path to service account credentials file"""
        self.settings.setValue('google_cloud/credentials_path', path)
        # Also set environment variable
        if path:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = path

    def get_location(self):
        """Get Google Cloud location"""
        return self.settings.value('google_cloud/location', 'global')

    def set_location(self, location: str):
        """Set Google Cloud location"""
        self.settings.setValue('google_cloud/location', location)

    def is_google_cloud_configured(self):
        """Check if Google Cloud is properly configured"""
        return (
            bool(self.get_project_id()) and
            bool(self.get_bucket_name()) and
            bool(self.get_credentials_path()) and
            Path(self.get_credentials_path()).exists()
        )

    # Voice Settings
    def get_voice_language(self):
        """Get selected voice language code"""
        return self.settings.value('voice/language_code', 'en-GB')

    def set_voice_language(self, language_code: str):
        """Set voice language code"""
        self.settings.setValue('voice/language_code', language_code)

    def get_voice_name(self):
        """Get selected voice name"""
        return self.settings.value('voice/name', 'en-GB-Chirp3-HD-Despina')

    def set_voice_name(self, voice_name: str):
        """Set voice name"""
        self.settings.setValue('voice/name', voice_name)

    def get_favorite_voices(self):
        """Get list of favorite voices"""
        favorites = self.settings.value('voice/favorites', [])
        return favorites if isinstance(favorites, list) else []

    def add_favorite_voice(self, language_code: str, voice_name: str):
        """Add a voice to favorites"""
        favorites = self.get_favorite_voices()
        voice_id = f"{language_code}:{voice_name}"
        if voice_id not in favorites:
            favorites.append(voice_id)
            self.settings.setValue('voice/favorites', favorites)

    def remove_favorite_voice(self, language_code: str, voice_name: str):
        """Remove a voice from favorites"""
        favorites = self.get_favorite_voices()
        voice_id = f"{language_code}:{voice_name}"
        if voice_id in favorites:
            favorites.remove(voice_id)
            self.settings.setValue('voice/favorites', favorites)

    # Output Settings
    def get_output_directory(self):
        """Get output directory path"""
        default = str(self.output_dir)
        return self.settings.value('output/directory', default)

    def set_output_directory(self, path: str):
        """Set output directory path"""
        self.settings.setValue('output/directory', path)

    def get_output_base_name(self):
        """Get output file base name"""
        return self.settings.value('output/base_name', 'audiobook')

    def set_output_base_name(self, name: str):
        """Set output file base name"""
        self.settings.setValue('output/base_name', name)

    def get_use_book_title(self):
        """Check if should use book title as base name"""
        return self.settings.value('output/use_book_title', True, type=bool)

    def set_use_book_title(self, use_title: bool):
        """Set whether to use book title as base name"""
        self.settings.setValue('output/use_book_title', use_title)

    def get_number_chapters(self):
        """Check if should number chapters sequentially"""
        return self.settings.value('output/number_chapters', True, type=bool)

    def set_number_chapters(self, number: bool):
        """Set whether to number chapters"""
        self.settings.setValue('output/number_chapters', number)

    # Processing Settings
    def get_max_sentence_length(self):
        """Get maximum sentence length"""
        return self.settings.value('processing/max_sentence_length', 200, type=int)

    def set_max_sentence_length(self, length: int):
        """Set maximum sentence length"""
        self.settings.setValue('processing/max_sentence_length', length)

    def get_max_chunk_length(self):
        """Get maximum chunk length for splitting"""
        return self.settings.value('processing/max_chunk_length', 180, type=int)

    def set_max_chunk_length(self, length: int):
        """Set maximum chunk length"""
        self.settings.setValue('processing/max_chunk_length', length)

    def get_retry_attempts(self):
        """Get number of retry attempts"""
        return self.settings.value('processing/retry_attempts', 3, type=int)

    def set_retry_attempts(self, attempts: int):
        """Set retry attempts"""
        self.settings.setValue('processing/retry_attempts', attempts)

    def get_auto_cleanup_gcs(self):
        """Check if should auto-cleanup GCS files"""
        return self.settings.value('processing/auto_cleanup_gcs', True, type=bool)

    def set_auto_cleanup_gcs(self, cleanup: bool):
        """Set auto-cleanup GCS files"""
        self.settings.setValue('processing/auto_cleanup_gcs', cleanup)

    # UI Settings
    def get_show_setup_wizard_on_start(self):
        """Check if should show setup wizard on start"""
        return self.settings.value('ui/show_setup_wizard', True, type=bool)

    def set_show_setup_wizard_on_start(self, show: bool):
        """Set whether to show setup wizard on start"""
        self.settings.setValue('ui/show_setup_wizard', show)

    def get_window_geometry(self):
        """Get saved window geometry"""
        return self.settings.value('ui/window_geometry', None)

    def set_window_geometry(self, geometry):
        """Save window geometry"""
        self.settings.setValue('ui/window_geometry', geometry)

    def get_last_input_directory(self):
        """Get last used input directory"""
        default = str(self.input_dir)
        return self.settings.value('ui/last_input_directory', default)

    def set_last_input_directory(self, path: str):
        """Set last used input directory"""
        self.settings.setValue('ui/last_input_directory', path)

    # Helper Methods
    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        self.settings.clear()

    def export_settings(self, file_path: str):
        """Export settings to JSON file"""
        settings_dict = {}
        for key in self.settings.allKeys():
            settings_dict[key] = self.settings.value(key)

        with open(file_path, 'w') as f:
            json.dump(settings_dict, f, indent=2)

    def import_settings(self, file_path: str):
        """Import settings from JSON file"""
        with open(file_path, 'r') as f:
            settings_dict = json.load(f)

        for key, value in settings_dict.items():
            self.settings.setValue(key, value)

    def get_all_settings(self):
        """Get all settings as dictionary"""
        return {key: self.settings.value(key) for key in self.settings.allKeys()}
