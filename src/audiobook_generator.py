import os
import re
import time
import logging
from pathlib import Path
from google.cloud import texttospeech_v1
from google.cloud.storage import Client as StorageClient
from google.api_core import exceptions as gcp_exceptions
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from docx import Document
import nltk
from tqdm import tqdm

# --- Project Directory Setup ---
# Get the project root directory (parent of src/)
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent

# Create necessary directories
CREDENTIALS_DIR = PROJECT_DIR / "credentials"
INPUT_DIR = PROJECT_DIR / "input"
OUTPUT_DIR = PROJECT_DIR / "output"
LOGS_DIR = PROJECT_DIR / "logs"

for directory in [CREDENTIALS_DIR, INPUT_DIR, OUTPUT_DIR, LOGS_DIR]:
    directory.mkdir(exist_ok=True)

# --- Enhanced Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / 'audiobook_processing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- Configuration ---

# IMPORTANT: Before running, ensure you have installed the required libraries:
# pip install google-cloud-texttospeech google-cloud-storage ebooklib beautifulsoup4 python-docx nltk

# IMPORTANT: For NLTK sentence tokenization, you need the 'punkt' resource.
# Run this in a Python interpreter ONCE to download it:
# >>> import nltk
# >>> nltk.download('punkt')

# 1. SET THE PATH TO YOUR SERVICE ACCOUNT KEY FILE:
service_account_path = CREDENTIALS_DIR / 'audiobook-generator-tts-service-account.json'
if service_account_path.exists():
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(service_account_path)
    logger.info(f"Using service account: {service_account_path}")
else:
    logger.error(f"Service account not found at: {service_account_path}")
    logger.error("Please place your Google Cloud service account JSON file in the credentials/ directory")

# 2. SET THE PATH TO YOUR BOOK FILE (supports .epub and .docx):
# Place your ebook file in the input/ directory, or specify a full path here
input_file_path = INPUT_DIR / 'your-book.epub'  # Change this to your actual filename

# 3. SET YOUR GOOGLE CLOUD PROJECT ID:
# Find this in Google Cloud Console: https://console.cloud.google.com
# Option 1: Edit these values directly (they're just defaults for public sharing)
project_id = "your-project-id"  # TODO: Replace with your actual project ID
gcs_bucket_name = "your-bucket-name"  # TODO: Replace with your actual bucket name

# Option 2: Create config_local.py with your real values (recommended, gitignored)
try:
    from config_local import PROJECT_ID, BUCKET_NAME
    project_id = PROJECT_ID
    gcs_bucket_name = BUCKET_NAME
    logger.info("✓ Loaded configuration from config_local.py")
except ImportError:
    logger.info("Using default configuration (edit lines 65-66 with your values)")

# 4. VERIFY YOUR CONFIGURATION:
if project_id == "your-project-id" or gcs_bucket_name == "your-bucket-name":
    logger.warning("⚠️  Using placeholder values! Update project_id and gcs_bucket_name")

# 5. SET THE DIRECTORY FOR YOUR DOWNLOADED AUDIO FILES:
local_output_directory = OUTPUT_DIR

# 6. VOICE SELECTION US or GB
#voice_language_code = 'en-US' #English Male
#voice_name = 'en-US-Chirp3-HD-Umbriel'
#voice_language_code = 'en-US' #English Female
#voice_name = 'en-US-Chirp3-HD-Despina'
voice_language_code = 'en-GB' #British Female
voice_name = 'en-GB-Chirp3-HD-Despina'
#voice_language_code = 'en-GB' #British Male
#voice_name = 'en-GB-Chirp3-HD-Umbriel' 
#voice_language_code = 'en-GB' #British Male - Ranger's Apprentice
#voice_name = 'en-GB-Chirp3-HD-Alnilam' 
#voice_language_code = 'es-US' #Spanish Male
#voice_name = 'es-US-Chirp3-HD-Enceladus'
#voice_language_code = 'ko-KR' #Korean Male
#voice_name = 'ko-KR-Chirp3-HD-Umbriel'
#voice_language_code = 'ja-JP' #Japanese Male
#voice_name = 'ja-JP-Chirp3-HD-Umbriel'

