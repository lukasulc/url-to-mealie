import os
from functools import wraps
from typing import Any, Callable, TypeVar
from urllib.parse import urlparse

import requests
from ai.recipe_parser import naive_parse, smart_parse
from ai.task import Task, TaskStatus
from fastapi import FastAPI, HTTPException  # pyright: ignore[reportMissingImports]
from logger import get_configured_logger
from requests.exceptions import (
    ConnectionError,
    HTTPError,
    InvalidJSONError,
    Timeout,
    TooManyRedirects,
)

app = FastAPI(title="Recipe Parser API")
logger = get_configured_logger(__name__)

MEALIE_BASE_URL = os.getenv("MEALIE_BASE_URL", "").rstrip("/")
MEALIE_STATIC_URL = os.getenv("MEALIE_STATIC_URL", MEALIE_BASE_URL).rstrip("/")
MEALIE_TOKEN = os.getenv("MEALIE_TOKEN")
MEALIE_RECIPE_URL = f"{MEALIE_BASE_URL}/api/recipes" if MEALIE_BASE_URL else ""
CREATE_NEW_FOOD_AND_UNIT = os.getenv("CREATE_NEW_FOOD_AND_UNIT")


# Custom exceptions
class MealieConfigError(Exception):
    """Raised when Mealie configuration is invalid"""

    pass


class RecipeValidationError(Exception):
    """Raised when recipe data validation fails"""

    pass


class ImageProcessingError(Exception):
    """Raised when there's an error processing recipe images"""

    pass


T = TypeVar("T")


