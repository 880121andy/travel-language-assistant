import gradio as gr
from ollama_client import OllamaClient
from whisper_transcriber import WhisperTranscriber
from prompts import build_system_prompt
from langdetect import detect
from typing import List, Dict, Generator, Tuple, Any
import re
from tts import synthesize_text
from progress_store import progress_store

SUPPORTED_TARGET_LANGS = ["Spanish", "French", "Japanese", "Mandarin Chinese", "German", "Italian"]
MODES = ["Conversation", "Scenario"]
SCENARIOS = ["Restaurant", "Hotel", "Directions", "Shopping", "Emergency"]

ollama_client = OllamaClient(model="llama3")
transcriber = WhisperTranscriber(model_size="small")

# Maintain conversation state
initial_system_prompt_cache = {}

def init_state():
    return {
        "history": [],  # list of {role, content}
        "turn": 0,
    }

STATE = init_state()

def reset_chat():
    global STATE
    STATE = init_state()
    return gr.update(value=[]), gr.update(value=""), gr.update(value=""), gr.update(value="")


def _extract_vocabulary(text: str) -> List[str]:
    # Basic tokenization: split on non-letter, keep words >=3 chars, exclude common stop words
    stop = set(["the","and","for","you","are","with","that","this","have","has","your","from","will","into","then","here","there"])
    tokens = re.split(r"[^A-Za-zÀ-ÖØ-öø-ÿ]+", text)
    words = []
    for t in tokens:
        w = t.strip().lower()
        if len(w) < 3 or w in stop:
            continue
        words.append(w)
    return words

def process_interaction(audio_file, target_language, mode, scenario, base_language="English", stream=False) -> Generator[Tuple[Any, str, str, str, Any, str], None, None]:
    """
    Generator yielding incremental updates if stream=True.
    Yields tuples for components: (chatbot, user_transcript, translation, extras, tts_audio, stats)
    When stream=False, yields once.
    """
    if not audio_file:
        chat_display: List[List[str]] = []
        stats = _format_stats()
        yield chat_display, "No audio provided", "", "", None, stats
        return

    # Transcribe user speech
    transcription = transcriber.transcribe(audio_file, language_hint=None)
    user_text = transcription["text"]

    # Attempt detect base language if user speaks target language
    try:
        detected_lang = detect(user_text)
    except Exception:
        detected_lang = "unknown"

    STATE["turn"] += 1
    progress_store.increment_turn()

    # Build / refresh system prompt once at start
    if STATE["turn"] == 1:
        system_prompt = build_system_prompt(base_language, target_language, mode, scenario, STATE["turn"])
        STATE["history"].append({"role": "system", "content": system_prompt})
    else:
        # Minimal update system prompt each turn (optional: could adjust turn_number)
        pass

    # Add user message
    STATE["history"].append({"role": "user", "content": user_text})

    response_text = ""
    if stream:
        for c in ollama_client.chat(STATE["history"], stream=True):
            response_text += c
            # Build temporary chat display with partial assistant content
            temp_history = STATE["history"] + [{"role": "assistant", "content": response_text}]
            chat_display = _history_to_chat(temp_history)
            stats = _format_stats()
            # yield partial; other boxes empty until final
            yield chat_display, user_text, "(streaming...)", "", None, stats
        # After streaming completes proceed to final parsing
    else:
        response_text = ollama_client.chat(STATE["history"], stream=False)

    STATE["history"].append({"role": "assistant", "content": response_text})

    target_section, translation_section, alternatives_section, corrections_section, tip_section = _parse_sections(response_text)

    # Track corrections count
    corrections_count = 0
    if corrections_section:
        # count lines that look like corrections (start with '-' or contain '->')
        for line in corrections_section.splitlines():
            if line.strip() and (line.strip().startswith("-") or "->" in line):
                corrections_count += 1
    if corrections_count:
        progress_store.add_corrections(corrections_count)

    # Vocabulary extraction from target section
    vocab_words = set(_extract_vocabulary(target_section))
    if vocab_words:
        progress_store.add_vocabulary(vocab_words)

    # Synthesize TTS audio for target section
    audio_path = synthesize_text(target_language, target_section) if target_section else None

    # Build display
    chat_display = _history_to_chat(STATE["history"])
    stats = _format_stats()
    extras_combined = alternatives_section + ("\n" + corrections_section if corrections_section else "")
    yield chat_display, user_text, translation_section, extras_combined, audio_path, stats