# 7. AUDIO ENCODING - Long Audio Synthesis only supports LINEAR16
audio_encoding = texttospeech_v1.AudioEncoding.LINEAR16

# 8. DOCX HEADING STYLE FOR CHAPTERS (only used for .docx files)
chapter_heading_style = 'Heading 1'

# 9. GOOGLE CLOUD LOCATION
location = "global"

# 10. FILE NAMING CONFIGURATION
audiobook_base_name = "Hannah"

# 11. PREFACE NAMING
preface_name = "Preface"

# 12. ENHANCED SENTENCE LENGTH LIMITS AND TIMEOUTS
max_sentence_length = 200  # Increased from 180
max_chunk_length = 180     # Increased from 150
max_timeout = 1800         # 30 minutes instead of 10
retry_attempts = 3         # Number of retry attempts

# --- End of Configuration ---

def get_file_type(filepath):
    """Determine the file type based on extension."""
    ext = os.path.splitext(filepath)[1].lower()
    if ext == '.epub':
        return 'epub'
    elif ext == '.docx':
        return 'docx'
    else:
        raise ValueError(f"Unsupported file type: {ext}. Supported types: .epub, .docx")

def sanitize_filename(name):
    """Removes or replaces characters not suitable for filenames."""
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'[-\s]+', '_', name).strip('_')
    return name if name else "untitled"

def extract_chapter_number(title):
    """
    Extracts chapter number from title if present.
    Returns (chapter_number, cleaned_title) or (None, original_title)
    """
    patterns = [
        r'^(chapter|ch\.?)\s*(\d+)(.*)$',
        r'^(\d+)\.?\s*(.*)$',
    ]
    
    for pattern in patterns:
        match = re.match(pattern, title.strip(), re.IGNORECASE)
        if match:
            groups = match.groups()
            
            if pattern == patterns[0] and len(groups) >= 3:
                try:
                    chapter_num = int(groups[1])
                    rest = groups[2].strip() if groups[2] else ""
                    rest = re.sub(r'^[:\-\.\s]+', '', rest).strip()
                    return chapter_num, rest
                except ValueError:
                    continue
            
            elif pattern == patterns[1] and len(groups) >= 2:
                try:
                    chapter_num = int(groups[0])
                    rest = groups[1].strip() if groups[1] else ""
                    rest = re.sub(r'^[:\-\.\s]+', '', rest).strip()
                    return chapter_num, rest
                except ValueError:
                    continue
    
    return None, title

def extract_text_from_html(html_content):
    """Extract clean text from HTML content."""
    if not html_content:
        return ""
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    for script in soup(["script", "style"]):
        script.decompose()
    
    text = soup.get_text()
    
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = ' '.join(chunk for chunk in chunks if chunk)
    
    return text

def extract_chapters_from_epub(epub_filepath):
    """Extracts chapters from an EPUB file."""
    try:
        book = epub.read_epub(epub_filepath)
    except Exception as e:
        logger.error(f"Error opening or parsing EPUB file '{epub_filepath}': {e}")
        return

    spine_items = []
    for item_id, linear in book.spine:
        try:
            item = book.get_item_with_id(item_id)
        except AttributeError:
            item = book.get_item_by_id(item_id)
        
        if item and item.get_type() == ebooklib.ITEM_DOCUMENT:
            spine_items.append(item)
    
    if not spine_items:
        logger.error("No readable content found in EPUB file.")
        return
    
    toc_titles = {}
    def extract_toc_titles(toc_item, level=0):
        if isinstance(toc_item, tuple):
            section, children = toc_item
            if hasattr(section, 'href') and hasattr(section, 'title'):
                href = section.href.split('#')[0]
                toc_titles[href] = section.title.strip()
            
            for child in children:
                extract_toc_titles(child, level + 1)
        elif hasattr(toc_item, 'href') and hasattr(toc_item, 'title'):
            href = toc_item.href.split('#')[0]
            toc_titles[href] = toc_item.title.strip()
    
    for toc_item in book.toc:
        extract_toc_titles(toc_item)
    
    chapter_count = 0
    for item in spine_items:
        content = item.get_content().decode('utf-8', errors='ignore')
        text = extract_text_from_html(content)
        
        if not text.strip():
            continue
        
        original_title = toc_titles.get(item.get_name(), "")
        
        if not original_title:
            soup = BeautifulSoup(content, 'html.parser')
            for tag in ['h1', 'h2', 'h3', 'title']:
                heading = soup.find(tag)
                if heading and heading.get_text().strip():
                    original_title = heading.get_text().strip()
                    break
        
        if not original_title:
            original_title = f"Chapter {chapter_count + 1}"
        
        chapter_num, clean_title = extract_chapter_number(original_title)
        
        chapter_count += 1
        yield clean_title, text, chapter_num, original_title

