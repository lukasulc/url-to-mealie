import json
import logging
import os
import queue
import threading
from typing import Any, Dict, Optional

import requests
from ai.recipe_parser import naive_parse
from ai.task import Task, TaskStatus
from logger import get_configured_logger
from recipe.mealie import llm_response_to_mealie, update_recipe

logger = get_configured_logger(__name__)

LLM_SERVER_URL = os.getenv("LLM_SERVER_URL", "http://llm:6998")
RESPONSE_TIMEOUT = int(os.getenv("LLM_RESPONSE_TIMEOUT", 600))


class LLMTaskQueue:
    def __init__(
        self,
        prompt_path=os.path.join(
            os.path.dirname(__file__), "prompts", "system_prompt_2.txt"
        ),
    ):
        self.task_queue: queue.Queue[Task] = queue.Queue()
        self.current_task: Optional[Task] = None

        self.worker = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker.start()

        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                self.system_prompt = f.read()
        except FileNotFoundError as e:
            logger.error(f"System prompt file not found: {e}")
            raise FileNotFoundError("System prompt file not found")
        except Exception as e:
            logger.error(f"Error loading system prompt: {e}")
            self.system_prompt = "You are a helpful assistant."

    def submit_task(self, task: Task) -> queue.Queue[Task]:
        """Add a URL to the processing queue"""

        task.queue_position = self.task_queue.unfinished_tasks + 1
        self.task_queue.put(task)

        return self.task_queue

    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        q_status = {
            "queue_count": self.task_queue.unfinished_tasks,
            "queued_tasks": list(self.task_queue.queue),
            "currently_processing": (self.current_task if self.current_task else None),
        }
        return q_status

    def _worker_loop(self):
        """Main worker loop - processes one LLM task at a time"""
        while True:
            self.current_task = self.task_queue.get()

            try:
                if self.current_task.recipe_slug and self.current_task.context:

                    # Update recipe with transcription
                    recipe = {
                        "description": (
                            f"{self.current_task.original_caption}\n\n"
                            "[Status: Transcription successful - Processing with LLM...]"
                        ),
                        "recipeIngredient": naive_parse(
                            self.current_task.context.transcription
                        ).get("recipeIngredient", []),
                        "recipeInstructions": naive_parse(
                            self.current_task.context.transcription
                        ).get("recipeInstructions", []),
                    }
                    update_recipe(self.current_task.recipe_slug, recipe)

                # Process with LLM
                response = self._process_llm_task(self.current_task)
                self.current_task.status = TaskStatus.SAVING
                llm_response_to_mealie(self.current_task, response)
                self.current_task.status = TaskStatus.COMPLETED
            except Exception as e:
                logger.error(f"Error processing {self.current_task.url}: {e}")
                self.current_task.status = TaskStatus.FAILED
                self.current_task.error = str(e)
            finally:
                # Remove from queue list when done (success or failure)
                self.task_queue.task_done()

    def _process_llm_task(self, task: Task):
        """Your LLM processing logic"""
        logging.info(f"Starting LLM processing for: {task.url}")

        if not task.context or not task.context.prompt:
            raise ValueError("Task context or prompt is missing")

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": task.context.prompt},
        ]

        response = self._call_llm_server(messages)
        logging.debug(f"LLM response: {response}")

        logging.info(f"Finished LLM processing for: {task.url}")
        return response

    def _call_llm_server(
        self, messages: list, with_schema: bool = False
    ) -> dict[str, Any]:
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
            raise LLMServerRequestError(f"Failed to get response from LLM server: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from LLM server: {e}")
            raise LLMServerRequestError(f"Invalid JSON response from LLM server: {e}")


class LLMServerRequestError(Exception):
    """Custom exception for LLM server request errors."""

    pass


def create_prompt(caption: str, transcription: str) -> str:
    """Combine caption and transcription into a single prompt."""
    return f"""Parse this recipe information into structured data.

This is the caption of the video, use it to get the exact ingredients and quantities:
{caption}

This is the Transcribed Audio. Use this to deduce what the recipe instructions are:
{transcription}

Extract all recipe information and return it in JSON format as specified."""


def load_json_schema(schema_file_name: str) -> dict:
    """Load the JSON schema for recipe parsing."""
    schema_path = os.path.join(os.path.dirname(__file__), schema_file_name)
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)