def _history_to_chat(history: List[Dict[str, str]]) -> List[List[str]]:
    chat_display: List[List[str]] = []
    pending_user = None
    for msg in history:
        role = msg.get("role")
        content = msg.get("content", "")
        if role == "system":
            continue
        if role == "user":
            pending_user = content
        elif role == "assistant" and pending_user is not None:
            chat_display.append([pending_user, content])
            pending_user = None
    return chat_display

def _parse_sections(response_text: str):
    target_section = ""; translation_section = ""; alternatives_section = ""; corrections_section = ""; tip_section = ""
    lines = [l.strip() for l in response_text.splitlines() if l.strip()]
    current_key = None
    collector = {"TARGET": [], "EN": [], "ALTERNATIVES": [], "CORRECTIONS": [], "TIP": []}
    for line in lines:
        upper = line.upper()
        if upper.startswith("TARGET:"):
            current_key = "TARGET"; collector[current_key].append(line.split("TARGET:",1)[1].strip()); continue
        if upper.startswith("EN:"):
            current_key = "EN"; collector[current_key].append(line.split("EN:",1)[1].strip()); continue
        if upper.startswith("ALTERNATIVES"):
            current_key = "ALTERNATIVES"; continue
        if upper.startswith("CORRECTIONS"):
            current_key = "CORRECTIONS"; continue
        if "CULTURAL" in upper or "TIP" in upper:
            current_key = "TIP"; collector[current_key].append(line); continue
        if current_key:
            collector[current_key].append(line)
    target_section = "\n".join(collector["TARGET"]).strip()
    translation_section = "\n".join(collector["EN"]).strip()
    alternatives_section = "\n".join(collector["ALTERNATIVES"]).strip()
    corrections_section = "\n".join(collector["CORRECTIONS"]).strip()
    tip_section = "\n".join(collector["TIP"]).strip()
    return target_section, translation_section, alternatives_section, corrections_section, tip_section

def _format_stats():
    top_vocab = progress_store.top_vocabulary(8)
    vocab_str = ", ".join([f"{w}({c})" for w,c in top_vocab]) if top_vocab else "(none yet)"
    return f"Turns: {progress_store.data['turns']} | Corrections: {progress_store.data['corrections']}\nTop vocab: {vocab_str}"


def build_ui():
    with gr.Blocks(title="Travel Language Learning Assistant") as demo:
        gr.Markdown("# 🌍 Travel Language Learning Voice Assistant\nPractice speaking and get instant corrections, translations, and cultural tips.")
        with gr.Row():
            target = gr.Dropdown(SUPPORTED_TARGET_LANGS, value="Spanish", label="Target Language")
            mode = gr.Radio(MODES, value="Conversation", label="Mode")
            scenario = gr.Dropdown(SCENARIOS, value="Restaurant", label="Scenario (if Scenario Mode)")
        audio = gr.Audio(source="microphone", type="filepath", label="Speak and then click 'Transcribe & Chat'")
        with gr.Row():
            stream_checkbox = gr.Checkbox(value=False, label="Stream response")
            submit_btn = gr.Button("Transcribe & Chat", variant="primary")
            reset_btn = gr.Button("Reset Conversation")
        chatbot = gr.Chatbot(label="Conversation")
        user_transcript = gr.Textbox(label="Your Speech (Transcribed)")
        translation_box = gr.Textbox(label="Translation")
        extras_box = gr.Textbox(label="Alternatives / Corrections", lines=6)
        tts_audio = gr.Audio(label="Assistant Voice", autoplay=True)
        stats_box = gr.Textbox(label="Learning Stats", value="Turns: 0 | Corrections: 0\nTop vocab: (none yet)")

        submit_btn.click(
            fn=process_interaction,
            inputs=[audio, target, mode, scenario, gr.Textbox(value="English", visible=False), stream_checkbox],
            outputs=[chatbot, user_transcript, translation_box, extras_box, tts_audio, stats_box]
        )
        reset_btn.click(fn=reset_chat, inputs=None, outputs=[chatbot, user_transcript, translation_box, extras_box])
    return demo

app = build_ui()

if __name__ == "__main__":
    app.launch()
