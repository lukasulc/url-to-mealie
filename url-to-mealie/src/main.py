import os
import subprocess
from datetime import datetime
from threading import Thread
from typing import Annotated

import requests
from ai.audio_processing import (
    InstagramError,
    fetch_metadata,
    get_thumbnail,
    process_audio,
)
from ai.llm_task_queue import LLMTaskQueue
from ai.task import Task
from fastapi import FastAPI, Form  # pyright: ignore[reportMissingImports]
from fastapi.exceptions import RequestValidationError  # pyright: ignore
from fastapi.requests import Request  # pyright: ignore[reportMissingImports]
from fastapi.responses import HTMLResponse  # pyright: ignore[reportMissingImports]
from logger import get_configured_logger
from recipe.mealie import send_recipe_to_mealie, set_recipe_thumbnail
from templates.templates import (
    get_error_page,
    get_exception_page,
    get_homepage,
    get_instagram_error,
    get_status_page,
    get_success_page,
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


@app.get("/", response_class=HTMLResponse)
def form(request: Request):
    return get_homepage(
        request,
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
    error_html = (
        f"<div>• {get_exception_page(request, '</div><div>• '.join(messages))}</div>"
    )
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
    request: Request,
    url: Annotated[
        str,
        Form(
            description="Instagram or TikTok video URL",
            example="https://www.instagram.com/p/abc123/",
            pattern=r"^https?:\/\/(www\.)?(instagram\.com\/|tiktok\.com\/|youtube\.com\/|facebook\.com\/).+",
        ),
    ],
    recipeName: Annotated[
        str,
        Form(
            description="Recipe name",
            example="Chocolate Pancake Recipe",
            hint="Only letters and spaces, max 100 characters",
            pattern=r"^[a-zA-Z\s]{1,100}$",
            min_length=1,
            max_length=100,
        ),
    ],
):
    logger.info(f"Processing new recipe '{recipeName}' from URL: {url}")

    task = Task(url=url)
    try:
        logger.debug("Fetching video metadata...")
        try:
            metadata = fetch_metadata(url)
        except InstagramError as error:
            logger.error(f"Error fetching metadata: {error}")
            return get_instagram_error(request, str(error))

        caption: str = metadata.get("description", "")
        caption = caption.replace("-", " ")
        logger.info(f"Caption length: {len(caption)} characters.")

        # Create initial recipe with just the name and caption
        initial_description = f"{caption}\n\n[Status: Recipe created - Processing...]"

        recipe_response = send_recipe_to_mealie(recipeName)

        thumbnail_url = get_thumbnail(metadata)
        if thumbnail_url:
            set_recipe_thumbnail(recipe_response, thumbnail_url)

        task.recipe_slug = recipe_response
        task.original_caption = caption

        Thread(
            target=process_audio,
            daemon=True,
            args=[url, llm_queue, task, caption, metadata],
        ).start()

        app_state["recipes_processed"] += 1
        app_state["last_error"] = None

        recipe_url = f"{MEALIE_STATIC_URL}/g/home/r/{recipe_response}"
        return get_success_page(request, recipe_url, recipeName, app_state)

    except subprocess.CalledProcessError as e:
        error_msg = (
            f"Failed to download video: {e.stderr.decode() if e.stderr else str(e)}"
        )
        logger.error(error_msg)
        return get_error_page(request, error_msg, url)

    except Exception as e:
        logger.error(f"Error processing recipe: {str(e)}", exc_info=True)
        app_state["last_error"] = {
            "time": datetime.now().isoformat(),
            "error": str(e),
            "url": url,
        }
        return get_error_page(request, str(e), url)


@app.get("/status", response_class=HTMLResponse)
def queue_status(
    request: Request,
):
    return get_status_page(request, llm_queue.get_queue_status(), MEALIE_URL)


@app.get("/status/json")
def queue_status_json():
    return llm_queue.get_queue_status()


def main():
    """Main entry point for the application."""
    validate_mealie_config(MEALIE_TOKEN, MEALIE_BASE_URL)


if __name__ == "__main__":
    main()