def extract_chapters_from_docx(docx_filepath, heading_style_name):
    """Extracts chapters from a DOCX file."""
    try:
        doc = Document(docx_filepath)
    except Exception as e:
        logger.error(f"Error opening or parsing DOCX file '{docx_filepath}': {e}")
        return

    chapters = []
    current_chapter_title = preface_name
    current_chapter_paragraphs = []
    has_found_first_chapter_heading = False
    current_chapter_num = None
    current_original_title = preface_name

    for para in doc.paragraphs:
        para_text = para.text.strip()
        if para.style.name == heading_style_name:
            has_found_first_chapter_heading = True
            if current_chapter_paragraphs:
                chapters.append((current_chapter_title, "\n".join(current_chapter_paragraphs), current_chapter_num, current_original_title))
            
            if para_text:
                current_original_title = para_text
                chapter_num, clean_title = extract_chapter_number(para_text)
                current_chapter_num = chapter_num
                current_chapter_title = clean_title if clean_title else para_text
            else:
                current_original_title = f"Untitled Chapter"
                current_chapter_title = "Untitled Chapter"
                current_chapter_num = None
            
            current_chapter_paragraphs = []
        elif para_text:
            current_chapter_paragraphs.append(para_text)
    
    if current_chapter_paragraphs or (not chapters and (current_chapter_title != preface_name or has_found_first_chapter_heading)):
        chapters.append((current_chapter_title, "\n".join(current_chapter_paragraphs), current_chapter_num, current_original_title))
    
    if not chapters and not current_chapter_paragraphs:
         logger.warning(f"No content or chapter headings matching style '{heading_style_name}' found in the document.")
         return

    for title, text, chapter_num, original_title in chapters:
        yield title, text, chapter_num, original_title

def extract_chapters(file_path, file_type, heading_style=None):
    """Universal chapter extraction function."""
    if file_type == 'epub':
        return extract_chapters_from_epub(file_path)
    elif file_type == 'docx':
        if not heading_style:
            heading_style = chapter_heading_style
        return extract_chapters_from_docx(file_path, heading_style)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")

def generate_filename(base_name, sequential_number):
    """Generate simplified filename."""
    return f"{base_name}_{sequential_number}"

def aggressive_sentence_splitting(text, max_length=max_sentence_length):
    """Aggressively splits long sentences with multiple fallback strategies."""
    try:
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            logger.info("Downloading NLTK punkt tokenizer...")
            nltk.download('punkt', quiet=True)
        
        sentences = nltk.sent_tokenize(text)
    except:
        sentences = text.split('.')
        sentences = [s.strip() + '.' for s in sentences if s.strip()]
    
    processed_sentences = []
    
    for sentence in sentences:
        if len(sentence) <= max_length:
            processed_sentences.append(sentence)
        else:
            split_sentence = split_long_sentence_aggressively(sentence, max_length)
            if split_sentence:
                processed_sentences.extend(split_sentence)
            else:
                logger.warning(f"Skipping overly complex sentence of {len(sentence)} characters")
                continue
    
    return ' '.join(processed_sentences)

