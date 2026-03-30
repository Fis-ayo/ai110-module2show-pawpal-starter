from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str  # "low", "medium", "high"
    is_completed: bool = False

    def to_dict(self) -> dict:
        pass


@dataclass
class Pet:
    name: str
    species: str  # "dog", "cat", "other"
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        pass

    def get_tasks_by_priority(self) -> list[Task]:
        pass


@dataclass
class Owner:
    name: str
    available_minutes: int
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        pass


class Schedule:
    def __init__(self):
        self.scheduled_tasks: list[Task] = []
        self.total_duration: int = 0
        self.explanations: dict[str, str] = {}

    def add_entry(self, task: Task, reason: str) -> None:
        pass

    def display(self) -> str:
        pass


def schedule_tasks(pet: Pet, available_minutes: int) -> Schedule:
    pass
