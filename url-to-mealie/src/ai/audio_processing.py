import json
import subprocess
import uuid

from faster_whisper import WhisperModel
from logger import get_configured_logger

logger = get_configured_logger(__name__)

_whisper_model = None

MOBILE_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"


def get_whisper_model():
    """Lazy initialization of Whisper model"""
    global _whisper_model
    if _whisper_model is None:
        logger.info("Loading Whisper model...")
        _whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")
        logger.info("Whisper model loaded")
    return _whisper_model


def classify_instagram_error(stderr: str) -> str:
    s = (stderr or "").lower()
    if "rate-limit" in s or "rate limit" in s:
        return "rate_limit"
    if "login required" in s or "requested content is not available" in s:
        return "login_required"
    if "private" in s:
        return "private_content"
    if "not available" in s:
        return "content_unavailable"
    return "unknown"


def download_audio(
    url: str, args=["yt-dlp", "-x", "--audio-format", "mp3", "-o"]
) -> str:
    filename = f"/tmp/{uuid.uuid4()}.mp3"
    try:
        subprocess.run(
            args + [filename, url],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        logger.error(f"Error downloading audio: {e.stderr}", exc_info=True)
        if len(args) == 5:
            logger.info("Retrying without audio format specification...")
            return download_audio(
                url,
                args=[
                    "yt-dlp",
                    "-x",
                    "--audio-format",
                    "-o",
                    "--user-agent",
                    MOBILE_UA,
                    "mp3",
                ],
            )
        return None, classify_instagram_error(e.stderr)
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


def fetch_metadata(
    url: str,
    args: list = [
        "yt-dlp",
        "-j",
        "--no-warnings",
    ],
) -> dict:
    """Download metadata from Social Media video."""
    try:
        result = subprocess.run(
            args + [url],
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error downloading audio: {e.stderr}", exc_info=True)
        if len(args) == 3:
            logger.info("Retrying without audio format specification...")
            return download_audio(
                url,
                args=[
                    "yt-dlp",
                    "-x",
                    "--audio-format",
                    "mp3",
                    "--user-agent",
                    MOBILE_UA,
                    "-o",
                ],
            )
        return None, classify_instagram_error(e.stderr)
    return None
