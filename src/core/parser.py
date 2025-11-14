"""
Chapter extraction and text processing for ebooks
"""
import re
import logging
from pathlib import Path
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from docx import Document
import nltk

logger = logging.getLogger(__name__)


class EbookParser:
    """Parser for extracting chapters from ebooks"""

    def __init__(self, max_sentence_length=200, max_chunk_length=180):
        self.max_sentence_length = max_sentence_length
        self.max_chunk_length = max_chunk_length
        self._ensure_nltk_data()

    def _ensure_nltk_data(self):
        """Ensure NLTK punkt data is available"""
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            logger.info("Downloading NLTK punkt tokenizer...")
            nltk.download('punkt', quiet=True)

    @staticmethod
    def get_file_type(filepath):
        """Determine the file type based on extension"""
        ext = Path(filepath).suffix.lower()
        if ext == '.epub':
            return 'epub'
        elif ext == '.docx':
            return 'docx'
        else:
            raise ValueError(f"Unsupported file type: {ext}. Supported: .epub, .docx")

    @staticmethod
    def sanitize_filename(name):
        """Remove or replace characters not suitable for filenames"""
        name = re.sub(r'[^\w\s-]', '', name)
        name = re.sub(r'[-\s]+', '_', name).strip('_')
        return name if name else "untitled"

    @staticmethod
    def extract_chapter_number(title):
        """
        Extract chapter number from title if present
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

    @staticmethod
    def extract_text_from_html(html_content):
        """Extract clean text from HTML content"""
        if not html_content:
            return ""

        soup = BeautifulSoup(html_content, 'html.parser')

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        text = soup.get_text()

        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)

        return text

    def extract_chapters_from_epub(self, epub_filepath):
        """Extract chapters from an EPUB file"""
        try:
            book = epub.read_epub(epub_filepath)
        except Exception as e:
            logger.error(f"Error opening EPUB file '{epub_filepath}': {e}")
            raise

        # Get spine items (reading order)
        spine_items = []
        for item_id, linear in book.spine:
            try:
                item = book.get_item_with_id(item_id)
            except AttributeError:
                item = book.get_item_by_id(item_id)

            if item and item.get_type() == ebooklib.ITEM_DOCUMENT:
                spine_items.append(item)

        if not spine_items:
            raise ValueError("No readable content found in EPUB file")

        # Extract table of contents titles
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

        # Extract chapters
        chapter_count = 0
        for item in spine_items:
            content = item.get_content().decode('utf-8', errors='ignore')
            text = self.extract_text_from_html(content)

            if not text.strip():
                continue

            # Get title from TOC or heading
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

            chapter_num, clean_title = self.extract_chapter_number(original_title)

            chapter_count += 1
            yield clean_title, text, chapter_num, original_title

    def extract_chapters_from_docx(self, docx_filepath, heading_style_name='Heading 1'):
        """Extract chapters from a DOCX file"""
        try:
            doc = Document(docx_filepath)
        except Exception as e:
            logger.error(f"Error opening DOCX file '{docx_filepath}': {e}")
            raise

        chapters = []
        current_chapter_title = "Preface"
        current_chapter_paragraphs = []
        has_found_first_chapter_heading = False
        current_chapter_num = None
        current_original_title = "Preface"

        for para in doc.paragraphs:
            para_text = para.text.strip()
            if para.style.name == heading_style_name:
                has_found_first_chapter_heading = True
                if current_chapter_paragraphs:
                    chapters.append((
                        current_chapter_title,
                        "\n".join(current_chapter_paragraphs),
                        current_chapter_num,
                        current_original_title
                    ))

                if para_text:
                    current_original_title = para_text
                    chapter_num, clean_title = self.extract_chapter_number(para_text)
                    current_chapter_num = chapter_num
                    current_chapter_title = clean_title if clean_title else para_text
                else:
                    current_original_title = "Untitled Chapter"
                    current_chapter_title = "Untitled Chapter"
                    current_chapter_num = None

                current_chapter_paragraphs = []
            elif para_text:
                current_chapter_paragraphs.append(para_text)

        # Add last chapter
        if current_chapter_paragraphs or (not chapters and has_found_first_chapter_heading):
            chapters.append((
                current_chapter_title,
                "\n".join(current_chapter_paragraphs),
                current_chapter_num,
                current_original_title
            ))

        if not chapters:
            raise ValueError(f"No chapters found with style '{heading_style_name}'")

        for title, text, chapter_num, original_title in chapters:
            yield title, text, chapter_num, original_title

    def extract_chapters(self, file_path, heading_style='Heading 1'):
        """Universal chapter extraction function"""
        file_type = self.get_file_type(file_path)

        if file_type == 'epub':
            return self.extract_chapters_from_epub(file_path)
        elif file_type == 'docx':
            return self.extract_chapters_from_docx(file_path, heading_style)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

    def process_text(self, text):
        """
        Process text for TTS conversion
        Cleans problematic characters and splits long sentences
        """
        # Clean problematic characters
        problematic_chars = ['—', '"', '"', 'Â']
        for char in problematic_chars:
            text = text.replace(char, ' ')

        # Clean up unicode issues
        text = text.encode('utf-8', errors='ignore').decode('utf-8')

        # Aggressive sentence splitting
        processed_text = self.aggressive_sentence_splitting(text)

        return processed_text

    def aggressive_sentence_splitting(self, text):
        """Aggressively split long sentences"""
        try:
            sentences = nltk.sent_tokenize(text)
        except:
            sentences = text.split('.')
            sentences = [s.strip() + '.' for s in sentences if s.strip()]

        processed_sentences = []

        for sentence in sentences:
            if len(sentence) <= self.max_sentence_length:
                processed_sentences.append(sentence)
            else:
                split_sentence = self.split_long_sentence(sentence)
                if split_sentence:
                    processed_sentences.extend(split_sentence)
                else:
                    logger.warning(f"Skipping overly complex sentence of {len(sentence)} characters")
                    continue

        return ' '.join(processed_sentences)

    def split_long_sentence(self, sentence):
        """Split a single long sentence"""
        connectors = [
            ' and ', ' but ', ' or ', ' so ', ' yet ', ' for ', ' nor ',
            ' because ', ' since ', ' although ', ' while ', ' whereas ',
            ' however ', ' moreover ', ' furthermore ', ' therefore ',
            ' consequently ', ' nevertheless ', ' meanwhile '
        ]

        # Try splitting on connectors
        for connector in connectors:
            if connector in sentence and len(sentence) > self.max_sentence_length:
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

                    if all(len(p) <= self.max_sentence_length for p in result):
                        return result

        # Try splitting on commas
        if ',' in sentence and len(sentence) > self.max_sentence_length:
            parts = sentence.split(',')
            if len(parts) > 2:
                result = []
                current_part = ""

                for i, part in enumerate(parts):
                    test_part = current_part + (',' if current_part else '') + part.strip()

                    if len(test_part) <= self.max_sentence_length:
                        current_part = test_part
                    else:
                        if current_part:
                            result.append(current_part + '.')
                            current_part = part.strip()
                        else:
                            if len(part.strip()) > self.max_sentence_length:
                                result.extend(self.force_split_text(part.strip()))
                            else:
                                current_part = part.strip()

                if current_part:
                    result.append(current_part + '.')

                return result

        # Force split if too long
        if len(sentence) > self.max_sentence_length:
            return self.force_split_text(sentence)

        return None

    def force_split_text(self, text):
        """Force split text into chunks by words"""
        if len(text) <= self.max_chunk_length:
            return [text]

        chunks = []
        words = text.split()
        current_chunk = ""

        for word in words:
            test_chunk = current_chunk + (' ' if current_chunk else '') + word

            if len(test_chunk) <= self.max_chunk_length:
                current_chunk = test_chunk
            else:
                if current_chunk:
                    chunks.append(current_chunk + '.')
                    current_chunk = word
                else:
                    # Word itself is too long
                    chunks.append(word[:self.max_chunk_length] + '.')
                    current_chunk = word[self.max_chunk_length:]

        if current_chunk:
            chunks.append(current_chunk + '.')

        return chunks

    @staticmethod
    def estimate_cost(chapters, voice_name):
        """
        Estimate the cost of generating audiobook
        Returns dict with character count, estimated cost, and duration
        """
        total_chars = sum(len(text) for _, text, _, _ in chapters)

        # Pricing per million characters
        voice_pricing = {
            'Standard': 4.00,
            'WaveNet': 16.00,
            'Neural2': 16.00,
            'Chirp3-HD': 16.00,
            'Studio': 16.00,
        }

        # Determine voice type
        voice_type = 'Standard'
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

        # Estimate duration (~1000 chars per minute of audio)
        duration_minutes = total_chars / 1000
        duration_hours = duration_minutes / 60

        return {
            'total_characters': total_chars,
            'voice_type': voice_type,
            'price_per_million': price_per_million,
            'estimated_cost': estimated_cost,
            'duration_minutes': duration_minutes,
            'duration_hours': duration_hours,
            'chapter_count': len(chapters)
        }
