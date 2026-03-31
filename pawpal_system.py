from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
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
    preferred_time: str = ""      # "HH:MM" format, e.g. "07:30". Empty = no specific time.
    frequency: str = ""           # "" = one-off, "daily" = every day, "weekly" = every 7 days
    recurrence_count: int = 0     # how many times this task has been completed
    due_date: date | None = None  # next due date; None means no fixed date

    def mark_complete(self) -> Task | None:
        """Mark this task as completed and return the next occurrence if recurring.

        How timedelta is used:
          - "daily"  tasks get due_date = today + timedelta(days=1)
          - "weekly" tasks get due_date = today + timedelta(days=7)
          timedelta(days=N) shifts a date object forward by exactly N calendar
          days, handling month/year rollovers automatically.

        Returns:
            A new Task with a fresh due_date if the task is recurring,
            or None for one-off tasks.
        """
        self.is_completed = True
        self.recurrence_count += 1

        if self.frequency in ("daily", "weekly"):
            days = 1 if self.frequency == "daily" else 7
            base = self.due_date if self.due_date else date.today()
            next_due = base + timedelta(days=days)
            return Task(
                title=self.title,
                duration_minutes=self.duration_minutes,
                priority=self.priority,
                preferred_time=self.preferred_time,
                frequency=self.frequency,
                due_date=next_due,
            )
        return None

    def to_dict(self) -> dict:
        """Return task data as a serializable dictionary."""
        return {
            "title": self.title,
            "duration_minutes": self.duration_minutes,
            "priority": self.priority.name,
            "is_completed": self.is_completed,
            "preferred_time": self.preferred_time if self.preferred_time else "—",
            "frequency": self.frequency if self.frequency else "one-off",
            "due_date": str(self.due_date) if self.due_date else "—",
            "recurrence_count": self.recurrence_count,
        }


@dataclass
class Pet:
    name: str
    species: str  # "dog", "cat", "other"
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to this pet's task list."""
        self.tasks.append(task)

    def complete_task(self, task: Task) -> Task | None:
        """Mark a task complete and auto-register its next occurrence if recurring.

        Calls task.mark_complete(), which handles the recurrence logic using
        timedelta. If a next-occurrence Task is returned, it is immediately
        appended to this pet's task list so it appears in future schedules
        without any extra steps from the caller.

        Args:
            task: A Task that belongs to this pet's task list.

        Returns:
            The newly created next-occurrence Task if task.frequency is
            "daily" or "weekly", otherwise None.
        """
        next_task = task.mark_complete()
        if next_task:
            self.add_task(next_task)
        return next_task

    def get_tasks_by_priority(self) -> list[Task]:
        """Return incomplete tasks sorted from highest to lowest priority.

        Completed tasks are excluded so the scheduler only sees actionable work.
        Sorting uses Priority.value (HIGH=3, MEDIUM=2, LOW=1) in descending order
        via reverse=True.

        Returns:
            A new list of pending Task objects, highest priority first.
        """
        return sorted(
            (t for t in self.tasks if not t.is_completed),
            key=lambda t: t.priority.value,
            reverse=True,
        )

    def get_tasks_by_status(self, completed: bool) -> list[Task]:
        """Return tasks filtered by completion status.

        Args:
            completed: Pass True to retrieve only completed tasks,
                       False to retrieve only pending tasks.

        Returns:
            A list of Task objects whose is_completed field matches
            the requested status. Order mirrors the original task list.
        """
        return [t for t in self.tasks if t.is_completed == completed]


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

    def get_tasks_for_pet(self, pet_name: str) -> list[Task]:
        """Return all tasks for a pet matched by name (case-insensitive).

        Args:
            pet_name: The name to search for. Comparison is case-insensitive,
                      so "mochi" and "Mochi" both match a Pet named "Mochi".

        Returns:
            The matched pet's full task list (both pending and completed),
            or an empty list if no pet with that name exists.
        """
        for pet in self.pets:
            if pet.name.lower() == pet_name.lower():
                return pet.tasks
        return []


class Schedule:
    def __init__(self):
        self.scheduled_tasks: list[Task] = []
        self.total_duration: int = 0
        self.explanations: list[tuple[Task, str]] = []

    def add_entry(self, task: Task, reason: str) -> None:
        """Add a task and its scheduling reason to the schedule.

        Appends the task to scheduled_tasks, records the (task, reason) pair
        in explanations for display, and increments total_duration.

        Args:
            task:   The Task being scheduled.
            reason: A plain-language string explaining why this task was
                    included (e.g. priority, available time remaining, or a
                    conflict notice).
        """
        self.scheduled_tasks.append(task)
        self.explanations.append((task, reason))
        self.total_duration += task.duration_minutes

    def display(self) -> str:
        """Format and return the full schedule as a human-readable string.

        Each line shows the task's time slot, recurrence label, title,
        duration, priority, and the reason it was scheduled. A total
        duration line is appended at the end.

        Returns:
            A multi-line string suitable for printing to the terminal
            or rendering with st.text() in Streamlit.
        """
        lines = []
        for task, reason in self.explanations:
            time_label = task.preferred_time if task.preferred_time else "anytime"
            freq_label = f" [{task.frequency}]" if task.frequency else ""
            lines.append(
                f"- [{time_label}]{freq_label} {task.title} ({task.duration_minutes} min)"
                f" [{task.priority.name}]: {reason}"
            )
        lines.append(f"Total time: {self.total_duration} min")
        return "\n".join(lines)


