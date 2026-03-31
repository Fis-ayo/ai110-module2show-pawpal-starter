# PawPal+

**PawPal+** is a Streamlit app that helps busy pet owners build a realistic daily care schedule. Enter your available time, add tasks for your pet, and PawPal+ will sort, filter, and schedule them automatically — flagging conflicts before they become problems.

---

## Features

### Smart Scheduling
PawPal+ uses a priority-first, time-aware greedy algorithm to build a daily plan that fits within your available minutes. Tasks are included in order of urgency, and the scheduler explains why each task was chosen (or skipped).

### Chronological Sorting
Tasks with a preferred time (`HH:MM`) are displayed and scheduled in chronological order. Because the time strings are zero-padded, they sort correctly with a simple string comparison — no datetime parsing needed. Tasks with no preferred time always appear last.

### Priority-Based Ordering
Tasks can be marked **HIGH**, **MEDIUM**, or **LOW** priority. `get_tasks_by_priority()` returns only pending tasks, ranked from highest to lowest, so the most critical care always gets scheduled first.

### Conflict Detection
If two pending tasks share the exact same start time, PawPal+ raises a visible warning in both the task list and the schedule view. The warning names the specific tasks and time, and suggests how to resolve the overlap — before it causes a real-time rush for your pet.

### Recurring Tasks
Tasks can repeat on a **daily** or **weekly** cadence. When you mark a recurring task complete, PawPal+ automatically calculates the next due date using Python's `timedelta` and adds it to the schedule — no manual re-entry needed.

### Status Filtering
Switch between **All**, **Pending**, and **Completed** views of your task list at any time. You can also sort the visible tasks by **Priority** or by **Time**, using the Scheduler's `sort_by_time()` method directly.

### Schedule Summary
After generating a schedule, a three-metric dashboard shows tasks scheduled, total time used, and time remaining. The full schedule renders as a structured table with a conflict badge (`⚠️ Conflict` or `✓ Scheduled`) on each row.

---

## Getting Started

### Requirements

- Python 3.9+
- Dependencies listed in `requirements.txt`

### Setup

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run the app

```bash
streamlit run app.py
```

---

## How to Use

1. **Owner & Pet Info** — Enter the owner's name, how many minutes are available today, and the pet's name and species. Click **Save Owner & Pet**.
2. **Add Tasks** — Fill in a task title, duration, priority, optional preferred time (`HH:MM`), and recurrence. Click **Add task**.
3. **Review the task list** — Use the filter and sort controls to check your tasks. Conflict warnings appear here if two tasks share the same time.
4. **Generate Schedule** — Click **Generate schedule**. PawPal+ will show a metrics summary, a structured task table, and any conflict callouts with actionable advice.

---

## Project Structure

```
app.py              # Streamlit UI
pawpal_system.py    # Core data model and scheduling logic
main.py             # CLI entry point (demo / manual testing)
tests/
  test_pawpal.py    # Automated test suite
requirements.txt
```

---

## Running Tests

```bash
python -m pytest tests/test_pawpal.py -v
```

### Test coverage

| Area | What is verified |
|---|---|
| Chronological sorting | Tasks sort by `HH:MM`; untimed tasks always land last |
| Priority filtering | `get_tasks_by_priority` returns HIGH → MEDIUM → LOW; excludes completed tasks |
| Recurrence — daily | Completing a daily task produces a new Task due tomorrow |
| Recurrence — weekly | Completing a weekly task produces a new Task due in 7 days |
| Recurrence — one-off | Completing a one-off task returns `None` (no next occurrence) |
| Recurrence count | `recurrence_count` increments on each completion |
| Pet task list growth | `Pet.complete_task()` appends the next occurrence automatically |
| Conflict detection | Two tasks at the same time produce a warning; different times do not |
| Conflict — completed tasks | A completed task at a shared time does not trigger a false positive |
| Cross-pet conflicts | `detect_all_conflicts()` catches collisions across different pets |

16 tests · 16 passed
