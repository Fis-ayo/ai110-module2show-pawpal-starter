from datetime import date, timedelta

from pawpal_system import Owner, Pet, Priority, Scheduler, Task


# ---------------------------------------------------------------------------
# Existing tests
# ---------------------------------------------------------------------------

def test_mark_complete_changes_status():
    task = Task("Feeding", duration_minutes=10, priority=Priority.HIGH)
    assert task.is_completed is False
    task.mark_complete()
    assert task.is_completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Mochi", species="dog")
    assert len(pet.tasks) == 0
    pet.add_task(Task("Morning walk", duration_minutes=30, priority=Priority.HIGH))
    assert len(pet.tasks) == 1


# ---------------------------------------------------------------------------
# Sorting correctness
# ---------------------------------------------------------------------------

def test_sort_by_time_chronological_order():
    """Tasks with preferred_time should come back in HH:MM order."""
    owner = Owner(name="Ada", available_minutes=120, pets=[])
    scheduler = Scheduler(owner)

    evening = Task("Evening walk", duration_minutes=30, priority=Priority.LOW, preferred_time="18:00")
    morning = Task("Morning feed", duration_minutes=10, priority=Priority.HIGH, preferred_time="07:30")
    midday = Task("Midday brush", duration_minutes=15, priority=Priority.MEDIUM, preferred_time="12:00")

    sorted_tasks = scheduler.sort_by_time([evening, morning, midday])

    assert [t.preferred_time for t in sorted_tasks] == ["07:30", "12:00", "18:00"]


def test_sort_by_time_untimed_tasks_go_last():
    """Tasks with no preferred_time should sort after all timed tasks."""
    owner = Owner(name="Ada", available_minutes=120, pets=[])
    scheduler = Scheduler(owner)

    no_time = Task("Anytime play", duration_minutes=20, priority=Priority.HIGH)
    timed = Task("Morning feed", duration_minutes=10, priority=Priority.LOW, preferred_time="08:00")

    sorted_tasks = scheduler.sort_by_time([no_time, timed])

    assert sorted_tasks[0].preferred_time == "08:00"
    assert sorted_tasks[1].preferred_time == ""


def test_get_tasks_by_priority_order():
    """get_tasks_by_priority should return HIGH → MEDIUM → LOW."""
    pet = Pet(name="Luna", species="cat")
    pet.add_task(Task("Low task", duration_minutes=5, priority=Priority.LOW))
    pet.add_task(Task("High task", duration_minutes=5, priority=Priority.HIGH))
    pet.add_task(Task("Med task", duration_minutes=5, priority=Priority.MEDIUM))

    result = pet.get_tasks_by_priority()

    assert [t.priority for t in result] == [Priority.HIGH, Priority.MEDIUM, Priority.LOW]


def test_get_tasks_by_priority_excludes_completed():
    """Completed tasks must not appear in the priority-sorted list."""
    pet = Pet(name="Luna", species="cat")
    done = Task("Old task", duration_minutes=5, priority=Priority.HIGH)
    done.mark_complete()
    pet.add_task(done)
    pet.add_task(Task("Pending task", duration_minutes=5, priority=Priority.LOW))

    result = pet.get_tasks_by_priority()

    assert len(result) == 1
    assert result[0].title == "Pending task"


# ---------------------------------------------------------------------------
# Recurrence logic
# ---------------------------------------------------------------------------

def test_daily_task_creates_next_occurrence():
    """Completing a daily task should return a new Task due tomorrow."""
    today = date.today()
    task = Task(
        "Daily feed",
        duration_minutes=10,
        priority=Priority.HIGH,
        frequency="daily",
        due_date=today,
    )

    next_task = task.mark_complete()

    assert next_task is not None
    assert next_task.due_date == today + timedelta(days=1)
    assert next_task.title == "Daily feed"
    assert next_task.is_completed is False


def test_weekly_task_creates_next_occurrence():
    """Completing a weekly task should return a new Task due in 7 days."""
    today = date.today()
    task = Task(
        "Weekly bath",
        duration_minutes=20,
        priority=Priority.MEDIUM,
        frequency="weekly",
        due_date=today,
    )

    next_task = task.mark_complete()

    assert next_task is not None
    assert next_task.due_date == today + timedelta(days=7)


