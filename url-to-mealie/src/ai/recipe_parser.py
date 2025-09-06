import json
import os
from llama_cpp import Llama
from pathlib import Path
from logger import get_configured_logger

logger = get_configured_logger(__name__)

MODEL_DIR = Path(
    os.getenv(
        "MODEL_DIR", Path(Path(__file__).parts[0]) / f"{Path(__file__).parts[1]}/models"
    )
)
MODEL_PATH = MODEL_DIR / "parsing_model.gguf"

MODEL_DIR.mkdir(parents=True, exist_ok=True)

_llm = None


def get_llm() -> Llama:
    """Lazy initialization of the LLM to avoid loading it until needed."""
    global _llm
    if _llm is None:
        if not MODEL_PATH.exists():
            raise RuntimeError(
                f"Model not found at {MODEL_PATH}. Please download the GGUF format model "
                "from https://huggingface.co/"
            )
        _llm = Llama(
            model_path=str(MODEL_PATH),
            n_ctx=4096,
            n_threads=max(1, os.cpu_count() // 2),
            n_gpu_layers=-1,
            n_batch=8,
            low_vram=True,
            offload_kqv=True,
        )

    return _llm


SYSTEM_PROMPT = """You are a recipe parsing assistant. Your task is to carefully extract and format recipe information.

IMPORTANT RULES:
0. Always use English language and translate to English
1. Check spelling carefully for each word
2. Separate ingredients properly with commas
3. Use proper spacing between words
4. Format measurements consistently (e.g., "1 tsp", "2 tablespoons")
5. Each ingredient should be a complete, understandable phrase
6. Each instruction should be a complete sentence
7. Double-check the recipe name for accuracy
8. Use JSON format for the output, making sure it's valid and formatted correctly

Extract and format the following information:
1. Recipe name (clear and properly spelled)
2. List of ingredients (each with quantity and unit)
3. Step-by-step instructions that contain specific actions from the context of the Transcribed Audio (clear, complete sentences)
4. Servings/yield (if mentioned)
5. Total time (if mentioned)

Format the response EXACTLY as this JSON schema:
{
    "name": "Recipe Name Here",
    "recipeYield": "Serves X",
    "totalTime": "X minutes",
    "recipeIngredient": [
        "1 cup ingredient one",
        "2 tsp ingredient two"
    ],
    "recipeInstructions": [
        {"text": "Step one instruction."},
        {"text": "Step two instruction."}
    ]
}

If any field is not clearly present in the input, omit it from the JSON output.
Double-check your response for spelling and formatting before returning.

RETURN ONLY THE AFFOREMENTIONED JSON SCHEMA AND NOTHING ELSE."""


def create_prompt(caption: str, transcription: str) -> str:
    """Combine caption and transcription into a single prompt."""
    return f"""Parse this recipe information into structured data.

This is the caption of the video, use it to get the exact ingredients and quantities:
{caption}

This is the Transcribed Audio. Use this to create recipe instructions:
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

        if parsed.get("recipeIngredient") and parsed.get("recipeInstructions"):
            validated = parsed  # TODO: Add validation here
            logger.debug(f"Validated JSON: {validated}")
            return validated

    raise ValueError("Invalid or empty recipe structure")


def smart_parse(prompt: str) -> dict:
    """
    Parse recipe information using llama.cpp.
    Combines information from both caption and transcribed audio.
    Falls back to naive parsing if LLM parsing fails.
    """

    llm = get_llm()

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

    response = llm.create_chat_completion(
        messages=messages, temperature=0.1, top_p=0.1, repeat_penalty=1.2, stream=False
    )

    response_text = response["choices"][0]["message"]["content"]
    logger.debug(f"LLM Response: {response_text}")

    parsed = parse_llm_response(response_text)

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
