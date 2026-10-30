"""Consume streamed Ollama chunks and hand off sentences to TTS."""
import time

from jarvis.speech_chunks import SpeechChunker


def consume_response(chunks, *, speak=None, write=None, clock=None):
    """Return metrics. Speak callback is optional and does not select a voice."""
    now = clock or time.perf_counter
    started = now()
    first = None
    text_parts = []
    sentence_count = 0
    splitter = SpeechChunker()
    for chunk in chunks:
        if first is None and chunk:
            first = now() - started
        text_parts.append(chunk)
        if write is not None:
            write(chunk)
        for sentence in splitter.feed(chunk):
            sentence_count += 1
            if speak is not None:
                speak(sentence)
    for sentence in splitter.flush():
        sentence_count += 1
        if speak is not None:
            speak(sentence)
    return {"text": "".join(text_parts), "first_chunk_seconds": first,
            "total_seconds": now() - started, "sentences": sentence_count}