def test_one_off_task_returns_none():
    """Completing a one-off task should return None (no next occurrence)."""
    task = Task("Vet visit", duration_minutes=60, priority=Priority.HIGH)
    next_task = task.mark_complete()
    assert next_task is None


def test_recurrence_count_increments():
    """recurrence_count should increase by 1 each time mark_complete is called."""
    task = Task("Daily feed", duration_minutes=10, priority=Priority.HIGH, frequency="daily")
    assert task.recurrence_count == 0
    task.mark_complete()
    assert task.recurrence_count == 1


def test_complete_task_appends_next_to_pet():
    """Pet.complete_task() should append the new recurring task to pet.tasks."""
    pet = Pet(name="Mochi", species="dog")
    task = Task("Daily walk", duration_minutes=30, priority=Priority.HIGH, frequency="daily")
    pet.add_task(task)

    pet.complete_task(task)

    # Original task still present + one new occurrence appended
    assert len(pet.tasks) == 2
    assert pet.tasks[1].is_completed is False
    assert pet.tasks[1].title == "Daily walk"


def test_complete_one_off_does_not_grow_pet_tasks():
    """Completing a one-off task should NOT append anything to pet.tasks."""
    pet = Pet(name="Mochi", species="dog")
    task = Task("Vet visit", duration_minutes=60, priority=Priority.HIGH)
    pet.add_task(task)

    pet.complete_task(task)

    assert len(pet.tasks) == 1


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------

def test_detect_conflicts_same_time_raises_warning():
    """Two incomplete tasks at the same time should produce a conflict warning."""
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task("Walk", duration_minutes=30, priority=Priority.HIGH, preferred_time="18:00"))
    pet.add_task(Task("Brush", duration_minutes=10, priority=Priority.LOW, preferred_time="18:00"))

    owner = Owner(name="Ada", available_minutes=120, pets=[pet])
    scheduler = Scheduler(owner)
    warnings = scheduler.detect_conflicts(pet)

    assert len(warnings) == 1
    assert "18:00" in warnings[0]
    assert "WARNING" in warnings[0]


def test_detect_conflicts_no_overlap_returns_empty():
    """Tasks at different times should produce no warnings."""
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task("Walk", duration_minutes=30, priority=Priority.HIGH, preferred_time="07:00"))
    pet.add_task(Task("Brush", duration_minutes=10, priority=Priority.LOW, preferred_time="18:00"))

    owner = Owner(name="Ada", available_minutes=120, pets=[pet])
    scheduler = Scheduler(owner)
    warnings = scheduler.detect_conflicts(pet)

    assert warnings == []


def test_detect_conflicts_ignores_completed_tasks():
    """A completed task sharing a time slot should NOT trigger a conflict warning."""
    pet = Pet(name="Mochi", species="dog")
    done = Task("Old walk", duration_minutes=30, priority=Priority.HIGH, preferred_time="18:00")
    done.mark_complete()
    pet.add_task(done)
    pet.add_task(Task("Evening brush", duration_minutes=10, priority=Priority.LOW, preferred_time="18:00"))

    owner = Owner(name="Ada", available_minutes=120, pets=[pet])
    scheduler = Scheduler(owner)
    warnings = scheduler.detect_conflicts(pet)

    assert warnings == []


def test_detect_all_conflicts_cross_pet():
    """Tasks from two different pets at the same time should be flagged."""
    pet1 = Pet(name="Mochi", species="dog")
    pet1.add_task(Task("Walk", duration_minutes=30, priority=Priority.HIGH, preferred_time="18:00"))

    pet2 = Pet(name="Luna", species="cat")
    pet2.add_task(Task("Brush", duration_minutes=10, priority=Priority.LOW, preferred_time="18:00"))

    owner = Owner(name="Ada", available_minutes=120, pets=[pet1, pet2])
    scheduler = Scheduler(owner)
    warnings = scheduler.detect_all_conflicts()

    assert len(warnings) == 1
    assert "18:00" in warnings[0]
    assert "Mochi" in warnings[0]
    assert "Luna" in warnings[0]
