from pathlib import Path
from typing import Any, Dict

from fastapi import Request
from fastapi.templating import Jinja2Templates

# Initialize Jinja2Templates

templates = Jinja2Templates(directory=str(Path(__file__).parent / "jinja"))


def get_homepage(request: Request, url: str, token: str | None) -> Any:
    """Generate the homepage HTML."""
    mealie_status = "Connected" if token and url else "Not configured"
    status_class = "success" if token and url else "danger"

    return templates.TemplateResponse(
        request=request,
        name="homepage.html",
        context={
            "request": request,
            "url": url,
            "mealie_status": mealie_status,
            "status_class": status_class,
        },
    )


def get_exception_page(request: Request, error_message: str) -> Any:
    """Generate the exception page HTML."""
    return templates.TemplateResponse(
        request=request,
        name="exception.html",
        context={"request": request, "error_message": error_message},
    )


def get_success_page(
    request: Request, recipe_url: str, recipe_name: str, app_state: dict
) -> Any:
    """Generate the success page HTML."""
    return templates.TemplateResponse(
        request=request,
        name="success.html",
        context={
            "request": request,
            "recipe_url": recipe_url,
            "recipe_name": recipe_name,
            "recipes_processed": app_state["recipes_processed"],
        },
    )


def get_error_page(request: Request, error_message: str, url: str) -> Any:
    """Generate the error page HTML."""
    return templates.TemplateResponse(
        request=request,
        name="error.html",
        context={"request": request, "error_message": error_message, "url": url},
    )


def get_instagram_error(
    request: Request, errors: str, suggestions: str | None = None
) -> Any:
    """Generate the Instagram error page HTML."""
    return templates.TemplateResponse(
        request=request,
        name="instagram_error.html",
        context={"request": request, "errors": errors, "suggestions": suggestions},
    )


def get_status_page(request: Request, queue_status: Dict[str, Any], mealie_url) -> Any:
    """Generate the status page HTML."""
    return templates.TemplateResponse(
        request=request,
        name="status.html",
        context={
            "request": request,
            "queue_status": queue_status,
            "mealie_url": mealie_url,
        },
    )
