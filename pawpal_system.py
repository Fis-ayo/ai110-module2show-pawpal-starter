from dataclasses import dataclass, field
from enum import Enum


class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: Priority
    is_completed: bool = False

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.is_completed = True

    def to_dict(self) -> dict:
        """Return task data as a serializable dictionary."""
        return {
            "title": self.title,
            "duration_minutes": self.duration_minutes,
            "priority": self.priority.name,
            "is_completed": self.is_completed,
        }


@dataclass
class Pet:
    name: str
    species: str  # "dog", "cat", "other"
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to this pet's task list."""
        self.tasks.append(task)

    def get_tasks_by_priority(self) -> list[Task]:
        """Return incomplete tasks sorted from highest to lowest priority."""
        return sorted(
            (t for t in self.tasks if not t.is_completed),
            key=lambda t: t.priority.value,
            reverse=True,
        )


@dataclass
class Owner:
    name: str
    available_minutes: int
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's pet list."""
        self.pets.append(pet)

    def get_all_tasks(self) -> list[Task]:
        """Return a flat list of all tasks across every pet."""
        return [task for pet in self.pets for task in pet.tasks]


class Schedule:
    def __init__(self):
        self.scheduled_tasks: list[Task] = []
        self.total_duration: int = 0
        self.explanations: list[tuple[Task, str]] = []

    def add_entry(self, task: Task, reason: str) -> None:
        """Add a task and its scheduling reason to the schedule."""
        self.scheduled_tasks.append(task)
        self.explanations.append((task, reason))
        self.total_duration += task.duration_minutes

    def display(self) -> str:
        """Format and return the full schedule as a readable string."""
        lines = []
        for task, reason in self.explanations:
            lines.append(
                f"- {task.title} ({task.duration_minutes} min)"
                f" [{task.priority.name}]: {reason}"
            )
        lines.append(f"Total time: {self.total_duration} min")
        return "\n".join(lines)


class Scheduler:
    def __init__(self, owner: Owner) -> None:
        self.owner = owner

    def get_all_tasks(self, pet: Pet) -> list[Task]:
        """Return all incomplete tasks for a pet, sorted by priority."""
        return pet.get_tasks_by_priority()

    def generate_schedule(self, pet: Pet) -> Schedule:
        """Build a Schedule by greedily fitting tasks within the owner's available time."""
        schedule = Schedule()
        remaining = self.owner.available_minutes

        for task in pet.get_tasks_by_priority():
            if task.duration_minutes <= remaining:
                reason = (
                    f"Priority: {task.priority.name} | "
                    f"Fits within available time ({remaining} min left)"
                )
                schedule.add_entry(task, reason)
                remaining -= task.duration_minutes

        return schedule

    def summary(self, schedule: Schedule, pet: Pet) -> str:
        """Return a formatted summary of the schedule for a given owner and pet."""
        lines = [
            f"Owner: {self.owner.name}",
            f"Pet: {pet.name}",
            f"Tasks scheduled: {len(schedule.scheduled_tasks)}",
            f"Total duration: {schedule.total_duration} min",
            "",
            schedule.display(),
        ]
        return "\n".join(lines)
