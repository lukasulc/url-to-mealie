import importlib
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "url-to-mealie" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload

    def raise_for_status(self):
        return None


class TestMealieIngredientMatching(unittest.TestCase):
    def setUp(self):
        self.requests_module = types.ModuleType("requests")
        self.exceptions_module = types.ModuleType("requests.exceptions")

        class ConnectionError(Exception):
            pass

        class HTTPError(Exception):
            def __init__(self, *args, **kwargs):
                super().__init__(*args)
                self.response = None

        class InvalidJSONError(Exception):
            pass

        class Timeout(Exception):
            pass

        class TooManyRedirects(Exception):
            pass

        setattr(self.exceptions_module, "ConnectionError", ConnectionError)
        setattr(self.exceptions_module, "HTTPError", HTTPError)
        setattr(self.exceptions_module, "InvalidJSONError", InvalidJSONError)
        setattr(self.exceptions_module, "Timeout", Timeout)
        setattr(self.exceptions_module, "TooManyRedirects", TooManyRedirects)

        setattr(self.requests_module, "exceptions", self.exceptions_module)
        setattr(
            self.requests_module,
            "get",
            Mock(
                side_effect=[
                    FakeResponse(
                        [
                            {"id": 7, "name": "salt"},
                            {"id": 12, "name": "olive oil"},
                        ]
                    ),
                    FakeResponse(
                        [
                            {"id": 3, "name": "tbsp"},
                            {"id": 4, "name": "cup"},
                        ]
                    ),
                ]
            ),
        )
        setattr(
            self.requests_module, "post", Mock(return_value=FakeResponse({"id": 99}))
        )
        sys.modules["requests"] = self.requests_module
        sys.modules["requests.exceptions"] = self.exceptions_module

        fastapi_module = types.ModuleType("fastapi")

        class HTTPException(Exception):
            pass

        setattr(fastapi_module, "FastAPI", lambda *args, **kwargs: object())
        setattr(fastapi_module, "HTTPException", HTTPException)
        sys.modules["fastapi"] = fastapi_module

        logger_module = types.ModuleType("logger")
        setattr(logger_module, "get_configured_logger", lambda name: Mock())
        sys.modules["logger"] = logger_module

        ai_module = types.ModuleType("ai")
        recipe_parser_module = types.ModuleType("ai.recipe_parser")
        setattr(recipe_parser_module, "naive_parse", lambda *args, **kwargs: {})
        setattr(recipe_parser_module, "smart_parse", lambda *args, **kwargs: {})
        task_module = types.ModuleType("ai.task")

        class Task:
            pass

        class TaskStatus:
            SAVING = "saving"

        setattr(task_module, "Task", Task)
        setattr(task_module, "TaskStatus", TaskStatus)
        sys.modules["ai"] = ai_module
        sys.modules["ai.recipe_parser"] = recipe_parser_module
        sys.modules["ai.task"] = task_module

        sys.modules.pop("recipe.mealie", None)
        self.mealie = importlib.import_module("recipe.mealie")

    def test_existing_food_and_unit_are_matched_without_creating_new_ones(self):
        parsed_ingredient = {
            "input": "2 tbsp gray salt",
            "ingredient": {
                "food": {"id": None, "name": "gray salt"},
                "unit": {"id": None, "name": "tbsp"},
            },
        }

        processed = self.mealie.process_parsed_ingredients(parsed_ingredient)

        self.assertEqual(processed["food"], {"id": 7, "name": "salt"})
        self.assertEqual(processed["unit"], {"id": 3, "name": "tbsp"})
        self.assertEqual(self.requests_module.post.call_count, 0)

    def test_unmatched_items_are_removed_instead_of_being_created(self):
        parsed_ingredient = {
            "input": "2 pinches mystery spice",
            "ingredient": {
                "food": {"id": None, "name": "mystery spice"},
                "unit": {"id": None, "name": "pinch"},
            },
        }

        processed = self.mealie.process_parsed_ingredients(parsed_ingredient)

        self.assertNotIn("food", processed)
        self.assertNotIn("unit", processed)
        self.assertEqual(self.requests_module.post.call_count, 0)


if __name__ == "__main__":
    unittest.main()
