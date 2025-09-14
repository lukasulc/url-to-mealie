import os
import subprocess
from datetime import datetime
from typing import Annotated

import requests
from ai.audio_processing import (
    download_audio,
    fetch_metadata,
    transcribe_audio,
    InstagramError,
)
from ai.llm_task_queue import LLMTaskQueue, create_prompt
from ai.task import Task, TaskContext, TaskStatus
from fastapi import FastAPI, Form, status  # pyright: ignore[reportMissingImports]
from fastapi.exceptions import (  # pyright: ignore[reportMissingImports]
    RequestValidationError,
)
from fastapi.requests import Request  # pyright: ignore[reportMissingImports]
from fastapi.responses import (  # pyright: ignore[reportMissingImports]
    HTMLResponse,
    RedirectResponse,
)
from logger import get_configured_logger
from templates.templates import (
    get_error_page,
    get_exception_page,
    get_homepage,
    get_instagram_error,
    get_status_page,
)
from validators.config_validator import validate_mealie_config

app = FastAPI(title="Recipe Parser API")
logger = get_configured_logger(__name__)

app_state = {
    "startup_time": None,
    "recipes_processed": 0,
    "last_error": None,
    "model_loaded": False,
}

llm_queue = LLMTaskQueue()

MEALIE_BASE_URL = os.getenv("MEALIE_BASE_URL", ".").rstrip("/")
MEALIE_STATIC_URL = os.getenv("MEALIE_STATIC_URL", MEALIE_BASE_URL).rstrip("/")
MEALIE_TOKEN = os.getenv("MEALIE_TOKEN")
MEALIE_URL = f"{MEALIE_BASE_URL}/api/recipes" if MEALIE_BASE_URL else ""


def get_thumbnail(metadata: dict) -> str | None:
    """Get thumbnail from video metadata."""
    thumbnail_url = metadata.get("thumbnail")
    if not thumbnail_url:
        logger.warning("No thumbnail found in metadata")
        return None
    return thumbnail_url


@app.get("/", response_class=HTMLResponse)
def form():
    return get_homepage(
        MEALIE_URL,
        MEALIE_TOKEN,
    )


@app.on_event("startup")
async def startup_event():
    """Initialize application state and verify dependencies."""
    logger.info("Starting Recipe Parser application")
    app_state["startup_time"] = datetime.now()


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources."""
    logger.info("Shutting down Recipe Parser application")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    messages = []
    for err in errors:
        if "url" in err.get("loc", []):
            messages.append(err["msg"])
    error_html = f"<div>• {get_exception_page('</div><div>• '.join(messages))}</div>"
    return HTMLResponse(content=error_html, status_code=422)


def _normalize_ig_url(url: str) -> str:
    # Resolve share shortlinks and redirect to canonical reel/post URLs
    try:
        r = requests.get(url, allow_redirects=True, timeout=10)
        final = r.url or url
    except Exception:
        final = url
    # Ensure we pass canonical “/reel/” or “/p/” etc. to yt-dlp if found in the Location chain
    return final


@app.post("/submit", response_class=HTMLResponse)
def submit(
    url: Annotated[
        str,
        Form(
            description="Instagram or TikTok video URL",
            example="https://www.instagram.com/p/abc123/",
            pattern=r"^https?:\/\/(www\.)?(instagram\.com\/|tiktok\.com\/|youtube\.com\/).+",
        ),
    ],
):
    logger.info(f"Processing new recipe from URL: {url}")
    # url = _normalize_ig_url(url)
    # logger.debug(f"Normalized URL: {url}")

    task = Task(url=url)
    try:
        logger.debug("Fetching video metadata...")
        try:
            metadata = fetch_metadata(url)
        except InstagramError as error:
            logger.error(f"Error fetching metadata: {error}")
            return get_instagram_error(str(error))

        caption = metadata.get("description", "")
        logger.info(f"Caption length: {len(caption)} characters.")

        logger.debug("Downloading audio...")
        try:
            audio = download_audio(url)
        except InstagramError as error:
            logger.error(f"Error downloading audio: {error}")
            return get_instagram_error(str(error))

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

        app_state["recipes_processed"] += 1
        app_state["last_error"] = None

        return RedirectResponse(url="/status", status_code=status.HTTP_303_SEE_OTHER)
        # recipe_url = f"{MEALIE_STATIC_URL}/g/home/r/{result}"

        # return get_success_page(recipe_url, recipe.get("name", "Recipe"), app_state)

    except subprocess.CalledProcessError as e:
        error_msg = (
            f"Failed to download video: {e.stderr.decode() if e.stderr else str(e)}"
        )
        logger.error(error_msg)
        return get_error_page(error_msg, url)

    except Exception as e:
        logger.error(f"Error processing recipe: {str(e)}", exc_info=True)
        app_state["last_error"] = {
            "time": datetime.now().isoformat(),
            "error": str(e),
            "url": url,
        }
        return get_error_page(str(e), url)


@app.get("/status", response_class=HTMLResponse)
def queue_status():
    return get_status_page(llm_queue.get_queue_status(), MEALIE_URL)


@app.get("/status/json")
def queue_status_json():
    return llm_queue.get_queue_status()


def main():
    """Main entry point for the application."""
    validate_mealie_config(MEALIE_TOKEN, MEALIE_BASE_URL)


if __name__ == "__main__":
    main()