def split_long_sentence_aggressively(sentence, max_length):
    """Aggressively splits a single long sentence."""
    connectors = [' and ', ' but ', ' or ', ' so ', ' yet ', ' for ', ' nor ', 
                 ' because ', ' since ', ' although ', ' while ', ' whereas ', 
                 ' however ', ' moreover ', ' furthermore ', ' therefore ', 
                 ' consequently ', ' nevertheless ', ' meanwhile ']
    
    for connector in connectors:
        if connector in sentence and len(sentence) > max_length:
            parts = sentence.split(connector)
            if len(parts) > 1:
                result = []
                for i, part in enumerate(parts):
                    if i == 0:
                        result.append(part.strip() + '.')
                    else:
                        connector_part = connector.strip().capitalize() + ' ' + part.strip()
                        if not connector_part.endswith('.'):
                            connector_part += '.'
                        result.append(connector_part)
                
                if all(len(p) <= max_length for p in result):
                    return result
    
    if ',' in sentence and len(sentence) > max_length:
        parts = sentence.split(',')
        if len(parts) > 2:
            result = []
            current_part = ""
            
            for i, part in enumerate(parts):
                test_part = current_part + (',' if current_part else '') + part.strip()
                
                if len(test_part) <= max_length:
                    current_part = test_part
                else:
                    if current_part:
                        result.append(current_part + '.')
                        current_part = part.strip()
                    else:
                        if len(part.strip()) > max_length:
                            result.extend(force_split_text(part.strip(), max_chunk_length))
                        else:
                            current_part = part.strip()
            
            if current_part:
                result.append(current_part + '.')
            
            return result
    
    for delimiter in [' - ', ' -- ', ' — ']:
        if delimiter in sentence:
            parts = sentence.split(delimiter)
            if len(parts) > 1 and all(len(p.strip()) <= max_length for p in parts):
                return [p.strip() + '.' for p in parts if p.strip()]
    
    if len(sentence) > max_length:
        return force_split_text(sentence, max_chunk_length)
    
    return None

def force_split_text(text, chunk_size):
    """Force splits text into chunks."""
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    words = text.split()
    current_chunk = ""
    
    for word in words:
        test_chunk = current_chunk + (' ' if current_chunk else '') + word
        
        if len(test_chunk) <= chunk_size:
            current_chunk = test_chunk
        else:
            if current_chunk:
                chunks.append(current_chunk + '.')
                current_chunk = word
            else:
                chunks.append(word[:chunk_size] + '.')
                current_chunk = word[chunk_size:]
    
    if current_chunk:
        chunks.append(current_chunk + '.')
    
    return chunks

def enhanced_check_text_size(text, chapter_title):
    """Enhanced text size checking with detailed logging."""
    text_bytes = text.encode('utf-8')
    text_size = len(text_bytes)
    max_size = 900_000  # Slightly under 1MB to be safe
    
    logger.info(f"Chapter '{chapter_title}': {text_size} bytes, {len(text)} characters, {len(text.split())} words")
    
    if text_size > max_size:
        logger.warning(f"Chapter '{chapter_title}' exceeds size limit ({text_size} > {max_size} bytes)")
        return False, text_size
    
    return True, text_size

def robust_text_preprocessing(text, chapter_title):
    """More robust text preprocessing with detailed error handling."""
    try:
        logger.info(f"Starting text preprocessing for '{chapter_title}'")
        
        # Clean problematic characters that cause TTS issues
        problematic_chars = ['—', '"', '"', 'Â']
        for char in problematic_chars:
            if char in text:
                logger.warning(f"Found problematic character '{char}' in '{chapter_title}', cleaning...")
                text = text.replace(char, ' ')
        
        # Clean up unicode issues
        text = text.encode('utf-8', errors='ignore').decode('utf-8')
        
        # Try aggressive sentence splitting
        processed_text = aggressive_sentence_splitting(text, max_sentence_length)
        
        # Verify the result
        if not processed_text or len(processed_text.strip()) == 0:
            logger.error(f"Text preprocessing resulted in empty text for '{chapter_title}'")
            return text
        
        # Check sentence lengths in processed text
        sentences = processed_text.split('.')
        long_sentences = [s for s in sentences if len(s) > max_sentence_length]
        
        if long_sentences:
            logger.warning(f"'{chapter_title}' still has {len(long_sentences)} sentences over {max_sentence_length} characters after processing")
            for i, sentence in enumerate(long_sentences[:3]):
                logger.warning(f"Long sentence {i+1}: {len(sentence)} chars - '{sentence[:100]}...'")
        
        logger.info(f"Text preprocessing completed for '{chapter_title}': {len(processed_text)} characters")
        return processed_text
        
    except Exception as e:
        logger.error(f"Error in text preprocessing for '{chapter_title}': {e}")
        logger.info(f"Returning original text for '{chapter_title}'")
        return text

