from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from typing import Optional


@dataclass
class TaskContext:
    caption: str
    transcription: str
    thumbnail: str | None
    prompt: str


class TaskStatus(str, Enum):
    PROCESSING = "processing before transcription"
    TRANSCRIBING = "transcribing"
    WAITING = "waiting for LLM to have a free slot"
    GENERATING = "LLM is generating"
    SAVING = "saving recipe"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    url: str
    context: TaskContext
    id: int = int(datetime.now().timestamp() * 1000)
    status: TaskStatus = TaskStatus.PROCESSING
    queue_position: int = -1
    started_at: datetime = datetime.now()
    finished_at: datetime = datetime.now()
    error: Optional[str] = None

    def __init__(self, url: str = ""):
        self.url = url

    # Override __repr__ for better logging
    def __repr__(self):
        return f"Task(id={self.id}, url={self.url}, status={self.status}, position={self.queue_position})"

    # Override __str__ for better logging
    def __str__(self):
        return f"Url={self.url}, status={self.status}, position={self.queue_position})"
