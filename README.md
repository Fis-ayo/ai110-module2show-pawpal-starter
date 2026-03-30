# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Smarter Scheduling

Beyond the basic greedy scheduler, PawPal+ adds four algorithmic improvements:

**Chronological sorting (`Scheduler.sort_by_time`)**
Tasks are sorted by their `preferred_time` field in `"HH:MM"` format. Because the strings are zero-padded, a plain lambda key — `lambda t: t.preferred_time if t.preferred_time else "99:99"` — produces correct chronological order without any parsing. Tasks with no time set receive the sentinel `"99:99"` and always sort last.

**Flexible filtering (`Scheduler.filter_tasks`)**
A single method lets callers slice the full task list by pet name, completion status, or both at once. Passing no arguments returns every task across all pets — useful for dashboards and summaries.

**Recurring tasks (`Task.frequency` + `Pet.complete_task`)**
Tasks can be marked `"daily"` or `"weekly"`. When `Pet.complete_task(task)` is called, it uses Python's `timedelta` to calculate the next due date (`today + 1 day` or `today + 7 days`) and automatically appends a fresh task instance to the pet's list — no manual re-entry required.

**Conflict detection (`Scheduler.detect_conflicts` / `detect_all_conflicts`)**
`detect_conflicts(pet)` flags same-pet tasks sharing an exact `HH:MM` start time. `detect_all_conflicts()` extends this across every pet the owner has, catching cross-pet collisions too. Both methods return plain warning strings rather than raising exceptions, so the UI can display them gracefully.

---

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
