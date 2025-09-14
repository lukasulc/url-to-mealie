import json
import os
from typing import Any

import requests
from ai.recipe_parser import naive_parse, smart_parse
from ai.task import Task, TaskStatus
from fastapi import FastAPI, HTTPException  # pyright: ignore[reportMissingImports]
from logger import get_configured_logger

app = FastAPI(title="Recipe Parser API")
logger = get_configured_logger(__name__)

MEALIE_BASE_URL = os.getenv("MEALIE_BASE_URL", "").rstrip("/")
MEALIE_STATIC_URL = os.getenv("MEALIE_STATIC_URL", MEALIE_BASE_URL).rstrip("/")
MEALIE_TOKEN = os.getenv("MEALIE_TOKEN")
MEALIE_URL = f"{MEALIE_BASE_URL}/api/recipes" if MEALIE_BASE_URL else ""


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


def llm_response_to_mealie(task: Task, response: dict[str, Any]):
    try:
        logger.debug("Parsing recipe using LLM")
        recipe = smart_parse(response)
    except Exception as e:
        logger.error(
            f"Error parsing recipe with LLM: {e}. Falling back to naive parser.",
            exc_info=True,
        )
        recipe = naive_parse(task.context.transcription)

    logger.info(
        f"Parsed recipe: {len(recipe['recipeIngredient'])} ingredients, "
        f"{len(recipe['recipeInstructions'])} instructions"
    )
    logger.debug(f"Recipe data: {recipe}")

    task.status = TaskStatus.SAVING
    logger.debug("Sending recipe to Mealie")
    recipe["orgURL"] = task.url
    recipe["description"] = (
        recipe.get("description", "") + f"**[ORIGINAL CAPTION]**{task.context.caption}"
    )
    result = send_recipe_to_mealie(recipe)

    thumbnail_url = task.context.thumbnail
    if thumbnail_url:
        logger.debug(f"Setting recipe thumbnail in Mealie. URL: {thumbnail_url}")
        set_recipe_thumbnail(result, thumbnail_url)

    logger.info(f"Recipe added successfully with ID: {result}")
