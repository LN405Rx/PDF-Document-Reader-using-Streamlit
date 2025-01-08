# PDF to Audiobook Converter

[![Python application](https://github.com/LN405Rx/PDF-Document-Reader-using-Streamlit/actions/workflows/python-app.yml/badge.svg)](https://github.com/LN405Rx/PDF-Document-Reader-using-Streamlit/actions/workflows/python-app.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)

A Streamlit application that converts PDF documents to audiobooks using text-to-speech technology and runs locally on your computer.

## Features

- Upload and process PDF documents
- Text-to-speech conversion with adjustable settings
- Two voice options for text-to-speech
- Support for scanned PDFs through OCR (requires Tesseract)
- Progress tracking for long operations
- Clean resource management
- Error handling and recovery

## Requirements

- Python 3.8+
- Tesseract OCR (optional, for scanned PDFs)

## Installation

1. Clone the repository
   ```bash
   git clone https://github.com/LN405Rx/PDF-Document-Reader-using-Streamlit.git
   cd PDF-Document-Reader-using-Streamlit
   ```

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
3. Adjust voice settings:
   - Select your preferred voice
   - Adjust speed (50-400 wpm)
   - Set volume level
4. Use playback controls to navigate and listen to the content

## Contributing

Contributions are welcome! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details on how to submit pull requests, report issues, and contribute to the project.

## Security

For details about the security policy and how to report security vulnerabilities, please see our [Security Policy](SECURITY.md).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Uses [pyttsx3](https://github.com/nateshmbhat/pyttsx3) for text-to-speech
