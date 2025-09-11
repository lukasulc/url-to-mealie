import json
import os
import subprocess
from datetime import datetime
from typing import Annotated

import requests
from ai.audio_processing import download_audio, transcribe_audio
from ai.recipe_parser import create_prompt, naive_parse, smart_parse
from fastapi import FastAPI, Form, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.requests import Request
from fastapi.responses import HTMLResponse
from logger import get_configured_logger
from templates.templates import (
    get_error_page,
    get_exception_page,
    get_homepage,
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

MEALIE_BASE_URL = os.getenv("MEALIE_BASE_URL", "").rstrip("/")
MEALIE_STATIC_URL = os.getenv("MEALIE_STATIC_URL", MEALIE_BASE_URL).rstrip("/")
MEALIE_TOKEN = os.getenv("MEALIE_TOKEN")
MEALIE_URL = f"{MEALIE_BASE_URL}/api/recipes" if MEALIE_BASE_URL else ""


def fetch_metadata(url: str) -> dict:
    """Download metadata from Social Media video."""
    result = subprocess.run(
        ["yt-dlp", "-j", url], capture_output=True, text=True, check=True
    )
    return json.loads(result.stdout)


def fetch_thumbnail(metadata: dict) -> str:
    """Get thumbnail from video metadata."""
    thumbnail_url = metadata.get("thumbnail")
    if not thumbnail_url:
        logger.warning("No thumbnail found in metadata")
        return None
    return thumbnail_url


def send_recipe_to_mealie(recipe: dict):
    """Send recipe to Mealie API.

    Args:
        recipe (dict): Recipe data to send

    Returns:
        dict: Response from Mealie API

    Raises:
        HTTPException: If there's an error communicating with Mealie
    """

    logger.info(f"Sending recipe to Mealie at {MEALIE_BASE_URL}")

    try:
        recipe_json_str = json.dumps(recipe)
        request_body = {"includeTags": False, "data": recipe_json_str}

        headers = {
            "Authorization": f"Bearer {MEALIE_TOKEN}",
            "Content-Type": "application/json",
        }
        r = requests.post(
            f"{MEALIE_URL}/create/html-or-json", headers=headers, json=request_body
        )
        r.raise_for_status()
        return r.json()

    except requests.exceptions.ConnectionError:
        error_msg = f"Could not connect to Mealie at {MEALIE_BASE_URL}. Please check the URL and ensure Mealie is running."
        logger.error(error_msg)
        raise HTTPException(status_code=503, detail=error_msg)

    except requests.exceptions.HTTPError as e:
        error_msg = f"Mealie API error: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=e.response.status_code, detail=error_msg)


def set_recipe_thumbnail(slug: str, thumbnail_url: str):
    """Set recipe thumbnail in Mealie.

    Args:
        slug (str): Recipe slug/ID
        thumbnail_url (str): URL of the thumbnail image

    Returns:
        dict: Response from Mealie API

    Raises:
        HTTPException: If there's an error communicating with Mealie
    """

    try:
        request_body = {"includeTags": True, "url": thumbnail_url}

        headers = {
            "Authorization": f"Bearer {MEALIE_TOKEN}",
            "Content-Type": "application/json",
        }
        r = requests.post(
            f"{MEALIE_URL}/{slug}/image", headers=headers, json=request_body
        )
        r.raise_for_status()
        return r.json()

    except requests.exceptions.ConnectionError:
        error_msg = f"Could not connect to Mealie at {MEALIE_BASE_URL}. Please check the URL and ensure Mealie is running."
        logger.error(error_msg)
        raise HTTPException(status_code=503, detail=error_msg)

    except requests.exceptions.HTTPError as e:
        error_msg = f"Mealie API error: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=e.response.status_code, detail=error_msg)


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
    try:
        logger.debug("Fetching video metadata...")
        metadata = fetch_metadata(url)
        caption = metadata.get("description", "")
        logger.info(f"Caption length: {len(caption)} characters.")

        logger.debug("Downloading audio...")
        audio = download_audio(url)
        logger.debug("Transcribing audio...")
        transcribed_text = transcribe_audio(audio)
        logger.info(f"Transcription length: {len(transcribed_text)} characters.")

        try:
            logger.debug("Parsing recipe using LLM")
            recipe = smart_parse(create_prompt(caption, transcribed_text))
        except Exception as e:
            logger.error(
                f"Error parsing recipe with LLM: {e}. Falling back to naive parser.",
                exc_info=True,
            )
            recipe = naive_parse(transcribed_text)

        logger.info(
            f"Parsed recipe: {len(recipe['recipeIngredient'])} ingredients, "
            f"{len(recipe['recipeInstructions'])} instructions"
        )
        logger.debug(f"Recipe data: {recipe}")

        logger.debug("Sending recipe to Mealie")
        recipe["orgURL"] = url
        recipe["description"] = (
            recipe.get("description", "") + f"**[ORIGINAL CAPTION]**{caption}"
        )
        result = send_recipe_to_mealie(recipe)

        thumbnail_url = fetch_thumbnail(metadata)
        if thumbnail_url:
            logger.debug(f"Setting recipe thumbnail in Mealie. URL: {thumbnail_url}")
            set_recipe_thumbnail(result, thumbnail_url)

        logger.info(f"Recipe added successfully with ID: {result}")

        app_state["recipes_processed"] += 1
        app_state["last_error"] = None

        recipe_url = f"{MEALIE_STATIC_URL}/g/home/r/{result}"

        return get_success_page(recipe_url, recipe.get("name", "Recipe"), app_state)

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


def main():
    validate_mealie_config(MEALIE_TOKEN, MEALIE_BASE_URL)
    """Main entry point for the application."""
    if not MEALIE_TOKEN:
        logger.error("MEALIE_TOKEN environment variable is not set!")

    if not MEALIE_BASE_URL:
        logger.error("MEALIE_BASE_URL environment variable is not set!")


if __name__ == "__main__":
    main()
