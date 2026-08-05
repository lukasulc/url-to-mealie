import json
import os
import subprocess
import tempfile
import uuid
from contextlib import contextmanager

from typing import Optional

import requests
from logger import get_configured_logger
from ai.task import Task, TaskStatus, TaskContext
from ai.llm_task_queue import LLMTaskQueue, create_prompt

logger = get_configured_logger(__name__)

WHISPER_SERVER_URL = f"http://{os.getenv('WHISPER_ARG_HOST', 'localhost')}:{os.getenv('WHISPER_ARG_PORT', '6997')}"
WHISPER_INFERENCE_PATH = "/inference"

MOBILE_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"


class WhisperServerRequestError(Exception):
    """Custom exception for Whisper server request errors."""

    pass


def transcribe_audio(filename: str) -> str:
    try:
        response = call_whisper_server(filename)
        return extract_transcript(response)
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}", exc_info=True)
        raise


def call_whisper_server(filename: str) -> dict:
    """Send an audio file to the containerized whisper.cpp server."""
    try:
        with open(filename, "rb") as audio_file:
            response = requests.post(
                f"{WHISPER_SERVER_URL}{WHISPER_INFERENCE_PATH}",
                files={"file": (os.path.basename(filename), audio_file, "audio/mpeg")},
                data={
                    "temperature": "0.0",
                    "temperature_inc": "0.2",
                    "response_format": "json",
                },
                timeout=1800,
            )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling Whisper server: {e}")
        raise WhisperServerRequestError(
            f"Failed to get transcription from Whisper server: {e}"
        )
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON response from Whisper server: {e}")
        raise WhisperServerRequestError(
            f"Invalid JSON response from Whisper server: {e}"
        )


def extract_transcript(payload: dict) -> str:
    """Extract the transcript text from the Whisper server response."""
    if not isinstance(payload, dict):
        raise WhisperServerRequestError("Unexpected Whisper response format")

    text = payload.get("text")
    if isinstance(text, str) and text.strip():
        return text.strip()

    transcription = payload.get("transcription")
    if isinstance(transcription, str) and transcription.strip():
        return transcription.strip()

    segments = payload.get("segments")
    if isinstance(segments, list):
        texts = []
        for segment in segments:
            if isinstance(segment, dict):
                segment_text = segment.get("text")
                if isinstance(segment_text, str) and segment_text.strip():
                    texts.append(segment_text.strip())
        if texts:
            return " ".join(texts)

    raise WhisperServerRequestError("Unexpected Whisper response format")


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


class InstagramError(Exception):
    pass


def process_audio(
    url: str,
    llm_queue: LLMTaskQueue,
    task: Task,
    caption: str,
    metadata: dict,
):
    try:
        logger.debug("Downloading audio...")
        audio = download_audio(url)

        logger.debug("Transcribing audio...")
        task.status = TaskStatus.TRANSCRIBING
        transcribed_text = transcribe_audio(audio)
        logger.info(f"Transcription length: {len(transcribed_text)} characters.")

        task.status = TaskStatus.GENERATING
        task.context = TaskContext(
            caption=caption,
            transcription=transcribed_text,
            thumbnail=get_thumbnail(metadata),
            prompt=create_prompt(caption, transcribed_text),
        )
        llm_queue.submit_task(task)
    except Exception as e:
        logger.error(f"Background processing error: {str(e)}", exc_info=True)
        task.status = TaskStatus.FAILED
        task.error = str(e)


def download_audio(
    url: str, args=["yt-dlp", "-x", "--audio-format", "mp3", "-o"]
) -> str:
    filename = f"/tmp/{uuid.uuid4()}.mp3"

    with cookies_file_from_env() as cookies_path:
        try:
            subprocess.run(
                args + [filename, url, "--cookies", cookies_path],
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
                        "--user-agent",
                        MOBILE_UA,
                        "mp3",
                        "-o",
                    ],
                )
            raise InstagramError(classify_instagram_error(e.stderr))
        return filename


def fetch_metadata(
    url: str,
    args: list = [
        "yt-dlp",
        "-j",
        "--no-warnings",
    ],
) -> dict:
    """Download metadata from Social Media video."""
    with cookies_file_from_env() as cookies_path:
        try:
            result = subprocess.run(
                args + [url, "--cookies", cookies_path],
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            logger.error(f"Error downloading audio: {e.stderr}", exc_info=True)
            if len(args) == 3:
                logger.info("Retrying without audio format specification...")
                return fetch_metadata(
                    url,
                    args=["yt-dlp", "-j", "--no-warnings", "--user-agent", MOBILE_UA],
                )
            raise InstagramError(classify_instagram_error(e.stderr))

        return json.loads(result.stdout)


def get_thumbnail(metadata: dict) -> str | None:
    """Get thumbnail from video metadata."""
    thumbnail_url = metadata.get("thumbnail")
    if not thumbnail_url:
        logger.warning("No thumbnail found in metadata")
        return None
    return thumbnail_url


@contextmanager
def cookies_file_from_env():
    """
    Create a temporary Netscape cookies.txt from env and yield its path.
    Supports:
      - IG_COOKIES_NETSCAPE (verbatim content)
      - IG_SESSIONID / IG_CSRFTOKEN
      - IG_COOKIE_STRING: "name=value; name2=value2"
    The file is deleted on exit.
    """
    ns_content = os.getenv("IG_COOKIES_NETSCAPE")
    sessionid = os.getenv("IG_SESSIONID")
    csrftoken = os.getenv("IG_CSRFTOKEN")
    cookie_str = os.getenv("IG_COOKIE_STRING")
    domain = ".instagram.com"
    # now = int(time())
    # far-future expiry to satisfy format
    exp = 2147483647

    lines = []
    if ns_content:
        # Use verbatim; ensure it has the required header line
        if not ns_content.lstrip().startswith("# Netscape HTTP Cookie File"):
            ns_content = "# Netscape HTTP Cookie File\n" + ns_content
        content = ns_content
    else:
        lines.append("# Netscape HTTP Cookie File")

        def add_cookie(name, value):
            if value:
                # domain, includeSubdomains, path, secure, expiry, name, value
                lines.append(f"{domain}\tTRUE\t/\tTRUE\t{exp}\t{name}\t{value}")

        if sessionid:
            add_cookie("sessionid", sessionid)
        if csrftoken:
            add_cookie("csrftoken", csrftoken)

        if not sessionid and cookie_str:
            # parse "k=v; k2=v2"
            for part in cookie_str.split(";"):
                if "=" in part:
                    k, v = part.strip().split("=", 1)
                    add_cookie(k.strip(), v.strip())

        content = "\n".join(lines) + "\n"

    tmp = tempfile.NamedTemporaryFile(prefix="ig_cookies_", suffix=".txt", delete=False)
    try:
        tmp.write(content.encode("utf-8"))
        tmp.flush()
        tmp.close()
        yield tmp.name
    finally:
        try:
            os.remove(tmp.name)
        except Exception:
            pass