def select_chapters_to_process(chapters_list):
    """Shows available chapters and allows user to select which ones to process."""
    print("\n" + "="*60)
    print("CHAPTERS FOUND:")
    print("="*60)
    
    for i, (title, text, chapter_num, original_title) in enumerate(chapters_list, 1):
        word_count = len(text.split())
        print(f"{i:2d}. {original_title} ({word_count:,} words)")
    
    print("="*60)
    print(f"Total: {len(chapters_list)} chapters found")
    print("="*60)
    
    while True:
        choice = input("\nProcess all chapters? (y/n) or enter chapter numbers (e.g., 1,3,5-7): ").strip().lower()
        
        if choice in ['y', 'yes', '']:
            return list(range(len(chapters_list)))
        elif choice in ['n', 'no']:
            print("Exiting without processing.")
            return []
        else:
            try:
                selected = []
                parts = choice.split(',')
                
                for part in parts:
                    part = part.strip()
                    if '-' in part:
                        start, end = map(int, part.split('-'))
                        selected.extend(range(start-1, end))
                    else:
                        selected.append(int(part) - 1)
                
                valid_selections = [i for i in selected if 0 <= i < len(chapters_list)]
                invalid_selections = [i+1 for i in selected if i < 0 or i >= len(chapters_list)]
                
                if invalid_selections:
                    print(f"Invalid chapter numbers: {invalid_selections}")
                    continue
                
                if valid_selections:
                    selected_titles = [chapters_list[i][3] for i in valid_selections]
                    print(f"\nSelected {len(valid_selections)} chapters:")
                    for i, title in enumerate(selected_titles, 1):
                        print(f"  {i}. {title}")
                    
                    confirm = input("\nProceed with these chapters? (y/n): ").strip().lower()
                    if confirm in ['y', 'yes', '']:
                        return valid_selections
                else:
                    print("No valid chapters selected.")
                    
            except ValueError:
                print("Invalid input. Please use format like: 1,3,5-7 or 'y' for all")

