# PDF to Audiobook Converter

A Streamlit application that converts PDF documents to audiobooks using text-to-speech technology.

## Features

- Upload and process PDF documents
- Text-to-speech conversion with adjustable settings
- Support for scanned PDFs through OCR (requires Tesseract)
- Progress tracking for long operations
- Clean resource management
- Error handling and recovery

## Requirements

- Python 3.8+
- Tesseract OCR (optional, for scanned PDFs)

## Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. (Optional) Install Tesseract OCR for scanned PDF support:
   - Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
   - Linux: `sudo apt-get install tesseract-ocr`

## Configuration

The application can be configured through environment variables:
- `TESSERACT_PATH`: Path to Tesseract executable (default: 'C:\Program Files\Tesseract-OCR\tesseract.exe')
- `CACHE_DIR`: Directory for temporary files (default: 'cache')

## Usage

1. Start the application:
   ```bash
   streamlit run app.py
   ```
2. Upload a PDF file
3. Adjust voice settings (speed, volume, voice selection)
4. Use playback controls to navigate and listen to the content

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
