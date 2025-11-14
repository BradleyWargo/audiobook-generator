"""
Google Cloud Text-to-Speech client wrapper
"""
import time
import logging
from pathlib import Path
from google.cloud import texttospeech_v1
from google.cloud.storage import Client as StorageClient
from google.api_core import exceptions as gcp_exceptions

logger = logging.getLogger(__name__)


class TTSClient:
    """Wrapper for Google Cloud Text-to-Speech API"""

    def __init__(self, project_id, bucket_name, location='global',
                 retry_attempts=3, max_timeout=1800):
        """
        Initialize TTS client

        Args:
            project_id: Google Cloud project ID
            bucket_name: Google Cloud Storage bucket name
            location: Google Cloud location (default: 'global')
            retry_attempts: Number of retry attempts for failed requests
            max_timeout: Maximum timeout in seconds for long audio synthesis
        """
        self.project_id = project_id
        self.bucket_name = bucket_name
        self.location = location
        self.retry_attempts = retry_attempts
        self.max_timeout = max_timeout

        self.tts_client = None
        self.storage_client = None

    def initialize(self):
        """Initialize Google Cloud clients"""
        try:
            self.tts_client = texttospeech_v1.TextToSpeechLongAudioSynthesizeClient()
            self.storage_client = StorageClient()
            logger.info("Google Cloud clients initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Google Cloud clients: {e}")
            return False

    def test_connection(self):
        """
        Test connection to Google Cloud
        Returns (success, message)
        """
        try:
            if not self.tts_client:
                self.initialize()

            # Try to list voices as a connection test
            client = texttospeech_v1.TextToSpeechClient()
            client.list_voices()

            logger.info("Google Cloud connection test successful")
            return True, "Connection successful!"
        except gcp_exceptions.PermissionDenied as e:
            msg = "Permission denied. Check your service account permissions."
            logger.error(f"Connection test failed: {msg}")
            return False, msg
        except gcp_exceptions.Unauthenticated as e:
            msg = "Authentication failed. Check your credentials file."
            logger.error(f"Connection test failed: {msg}")
            return False, msg
        except Exception as e:
            msg = f"Connection failed: {str(e)}"
            logger.error(f"Connection test failed: {msg}")
            return False, msg

    def synthesize_chapter(self, chapter_title, chapter_text, chapter_number,
                          original_title, voice_name, voice_language_code,
                          output_filename, progress_callback=None):
        """
        Synthesize a single chapter to audio

        Args:
            chapter_title: Cleaned chapter title
            chapter_text: Chapter text content
            chapter_number: Chapter number (or None)
            original_title: Original chapter title
            voice_name: Google TTS voice name
            voice_language_code: Language code
            output_filename: Base filename for output
            progress_callback: Optional callback(status, progress) for updates

        Returns:
            (gcs_uri, final_filename) on success, (None, None) on failure
        """
        if not chapter_text.strip():
            logger.warning(f"Chapter '{original_title}' has no text content. Skipping.")
            return None, None

        # Generate GCS output URI
        timestamp = int(time.time())
        gcs_output_uri = f"gs://{self.bucket_name}/{output_filename}_{timestamp}.wav"

        logger.info(f"="*60)
        logger.info(f"PROCESSING: '{original_title}'")
        logger.info(f"Output filename: {output_filename}.wav")
        logger.info(f"="*60)

        if progress_callback:
            progress_callback("preparing", 0, f"Processing '{original_title}'...")

        # Create chapter announcement
        if chapter_number is not None:
            chapter_announcement = f"Chapter {chapter_number}. {chapter_title}."
        else:
            chapter_announcement = f"{chapter_title}."

        chapter_text_with_announcement = f"{chapter_announcement}\n\n{chapter_text}"

        # Check text size
        text_bytes = chapter_text_with_announcement.encode('utf-8')
        text_size = len(text_bytes)
        max_size = 900_000  # Slightly under 1MB to be safe

        logger.info(f"Text size: {text_size} bytes ({len(chapter_text_with_announcement)} characters)")

        if text_size > max_size:
            logger.error(f"Chapter '{original_title}' exceeds size limit ({text_size} > {max_size})")
            return None, None

        # Calculate timeout
        base_timeout = 300  # 5 minutes base
        size_timeout = text_size / 500  # 1 second per 500 bytes
        calculated_timeout = min(base_timeout + size_timeout, self.max_timeout)

        logger.info(f"Calculated timeout: {int(calculated_timeout)} seconds")

        # Create request
        parent = f"projects/{self.project_id}/locations/{self.location}"
        request = {
            "parent": parent,
            "input": {"text": chapter_text_with_announcement},
            "voice": {
                "language_code": voice_language_code,
                "name": voice_name
            },
            "audio_config": {
                "audio_encoding": texttospeech_v1.AudioEncoding.LINEAR16
            },
            "output_gcs_uri": gcs_output_uri
        }

        # Retry logic
        for attempt in range(self.retry_attempts):
            try:
                logger.info(f"Attempt {attempt + 1}/{self.retry_attempts}: Starting synthesis...")

                if progress_callback:
                    progress_callback("uploading", 20, f"Uploading to Google Cloud...")

                operation = self.tts_client.synthesize_long_audio(request=request)

                logger.info(f"Waiting for synthesis to complete (timeout: {int(calculated_timeout)}s)...")

                if progress_callback:
                    progress_callback("processing", 40, f"Google is generating audio...")

                result = operation.result(timeout=calculated_timeout)

                if progress_callback:
                    progress_callback("completed", 100, f"Audio generated successfully!")

                logger.info(f"✅ SUCCESS: Synthesis completed for '{original_title}'")
                return gcs_output_uri, output_filename + ".wav"

            except gcp_exceptions.DeadlineExceeded:
                logger.error(f"❌ TIMEOUT: Synthesis timed out (attempt {attempt + 1})")
                if attempt < self.retry_attempts - 1:
                    wait_time = 60 * (attempt + 1)
                    logger.info(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ FINAL FAILURE: All attempts failed due to timeout")
                    if progress_callback:
                        progress_callback("failed", 0, "Synthesis timed out")

            except gcp_exceptions.ResourceExhausted:
                logger.error(f"❌ QUOTA EXCEEDED: API quota exhausted (attempt {attempt + 1})")
                if attempt < self.retry_attempts - 1:
                    wait_time = 300
                    logger.info(f"Waiting {wait_time} seconds for quota reset...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ FINAL FAILURE: Quota limit reached")
                    if progress_callback:
                        progress_callback("failed", 0, "API quota exceeded")

            except gcp_exceptions.InvalidArgument as e:
                logger.error(f"❌ INVALID REQUEST: Bad request: {e}")
                if progress_callback:
                    progress_callback("failed", 0, f"Invalid request: {e}")
                break

            except Exception as e:
                logger.error(f"❌ UNEXPECTED ERROR (attempt {attempt + 1}): {e}")
                if attempt < self.retry_attempts - 1:
                    wait_time = 30 * (attempt + 1)
                    logger.info(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ FINAL FAILURE: All attempts failed")
                    if progress_callback:
                        progress_callback("failed", 0, f"Synthesis failed: {e}")

        return None, None

    def download_from_gcs(self, gcs_uri, local_directory, final_filename,
                         progress_callback=None):
        """
        Download a file from Google Cloud Storage

        Args:
            gcs_uri: GCS URI (gs://bucket/path)
            local_directory: Local directory to save to
            final_filename: Final filename
            progress_callback: Optional callback(status, progress) for updates

        Returns:
            Local file path on success, None on failure
        """
        try:
            if progress_callback:
                progress_callback("downloading", 0, f"Downloading '{final_filename}'...")

            gcs_path = gcs_uri.replace("gs://", "")
            bucket_name = gcs_path.split("/")[0]
            object_name = "/".join(gcs_path.split("/")[1:])

            bucket = self.storage_client.bucket(bucket_name)
            blob = bucket.blob(object_name)

            local_file_path = Path(local_directory) / final_filename

            logger.info(f"Downloading to '{final_filename}'...")
            blob.download_to_filename(str(local_file_path))

            if progress_callback:
                progress_callback("completed", 100, f"Downloaded '{final_filename}'")

            logger.info(f"✅ Downloaded successfully")
            return str(local_file_path)

        except Exception as e:
            logger.error(f"❌ Error downloading from GCS: {e}")
            if progress_callback:
                progress_callback("failed", 0, f"Download failed: {e}")
            return None

    def cleanup_gcs_file(self, gcs_uri):
        """Delete a temporary file from Google Cloud Storage"""
        try:
            gcs_path = gcs_uri.replace("gs://", "")
            bucket_name = gcs_path.split("/")[0]
            object_name = "/".join(gcs_path.split("/")[1:])

            bucket = self.storage_client.bucket(bucket_name)
            blob = bucket.blob(object_name)

            blob.delete()
            logger.info(f"✅ Cleaned up temporary file from GCS")
            return True

        except Exception as e:
            logger.warning(f"Could not cleanup GCS file: {e}")
            return False

    def get_available_voices(self, language_code=None):
        """
        Get list of available voices

        Args:
            language_code: Optional language code to filter (e.g., 'en-US')

        Returns:
            List of voice objects
        """
        try:
            client = texttospeech_v1.TextToSpeechClient()
            response = client.list_voices(language_code=language_code)

            voices = []
            for voice in response.voices:
                voices.append({
                    'name': voice.name,
                    'language_codes': voice.language_codes,
                    'ssml_gender': str(voice.ssml_gender),
                })

            return voices

        except Exception as e:
            logger.error(f"Failed to get available voices: {e}")
            return []
