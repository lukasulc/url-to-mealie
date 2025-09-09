import json
import os
import requests
from logger import get_configured_logger

logger = get_configured_logger(__name__)

LLM_SERVER_URL = os.getenv("LLM_SERVER_URL", "http://llm:6998")
RESPONSE_TIMEOUT = int(os.getenv("LLM_RESPONSE_TIMEOUT", 600))


def load_json_schema(schema_file_name: str) -> dict:
    """Load the JSON schema for recipe parsing."""
    schema_path = os.path.join(os.path.dirname(__file__), schema_file_name)
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def call_llm_server(messages: list, with_schema: bool = False) -> dict:
    """Make a request to the llama.cpp server for chat completion."""
    try:
        response = requests.post(
            f"{LLM_SERVER_URL}/v1/chat/completions",
            json={
                "messages": messages,
                "temperature": 0.1,
                "top_p": 0.1,
                "repeat_penalty": 1.2,
                "stream": False,
                "json_schema": (
                    load_json_schema("recipe_schema.json") if with_schema else None
                ),
            },
            timeout=RESPONSE_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling LLM server: {e}")
        raise RuntimeError(f"Failed to get response from LLM server: {e}")


def create_prompt(caption: str, transcription: str) -> str:
    """Combine caption and transcription into a single prompt."""
    return f"""Parse this recipe information into structured data.

This is the caption of the video, use it to get the exact ingredients and quantities:
{caption}

This is the Transcribed Audio. Use this to deduce what the recipe instructions are:
{transcription}

Extract all recipe information and return it in JSON format as specified."""


def parse_llm_response(response: str) -> dict:
    """
    Extract the JSON object from the LLM response.
    Falls back to naive parsing if JSON parsing fails.
    """
    response = response.replace("```json", "").replace("```", "")
    response = (
        response.replace("”", '"').replace("“", '"').replace("’", "'").replace("‘", "'")
    )
    logger.debug(f"Response after cleanup: {response}")

    start = response.find("{")
    end = response.rfind("}") + 1
    if start >= 0 and end > start:
        json_str = response[start:end]
        parsed = json.loads(json_str)
        logger.debug(f"Parsed loads JSON: {parsed}")

        validated = parsed  # TODO: Add validation here
        logger.debug(f"Validated JSON: {validated}")
        return validated

    raise ValueError("Invalid or empty recipe structure")


def smart_parse(prompt: str) -> dict:
    """
    Parse recipe information using llama.cpp server.
    Combines information from both caption and transcribed audio.
    Falls back to naive parsing if LLM parsing fails.
    """
    prompt_path = os.path.join(
        os.path.dirname(__file__), "prompts", "system_prompt_2.txt"
    )
    with open(prompt_path, "r", encoding="utf-8") as f:
        SYSTEM_PROMPT = f.read()

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        try:
            response = call_llm_server(messages)
            response_text = response["choices"][0]["message"]["content"]
            logger.debug(f"LLM Response: {response_text}")
            parsed = parse_llm_response(response_text)
        except Exception as e:
            logger.error(f"Error during LLM processing: {e}")
            return naive_parse(prompt)

    if "recipeIngredient" not in parsed:
        parsed["recipeIngredient"] = []
    if "recipeInstructions" not in parsed:
        parsed["recipeInstructions"] = []
    if not isinstance(parsed["recipeInstructions"], list):
        parsed["recipeInstructions"] = [{"text": str(parsed["recipeInstructions"])}]
    elif not all(isinstance(x, dict) for x in parsed["recipeInstructions"]):
        parsed["recipeInstructions"] = [
            {"text": str(x)} for x in parsed["recipeInstructions"]
        ]

    return parsed


def naive_parse(text: str) -> dict:
    """
    Super simple heuristic parser:
    - Lines with numbers -> ingredients
    - Other lines -> instructions
    """
    lines = [line.strip() for line in text.split(".") if line.strip()]
    ingredients = [l for l in lines if any(char.isdigit() for char in l)]
    instructions = [l for l in lines if l not in ingredients]

    return {
        "name": "Recipe from Social Media video",
        "recipeIngredient": ingredients if ingredients else ["See transcription"],
        "recipeInstructions": [{"text": step} for step in instructions],
    }