class Scheduler:
    def __init__(self, owner: Owner) -> None:
        self.owner = owner

    @staticmethod
    def _time_to_minutes(time_str: str) -> int | None:
        """Convert HH:MM to minutes after midnight, or None if invalid."""
        parts = time_str.split(":")
        if len(parts) != 2:
            return None
        if not parts[0].isdigit() or not parts[1].isdigit():
            return None
        hours = int(parts[0])
        minutes = int(parts[1])
        if not (0 <= hours <= 23 and 0 <= minutes <= 59):
            return None
        return hours * 60 + minutes

    @staticmethod
    def _minutes_to_time(total_minutes: int) -> str:
        """Convert minutes after midnight back to zero-padded HH:MM."""
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours:02d}:{minutes:02d}"

    @staticmethod
    def _round_up(value: int, step: int) -> int:
        """Round value up to the nearest step interval."""
        if step <= 1:
            return value
        remainder = value % step
        return value if remainder == 0 else value + (step - remainder)

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Return tasks sorted by preferred_time in ascending 'HH:MM' order.

        How it works:
          "HH:MM" strings are zero-padded, so lexicographic order equals
          chronological order — "07:30" < "14:00" < "23:45".
          Tasks with no time set receive a sentinel value of "99:99" so
          they sort to the end of the list.

        Example key:
          lambda t: t.preferred_time if t.preferred_time else "99:99"
        """
        return sorted(
            tasks,
            key=lambda t: t.preferred_time if t.preferred_time else "99:99",
        )

    def filter_tasks(
        self,
        pet_name: str | None = None,
        completed: bool | None = None,
    ) -> list[Task]:
        """Return tasks across all owner's pets, narrowed by optional filters.

        Either filter may be omitted independently. Passing no arguments
        returns every task for every pet — equivalent to owner.get_all_tasks().

        Args:
            pet_name:  If provided, only tasks belonging to the pet with this
                       name are included (case-insensitive match). Pass None
                       to include tasks from all pets.
            completed: If True, return only completed tasks. If False, return
                       only pending tasks. If None, return both.

        Returns:
            A flat list of Task objects matching all supplied filters,
            ordered by pet then by the pet's internal task order.
        """
        results = []
        for pet in self.owner.pets:
            if pet_name is not None and pet.name.lower() != pet_name.lower():
                continue
            for task in pet.tasks:
                if completed is not None and task.is_completed != completed:
                    continue
                results.append(task)
        return results

    def detect_conflicts(self, pet: Pet) -> list[str]:
        """Return warning strings for pending tasks on the same pet sharing a HH:MM time.

        Groups all incomplete, time-stamped tasks by their preferred_time value.
        Any group with more than one task produces a warning string. Tasks with
        no preferred_time are ignored (they have no declared start time to clash).

        Args:
            pet: The Pet whose task list is scanned.

        Returns:
            A list of warning strings, one per conflicting time slot.
            Empty list means no conflicts detected for this pet.
        """
        time_map: dict[str, list[Task]] = {}
        for task in pet.tasks:
            if not task.is_completed and task.preferred_time:
                time_map.setdefault(task.preferred_time, []).append(task)

        warnings = []
        for time_str, tasks in time_map.items():
            if len(tasks) > 1:
                names = ", ".join(t.title for t in tasks)
                warnings.append(
                    f"WARNING [{pet.name}] {time_str}: '{names}' overlap"
                )
        return warnings

    def detect_all_conflicts(self) -> list[str]:
        """Return warning strings for ALL pending tasks across every pet.

        Strategy (lightweight — no exceptions raised):
          1. Build a dict mapping each HH:MM time to a list of
             (pet_name, task) pairs across all pets.
          2. Any time slot with more than one entry is a conflict,
             whether the tasks belong to the same pet or different pets.
          3. Return plain warning strings so callers can print or display
             them without any program crash.
        """
        # time -> list of (pet_name, task)
        time_map: defaultdict[str, list[tuple[str, Task]]] = defaultdict(list)
        for pet in self.owner.pets:
            for task in pet.tasks:
                if not task.is_completed and task.preferred_time:
                    time_map[task.preferred_time].append((pet.name, task))

        warnings = []
        for time_str, entries in time_map.items():
            if len(entries) > 1:
                detail = ", ".join(
                    f"{pet_name}:'{task.title}'" for pet_name, task in entries
                )
                warnings.append(
                    f"WARNING {time_str}: {detail}"
                )
        return warnings

    def generate_schedule(self, pet: Pet) -> Schedule:
        """Build a Schedule by fitting tasks within the owner's available time.

        Tasks are ordered by descending priority first, then chronologically by
        preferred_time (HH:MM) within each priority band. Tasks with no time
        appear last within their priority band.
        Conflicts are noted in the reason string.
        """
        schedule = Schedule()
        remaining = self.owner.available_minutes

        tasks = sorted(
            (t for t in pet.tasks if not t.is_completed),
            key=lambda t: (
                -t.priority.value,
                t.preferred_time if t.preferred_time else "99:99",
            ),
        )

        time_usage: dict[str, list[Task]] = {}

        for task in tasks:
            if task.duration_minutes <= remaining:
                t_key = task.preferred_time
                existing = time_usage.get(t_key, []) if t_key else []

                if existing:
                    conflict_titles = ", ".join(t.title for t in existing)
                    reason = (
                        f"CONFLICT with '{conflict_titles}' at {t_key} | "
                        f"Priority: {task.priority.name} | "
                        f"{remaining} min left"
                    )
                else:
                    time_label = t_key if t_key else "anytime"
                    reason = (
                        f"Priority: {task.priority.name} | "
                        f"Time: {time_label} | "
                        f"Fits within available time ({remaining} min left)"
                    )

                if t_key:
                    time_usage.setdefault(t_key, []).append(task)
                schedule.add_entry(task, reason)
                remaining -= task.duration_minutes

        return schedule

    def find_next_available_slot(
        self,
        pet: Pet,
        duration_minutes: int,
        day_start: str = "06:00",
        day_end: str = "22:00",
        granularity_minutes: int = 5,
    ) -> str | None:
        """Return the earliest free HH:MM slot for a new task duration.

        This scans pending, time-stamped tasks as occupied windows and returns
        the earliest start time where a new task of duration_minutes can fit
        between day_start and day_end.
        """
        if duration_minutes <= 0:
            return None

        start_min = self._time_to_minutes(day_start)
        end_min = self._time_to_minutes(day_end)
        if start_min is None or end_min is None or start_min >= end_min:
            return None

        intervals: list[tuple[int, int]] = []
        for task in pet.tasks:
            if task.is_completed or not task.preferred_time:
                continue
            task_start = self._time_to_minutes(task.preferred_time)
            if task_start is None:
                continue
            task_end = task_start + task.duration_minutes
            if task_end <= start_min or task_start >= end_min:
                continue
            intervals.append((max(task_start, start_min), min(task_end, end_min)))

        intervals.sort(key=lambda pair: pair[0])

        merged: list[list[int]] = []
        for start, end in intervals:
            if not merged or start > merged[-1][1]:
                merged.append([start, end])
            else:
                merged[-1][1] = max(merged[-1][1], end)

        cursor = self._round_up(start_min, granularity_minutes)
        for busy_start, busy_end in merged:
            candidate = self._round_up(cursor, granularity_minutes)
            if candidate + duration_minutes <= busy_start:
                return self._minutes_to_time(candidate)
            cursor = max(cursor, busy_end)

        candidate = self._round_up(cursor, granularity_minutes)
        if candidate + duration_minutes <= end_min:
            return self._minutes_to_time(candidate)
        return None

    def get_all_tasks(self, pet: Pet) -> list[Task]:
        """Return all incomplete tasks for a pet, sorted by priority."""
        return pet.get_tasks_by_priority()

    def summary(self, schedule: Schedule, pet: Pet) -> str:
        """Return a formatted summary of the schedule for a given owner and pet.

        Runs detect_conflicts() for the pet and prepends any warnings above
        the schedule display so they are always visible before the task list.

        Args:
            schedule: The Schedule produced by generate_schedule(pet).
            pet:      The Pet the schedule was built for.

        Returns:
            A multi-line string containing owner name, pet name, task count,
            total duration, optional conflict warnings, and the full schedule
            from schedule.display().
        """
        conflicts = self.detect_conflicts(pet)
        lines = [
            f"Owner: {self.owner.name}",
            f"Pet: {pet.name}",
            f"Tasks scheduled: {len(schedule.scheduled_tasks)}",
            f"Total duration: {schedule.total_duration} min",
        ]
        if conflicts:
            lines.append("\nWarnings:")
            for c in conflicts:
                lines.append(f"  ! {c}")
        lines += ["", schedule.display()]
        return "\n".join(lines)