def enhanced_synthesize_long_audio(chapter_title, chapter_text, chapter_number, original_title, 
                                 filename_base, sequential_number, gcs_bucket, project_id, 
                                 location, voice_name, voice_language_code):
    """Enhanced audio synthesis with better error handling, logging, and retry logic."""
    base_filename = generate_filename(filename_base, sequential_number)
    timestamp = int(time.time())
    gcs_output_uri = f"gs://{gcs_bucket}/{base_filename}_{timestamp}.wav"
    
    if not chapter_text.strip():
        logger.warning(f"Chapter '{original_title}' has no text content. Skipping.")
        return None, None

    logger.info(f"="*60)
    logger.info(f"PROCESSING CHAPTER {sequential_number}: '{original_title}'")
    logger.info(f"Output filename: {base_filename}.wav")
    logger.info(f"="*60)
    
    # Create the chapter announcement text
    if chapter_number is not None:
        chapter_announcement = f"Chapter {chapter_number}. {chapter_title}."
    else:
        chapter_announcement = f"{chapter_title}."
    
    chapter_text_with_announcement = f"{chapter_announcement}\n\n{chapter_text}"
    
    # Enhanced text preprocessing
    try:
        processed_text = robust_text_preprocessing(chapter_text_with_announcement, original_title)
    except Exception as e:
        logger.error(f"CRITICAL: Text preprocessing failed for '{original_title}': {e}")
        return None, None
    
    # Enhanced text size check
    is_within_limit, text_size = enhanced_check_text_size(processed_text, original_title)
    
    if not is_within_limit:
        logger.error(f"SKIPPING: Chapter '{original_title}' exceeds size limits even after processing")
        return None, None
    
    # Calculate enhanced timeout
    base_timeout = 300  # 5 minutes base
    size_timeout = text_size / 500  # 1 second per 500 bytes (more generous)
    calculated_timeout = min(base_timeout + size_timeout, max_timeout)
    
    logger.info(f"Text size: {text_size} bytes, Calculated timeout: {int(calculated_timeout)} seconds")
    
    # Create client and request
    client = texttospeech_v1.TextToSpeechLongAudioSynthesizeClient()
    parent = f"projects/{project_id}/locations/{location}"
    
    request = {
        "parent": parent,
        "input": {"text": processed_text},
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
    for attempt in range(retry_attempts):
        try:
            logger.info(f"Attempt {attempt + 1}/{retry_attempts}: Starting audio synthesis...")
            
            operation = client.synthesize_long_audio(request=request)
            
            logger.info(f"Waiting for synthesis to complete (timeout: {int(calculated_timeout)} seconds)...")
            
            result = operation.result(timeout=calculated_timeout)
            
            logger.info(f"✅ SUCCESS: Synthesis completed for '{original_title}'")
            return gcs_output_uri, base_filename + ".wav"
            
        except gcp_exceptions.DeadlineExceeded:
            logger.error(f"❌ TIMEOUT: Synthesis timed out for '{original_title}' (attempt {attempt + 1})")
            if attempt < retry_attempts - 1:
                wait_time = 60 * (attempt + 1)
                logger.info(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                logger.error(f"❌ FINAL FAILURE: All attempts failed for '{original_title}' due to timeout")
                
        except gcp_exceptions.ResourceExhausted:
            logger.error(f"❌ QUOTA EXCEEDED: API quota exhausted for '{original_title}' (attempt {attempt + 1})")
            if attempt < retry_attempts - 1:
                wait_time = 300
                logger.info(f"Waiting {wait_time} seconds for quota reset...")
                time.sleep(wait_time)
            else:
                logger.error(f"❌ FINAL FAILURE: Quota limit reached for '{original_title}'")
                
        except gcp_exceptions.InvalidArgument as e:
            logger.error(f"❌ INVALID REQUEST: Bad request for '{original_title}': {e}")
            break
            
        except Exception as e:
            logger.error(f"❌ UNEXPECTED ERROR: Synthesis failed for '{original_title}' (attempt {attempt + 1}): {e}")
            if attempt < retry_attempts - 1:
                wait_time = 30 * (attempt + 1)
                logger.info(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                logger.error(f"❌ FINAL FAILURE: All attempts failed for '{original_title}'")
    
    return None, None

def download_from_gcs(gcs_uri, local_directory, final_filename):
    """Downloads a file from Google Cloud Storage."""
    try:
        storage_client = StorageClient()
        
        gcs_path = gcs_uri.replace("gs://", "")
        bucket_name = gcs_path.split("/")[0]
        object_name = "/".join(gcs_path.split("/")[1:])
        
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(object_name)
        
        local_file_path = os.path.join(local_directory, final_filename)
        
        print(f"Downloading to '{final_filename}'...")
        blob.download_to_filename(local_file_path)
        print(f"✅ Downloaded successfully")
        
        return local_file_path
    
    except Exception as e:
        logger.error(f"❌ Error downloading from GCS: {e}")
        return None

def cleanup_gcs_file(gcs_uri):
    """Deletes the temporary file from Google Cloud Storage."""
    try:
        storage_client = StorageClient()
        
        gcs_path = gcs_uri.replace("gs://", "")
        bucket_name = gcs_path.split("/")[0]
        object_name = "/".join(gcs_path.split("/")[1:])
        
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(object_name)
        
        blob.delete()
        logger.info(f"✅ Cleaned up temporary file from GCS")
        
    except Exception as e:
        logger.warning(f"Could not cleanup GCS file: {e}")

def estimate_cost(chapters_list, voice_name):
    """
    Estimate the cost of generating audiobook based on character count.

    Args:
        chapters_list: List of (title, text, chapter_num, original_title) tuples
        voice_name: Name of the voice being used

    Returns:
        Dictionary with character count, estimated cost, and duration
    """
    # Count total characters
    total_chars = sum(len(text) for _, text, _, _ in chapters_list)

    # Pricing per million characters (as of 2024)
    voice_pricing = {
        'Standard': 4.00,
        'WaveNet': 16.00,
        'Neural2': 16.00,
        'Chirp3-HD': 16.00,  # Premium tier
        'Studio': 16.00,
    }

    # Determine voice type from voice_name
    voice_type = 'Standard'  # Default
    if 'Chirp3-HD' in voice_name or 'Chirp' in voice_name:
        voice_type = 'Chirp3-HD'
    elif 'Neural2' in voice_name:
        voice_type = 'Neural2'
    elif 'WaveNet' in voice_name:
        voice_type = 'WaveNet'
    elif 'Studio' in voice_name:
        voice_type = 'Studio'

    price_per_million = voice_pricing.get(voice_type, 16.00)
    estimated_cost = (total_chars / 1_000_000) * price_per_million

    # Estimate duration (rough approximation: ~1000 chars per minute of audio)
    duration_minutes = total_chars / 1000
    duration_hours = duration_minutes / 60

    return {
        'total_characters': total_chars,
        'voice_type': voice_type,
        'price_per_million': price_per_million,
        'estimated_cost': estimated_cost,
        'duration_minutes': duration_minutes,
        'duration_hours': duration_hours,
        'chapter_count': len(chapters_list)
    }

def print_cost_estimate(estimate):
    """Pretty print the cost estimate."""
    print(f"\n{'='*60}")
    print(f"📊 COST ESTIMATE")
    print(f"{'='*60}")
    print(f"📖 Chapters: {estimate['chapter_count']}")
    print(f"📝 Characters: {estimate['total_characters']:,}")
    print(f"🎙️ Voice type: {estimate['voice_type']} (${estimate['price_per_million']:.2f}/million chars)")
    print(f"💰 Estimated cost: ${estimate['estimated_cost']:.2f}")

    # Format duration nicely
    if estimate['duration_hours'] >= 1:
        hours = int(estimate['duration_hours'])
        minutes = int((estimate['duration_hours'] - hours) * 60)
        print(f"⏱️  Estimated duration: ~{hours}h {minutes}m")
    else:
        print(f"⏱️  Estimated duration: ~{int(estimate['duration_minutes'])}m")

    print(f"{'='*60}\n")

# --- Main execution ---
if __name__ == "__main__":
    # Create local output directory if it doesn't exist (already created above, but double-check)
    local_output_directory.mkdir(parents=True, exist_ok=True)
    print(f"✓ Output directory ready: {local_output_directory}")

    try:
        file_type = get_file_type(str(input_file_path))
        print(f"\n🎧 Enhanced AudioBook Generator")
        print(f"📖 File type: {file_type.upper()}")
        print(f"🏷️ Output pattern: {audiobook_base_name}_X.wav")
        
        if file_type == 'docx':
            print(f"🔑 Reading DOCX with heading style: '{chapter_heading_style}'")
        else:
            print(f"📚 Reading EPUB file")
        
        print(f"🎯 Target directory: {local_output_directory}")

        # Check if input file exists
        if not Path(input_file_path).exists():
            print(f"\n❌ ERROR: Input file not found at '{input_file_path}'")
            print(f"Please place your ebook file in: {INPUT_DIR}")
            exit()
        print(f"📝 Logging to: audiobook_processing.log")
        
        logger.info("Starting audiobook generation process")
        
        # Extract all chapters first
        print(f"\n📋 Extracting chapters...")
        chapters_list = list(extract_chapters(str(input_file_path), file_type))
        
        if not chapters_list:
            print(f"\n❌ No chapters found in the {file_type.upper()} file.")
            if file_type == 'docx':
                print(f"Please verify the heading style '{chapter_heading_style}' is correct.")
            exit()
        
        logger.info(f"Found {len(chapters_list)} chapters")

        # Show cost estimate
        cost_estimate = estimate_cost(chapters_list, voice_name)
        print_cost_estimate(cost_estimate)

        # Ask if user wants to proceed
        proceed = input("⚠️  Proceed with audiobook generation? (y/n): ").strip().lower()
        if proceed not in ['y', 'yes']:
            print("Cancelled by user.")
            exit()

        # Let user select which chapters to process
        selected_indices = select_chapters_to_process(chapters_list)
        
        if not selected_indices:
            print("No chapters selected. Exiting.")
            exit()
        
        # Process selected chapters with enhanced tracking
        print(f"\n🎵 Starting audio synthesis for {len(selected_indices)} chapters...")
        print("="*60)

        successful_chapters = 0
        skipped_chapters = []
        gcs_uris_and_filenames = []

        # Use tqdm for progress bar
        with tqdm(total=len(selected_indices), desc="🎧 Processing", unit="chapter",
                  bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]') as pbar:

            for processing_order, chapter_index in enumerate(selected_indices, 1):
                title, text_content, chapter_num, original_title = chapters_list[chapter_index]

                # Update progress bar with current chapter name
                pbar.set_postfix_str(f"{original_title[:40]}...")

                gcs_uri, final_filename = enhanced_synthesize_long_audio(
                    title, text_content, chapter_num, original_title,
                    audiobook_base_name, processing_order, gcs_bucket_name,
                    project_id, location, voice_name, voice_language_code
                )

                if gcs_uri and final_filename:
                    gcs_uris_and_filenames.append((gcs_uri, final_filename))
                    successful_chapters += 1
                    logger.info(f"✅ Chapter {processing_order} completed successfully")
                else:
                    skipped_chapters.append((processing_order, original_title))
                    logger.error(f"❌ Chapter {processing_order} was skipped: '{original_title}'")

                # Update progress bar
                pbar.update(1)
        
        print("="*60)
        print(f"✅ Successfully synthesized {successful_chapters}/{len(selected_indices)} chapters")
        
        if skipped_chapters:
            print(f"\n❌ SKIPPED CHAPTERS ({len(skipped_chapters)}):")
            for order, title in skipped_chapters:
                print(f"   {order}. {title}")
            print(f"\nCheck 'audiobook_processing.log' for detailed error information.")
        
        if gcs_uris_and_filenames:
            # Download all generated audio files
            print(f"\n📥 Downloading audio files...")
            successful_downloads = 0

            with tqdm(total=len(gcs_uris_and_filenames), desc="💾 Downloading", unit="file",
                      bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]') as pbar:

                for gcs_uri, final_filename in gcs_uris_and_filenames:
                    pbar.set_postfix_str(f"{final_filename}")
                    local_path = download_from_gcs(gcs_uri, local_output_directory, final_filename)
                    if local_path:
                        successful_downloads += 1
                        cleanup_gcs_file(gcs_uri)
                    pbar.update(1)
            
            print(f"\n🎉 Process Complete!")
            print(f"📊 Successfully downloaded: {successful_downloads}/{len(gcs_uris_and_filenames)} files")
            print(f"📁 Location: {local_output_directory}")
            print(f"🏷️ Files named: {audiobook_base_name}_1.wav, {audiobook_base_name}_2.wav, etc.")
            
            logger.info(f"Process completed. {successful_downloads}/{len(gcs_uris_and_filenames)} files downloaded successfully")
        else:
            print(f"\n❌ No audio files were generated successfully.")
            logger.error("No audio files were generated successfully")

    except FileNotFoundError:
        error_msg = f"ERROR: Input file not found at '{input_file_path}' or credentials file not found."
        print(f"❌ {error_msg}")
        logger.error(error_msg)
        print("Please check GOOGLE_APPLICATION_CREDENTIALS path.")
    except ImportError as e:
        error_msg = f"ERROR: Required library missing: {e}"
        print(f"❌ {error_msg}")
        logger.error(error_msg)
        print("Install with: pip install google-cloud-texttospeech google-cloud-storage ebooklib beautifulsoup4 python-docx nltk")
    except ValueError as e:
        error_msg = f"ERROR: {e}"
        print(f"❌ {error_msg}")
        logger.error(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error: {e}"
        print(f"❌ {error_msg}")
        logger.error(error_msg)
        import traceback
        traceback.print_exc()