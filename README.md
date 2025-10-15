# Meeting-Summarizer

Transcribe meeting audio and generate action-oriented summaries (key decisions and tasks).

## Features
- Upload audio files (web UI or API)
- Automatic transcription via ASR (OpenAI by default)
- LLM-generated summary with key decisions and action items
- Persistence in SQLite with retrieval endpoints

## Tech Stack
- Backend: FastAPI, SQLAlchemy (SQLite)
- ASR: OpenAI (default), abstraction to swap providers
- LLM: OpenAI (default)
- Frontend: Minimal HTML/JS uploader and results view

## Setup

1) Prerequisites
- Python 3.10+
- An OpenAI API key


### Web UI
1. Open the page, upload an audio file (e.g., .mp3, .wav, .m4a)
2. Wait for processing, then view transcript, summary, and action items


working demo link
https://drive.google.com/file/d/1J_r7255JnkC36FjYT6OetFL34NRS2pfU/view?usp=sharing
