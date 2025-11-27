# 🌍 Travel Language Learning Voice Assistant (Homework Edition)

A local voice assistant for practicing a target language in travel contexts. Built for a homework/demo scenario: minimal dependencies, easy local setup.
It uses:
- **Ollama** for local LLM generation
- **Whisper (faster-whisper)** for speech-to-text
- **Gradio** for a simple web UI

## Features
- Speak into your microphone; get instant transcription
- Assistant replies in target language + provides English translation
- Alternative phrases with formality/usage notes
- Gentle corrections of your mistakes
- Scenario role-play modes (Restaurant, Hotel, Directions, Shopping, Emergency)
- Cultural/etiquette tips every few turns
- Optional streaming responses
- Text-to-Speech playback of assistant reply (Edge TTS voices)
- Progress tracking: turn count, corrections, top vocabulary
- Vocabulary accumulation from target-language replies

## Requirements
- Windows (PowerShell 5.1) with Python 3.10+ recommended
- Ollama running (via WSL2 if native Windows build unavailable)
- (Optional) GPU for Whisper acceleration (CUDA)

## Quick Start (Windows PowerShell)

```powershell
cd "c:\Users\andy9\OneDrive\桌面\新增資料夾"
python -m venv .venv
.venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

Make sure Ollama is running (in WSL or native) and the model (e.g. `llama3`) is pulled.

Then:
```powershell
python app.py
```
Open the printed Gradio URL.

## Detailed Installation

### 1. Install Ollama (Windows via WSL2)
Open **Windows Terminal** and create/update WSL (Ubuntu recommended):
```powershell
wsl --install
```
Inside the Ubuntu shell:
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3
```
Leave WSL running; Ollama listens on `http://localhost:11434` accessible from Windows.

(If a native Windows version of Ollama is available at install time, use its installer instead.)

### 2. Clone / Prepare Project
```powershell
git clone https://github.com/880121andy/travel-language-assistant
python -m venv .venv
.venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Whisper Model Size
By default we load `small`. Adjust in `whisper_transcriber.py`:
```python
transcriber = WhisperTranscriber(model_size="medium")
```
Larger models improve accuracy but use more memory.

### 4. Run the App
Ensure Ollama is running (`ollama run llama3` once to preload or just keep daemon). Then:
```powershell
.venv\Scripts\activate
python app.py
```
Open the Gradio URL (usually `http://127.0.0.1:7860`).

### 5. (Optional) Change TTS Voice
Edit `tts.py` and swap the mapped neural voice for your target language.

### 6. (Optional) Clear Progress
Delete `progress.json` to reset stats.

## Usage Tips
1. Select target language and mode.
2. In Scenario mode, speak as if you are in that situation.
3. Try to respond in the target language; the assistant will correct you.
4. Toggle streaming for incremental replies (experimental).
5. Use the audio playback to shadow and mimic pronunciation.
6. Monitor stats to focus on repeated vocabulary.

## Customization
- Change base system prompt logic in `prompts.py`.
- Switch model in `ollama_client.py` (`model="llama3"` -> `mistral` or another multilingual model).
- Add more scenarios by extending `SCENARIOS` in `app.py`.
 - Adjust vocabulary filtering in `_extract_vocabulary` inside `app.py`.
 - Replace TTS voices in `VOICE_MAP` within `tts.py`.

## Troubleshooting
- If Gradio cannot import: ensure virtual environment is activated.
- If Ollama connection fails: verify WSL is running and port 11434 reachable.
- Whisper GPU issues: set `device="cpu"` in `WhisperTranscriber` for fallback.
 - TTS fails silently: check internet connectivity (Edge TTS uses remote service) or remove autoplay.
 - Streaming shows placeholder text: final translation appears after model completes.

## Next Ideas
- Add text-to-speech for assistant replies (edge-tts).
- Track learner progress and vocabulary.
- Provide spaced repetition quizzes.

## Notes
This repository is for coursework/homework demonstration; no license file included. If you later publish publicly, add a proper LICENSE file (e.g. MIT).