def handle_mealie_errors(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to handle common Mealie API errors consistently.

    Handles:
    - Connection errors (server down, network issues)
    - Authentication errors
    - Rate limiting
    - Invalid data
    - Server errors
    - Timeouts
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            # Validate Mealie configuration
            if not MEALIE_TOKEN or not MEALIE_BASE_URL:
                raise MealieConfigError(
                    "Mealie configuration is incomplete. Check MEALIE_TOKEN and MEALIE_BASE_URL."
                )

            # Validate base URL format
            parsed_url = urlparse(MEALIE_BASE_URL)
            if not all([parsed_url.scheme, parsed_url.netloc]):
                raise MealieConfigError(f"Invalid Mealie base URL: {MEALIE_BASE_URL}")

            return func(*args, **kwargs)

        except ConnectionError:
            error_msg = f"Could not connect to Mealie at {MEALIE_BASE_URL}. Please check the URL and ensure Mealie is running."
            logger.error(error_msg)
            raise HTTPException(status_code=503, detail=error_msg)

        except Timeout:
            error_msg = f"Request to Mealie timed out after {os.getenv('REQUEST_TIMEOUT', '30')} seconds"
            logger.error(error_msg)
            raise HTTPException(status_code=504, detail=error_msg)

        except HTTPError as e:
            status_code = getattr(e.response, "status_code", 500)
            if status_code == 401:
                error_msg = "Invalid or expired Mealie API token"
            elif status_code == 429:
                error_msg = "Too many requests to Mealie API"
            elif status_code == 404:
                error_msg = "Recipe or resource not found in Mealie"
            else:
                error_msg = f"Mealie API error: {str(e)}"
            logger.error(error_msg)
            raise HTTPException(status_code=status_code, detail=error_msg)

        except InvalidJSONError:
            error_msg = "Invalid JSON response from Mealie API"
            logger.error(error_msg)
            raise HTTPException(status_code=502, detail=error_msg)

        except TooManyRedirects:
            error_msg = "Too many redirects while connecting to Mealie"
            logger.error(error_msg)
            raise HTTPException(status_code=502, detail=error_msg)

        except MealieConfigError as e:
            logger.error(str(e))
            raise HTTPException(status_code=500, detail=str(e))

        except RecipeValidationError as e:
            logger.error(f"Recipe validation failed: {e}")
            raise HTTPException(status_code=400, detail=str(e))

        except ImageProcessingError as e:
            logger.error(f"Image processing failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

        except Exception as e:
            logger.error(f"Unexpected error in Mealie operation: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Internal server error")

    return wrapper


@handle_mealie_errors
def send_recipe_to_mealie(recipe_name: str) -> str:
    """Send recipe to Mealie API.

    Args:
        recipe_name (str): Recipe data to send

    Returns:
        slug: Response from Mealie API

    Raises:
        HTTPException: If there's an error communicating with Mealie
        MealieConfigError: If Mealie is not properly configured
        RecipeValidationError: If recipe data is invalid
    """
    logger.info(f"Sending recipe to Mealie at {MEALIE_BASE_URL}: {recipe_name}")

    headers = {
        "Authorization": f"Bearer {MEALIE_TOKEN}",
        "Content-Type": "application/json",
    }
    r = requests.post(
        f"{MEALIE_RECIPE_URL}", headers=headers, json={"name": recipe_name}
    )
    r.raise_for_status()
    return r.json()


@handle_mealie_errors
def set_recipe_thumbnail(slug: str, thumbnail_url: str) -> dict:
    """Set recipe thumbnail in Mealie.

    Args:
        slug (str): Recipe slug/ID
        thumbnail_url (str): URL of the thumbnail image

    Returns:
        dict: Response from Mealie API

    Raises:
        HTTPException: If there's an error communicating with Mealie
        MealieConfigError: If Mealie is not properly configured
        ImageProcessingError: If there's an error processing the image
    """
    request_body = {"includeTags": True, "url": thumbnail_url}

    headers = {
        "Authorization": f"Bearer {MEALIE_TOKEN}",
        "Content-Type": "application/json",
    }
    r = requests.post(
        f"{MEALIE_RECIPE_URL}/{slug}/image", headers=headers, json=request_body
    )
    r.raise_for_status()
    return r.json()


@handle_mealie_errors
def get_recipe(slug: str) -> dict:
    """Get an existing recipe from Mealie.

    Args:
        slug (str): Recipe slug/ID

    Returns:
        dict: The recipe data

    Raises:
        HTTPException: If there's an error communicating with Mealie
    """
    headers = {
        "Authorization": f"Bearer {MEALIE_TOKEN}",
        "Content-Type": "application/json",
    }
    r = requests.get(f"{MEALIE_RECIPE_URL}/{slug}", headers=headers)
    r.raise_for_status()
    return r.json()


@handle_mealie_errors
def update_recipe(slug: str, recipe_updates: dict) -> dict:
    """Update an existing recipe in Mealie.

    Args:
        slug (str): Recipe slug/ID
        recipe_updates (dict): Fields to update in the recipe

    Returns:
        dict: Updated recipe data

    Raises:
        HTTPException: If there's an error communicating with Mealie
        MealieConfigError: If Mealie is not properly configured
        RecipeValidationError: If recipe data is invalid
    """
    # Get current recipe and update only specified fields
    recipe = get_recipe(slug)
    recipe.update(recipe_updates)

    logger.debug(f"Recipe after update: {recipe}")

    headers = {
        "Authorization": f"Bearer {MEALIE_TOKEN}",
        "Content-Type": "application/json",
    }
    r = requests.put(f"{MEALIE_RECIPE_URL}/{slug}", headers=headers, json=recipe)
    r.raise_for_status()
    return r.json()


def process_parsed_ingredients(parsed_ingredient: dict):
    headers = {
        "Authorization": f"Bearer {MEALIE_TOKEN}",
        "Content-Type": "application/json",
    }
    ingredient = parsed_ingredient["ingredient"]
    ingredient["note"] = parsed_ingredient["input"]
    ingredient["display"] = parsed_ingredient["input"]
    if ingredient["food"] and ingredient["food"]["id"] is None:
        logger.debug(f"Food not in database: {ingredient}")
        if CREATE_NEW_FOOD_AND_UNIT:
            r = requests.post(
                f"{MEALIE_BASE_URL}/api/foods",
                headers=headers,
                json=ingredient["food"],
            )
            logger.debug(f"Created new food: {r.json()}")
            ingredient["food"]["id"] = r.json().get("id")
        else:
            del ingredient["food"]
    if ingredient["unit"] and ingredient["unit"]["id"] is None:
        logger.debug(f"Unit not in database: {ingredient}")
        if CREATE_NEW_FOOD_AND_UNIT:
            r = requests.post(
                f"{MEALIE_BASE_URL}/api/units",
                headers=headers,
                json=ingredient["unit"],
            )
            logger.debug(f"Created new unit: {r.json()}")
            ingredient["unit"]["id"] = r.json().get("id")
        else:
            del ingredient["unit"]
    return ingredient


@handle_mealie_errors
def mealie_parse_ingredients(recipe_ingredients: list[str]) -> list[dict]:
    headers = {
        "Authorization": f"Bearer {MEALIE_TOKEN}",
        "Content-Type": "application/json",
    }
    r = requests.post(
        f"{MEALIE_BASE_URL}/api/parser/ingredients",
        headers=headers,
        json={"ingredients": recipe_ingredients},
    )
    r.raise_for_status()
    return list(map(lambda v: process_parsed_ingredients(v), r.json()))


@handle_mealie_errors
def llm_response_to_mealie(task: Task, response: dict[str, Any]) -> None:
    """Process LLM response and update recipe in Mealie.

    Args:
        task (Task): Task containing recipe context and metadata
        response (dict[str, Any]): LLM response with recipe information

    Raises:
        HTTPException: If there's an error communicating with Mealie
        MealieConfigError: If Mealie is not properly configured
        RecipeValidationError: If recipe data is invalid
    """
    if not task.context or not task.recipe_slug:
        raise RecipeValidationError("Task context or recipe_slug missing")

    try:
        logger.debug("Parsing recipe using LLM")
        recipe = smart_parse(response)
    except Exception as e:
        logger.warning(
            f"Error parsing recipe with LLM: {e}. Falling back to naive parser.",
            exc_info=True,
        )
        recipe = naive_parse(task.context.transcription)

    if not recipe.get("recipeIngredient") and not recipe.get("recipeInstructions"):
        logger.warning("No ingredients or instructions found in parsed recipe")

    logger.info(
        f"Parsed recipe: {len(recipe.get('recipeIngredient', []))} ingredients, "
        f"{len(recipe.get('recipeInstructions', []))} instructions"
    )
    logger.debug(f"Recipe data: {recipe}")
    ingredients = mealie_parse_ingredients(recipe.get("recipeIngredient", []))

    task.status = TaskStatus.SAVING
    logger.debug("Updating recipe in Mealie")

    # Update the existing recipe with the new information
    recipe_updates = {
        "orgURL": task.url,
        "recipeIngredient": ingredients,
        "recipeInstructions": recipe.get("recipeInstructions", []),
        "description": f"**[ORIGINAL CAPTION]**{task.original_caption}\n\n[Status: Processing completed]",
    }
    logger.debug(f"Recipe updates: {recipe_updates}")

    mealie_response = update_recipe(task.recipe_slug, recipe_updates)
    logger.info(f"Recipe updated successfully: {mealie_response}")
