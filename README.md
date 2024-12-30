# PDF to Audiobook Converter - Streamlit App

A Streamlit-based application that converts PDF files to audiobooks using pyttsx3 for text-to-speech conversion.

## Features

- Convert PDF files to audio in real-time
- Interactive web interface with Streamlit
- Adjustable reading speed and volume
- Progress tracking and status updates
- Efficient memory management
- Error handling and recovery
- Automatic cache cleanup

## Prerequisites

- Python 3.8 or higher
- Streamlit
- pyttsx3
- pdfplumber

## Installation

1. Clone this repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

The application uses an internal configuration class for settings. Key settings include:
- Maximum file size: 50MB
- Cache timeout: 1 hour
- Text chunk size: 100-1000 characters
- Maximum worker threads: 3

## Running the Application

To run the application locally:

```bash
streamlit run app.py
```

## Usage

1. Launch the application using the command above
2. Upload a PDF file using the file uploader
3. Adjust settings in the sidebar (speed, volume, chunk size)
4. Use the play/pause controls to manage audio playback
5. Monitor progress in the status section

## Sample PDFs

Place your PDF files in the `pdf_books` directory. Note that this directory is gitignored by default to avoid accidentally committing copyrighted material. Only add PDF files that you have the rights to use and distribute.

## Last Update

Last updated: 2024-12-09 21:42:17 CST
