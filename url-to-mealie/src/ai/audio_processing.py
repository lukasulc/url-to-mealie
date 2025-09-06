import uuid, subprocess
from logger import get_configured_logger
from faster_whisper import WhisperModel

logger = get_configured_logger(__name__)

_whisper_model = None


def get_whisper_model():
    """Lazy initialization of Whisper model"""
    global _whisper_model
    if _whisper_model is None:
        logger.info("Loading Whisper model...")
        _whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")
        logger.info("Whisper model loaded")
    return _whisper_model


def download_audio(url: str) -> str:
    filename = f"/tmp/{uuid.uuid4()}.mp3"
    subprocess.run(
        ["yt-dlp", "-x", "--audio-format", "mp3", "-o", filename, url], check=True
    )
    return filename


def transcribe_audio(filename: str) -> str:
    try:
        model = get_whisper_model()
        segments, _ = model.transcribe(filename)
        text = " ".join(segment.text for segment in segments)
        return text
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}", exc_info=True)
        raise
