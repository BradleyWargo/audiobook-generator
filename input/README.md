# Input Directory

Place your ebook files here for conversion to audiobooks.

## Supported Formats

- **EPUB** (`.epub`) - Most common ebook format
- **DOCX** (`.docx`) - Microsoft Word documents

## Usage

1. Copy your ebook file to this directory:
   ```
   input/my-book.epub
   input/novel.docx
   ```

2. Update the filename in `src/audiobook_generator.py` (line 61):
   ```python
   input_file_path = INPUT_DIR / 'my-book.epub'
   ```

3. Run the script:
   ```bash
   python src/audiobook_generator.py
   ```

## Notes

- Files in this directory are gitignored (won't be committed)
- Keep original ebooks for backup
- File size doesn't matter - script processes chapters individually
- For DOCX files, chapters should be marked with "Heading 1" style

## Examples

Good filenames:
- `Hannah_Coulter.epub`
- `my-novel.docx`
- `book-title-v2.epub`

Avoid:
- Spaces in filenames (use underscores or hyphens instead)
- Special characters (#, $, %, etc.)
