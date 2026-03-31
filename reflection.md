# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

The initial UML design consisted of four classes: `Task`, `Pet`, `Owner`, and `Schedule`, plus a standalone `schedule_tasks()` function.

- **Task** holds the data for a single pet care activity — its title, duration in minutes, priority level (low/medium/high), and whether it has been completed. It is a pure data object with no scheduling logic.
- **Pet** represents the animal being cared for. It stores the pet's name and species, and owns a list of `Task` objects. It is responsible for managing its own tasks and can return them sorted by priority.
- **Owner** represents the person using the app. It stores the owner's name, their total available minutes for the day, and a list of pets they own. It is the top-level entry point for the system.
- **Schedule** represents the output of the scheduling process — an ordered list of tasks that fit within the owner's time budget, along with a plain-language explanation for why each task was included. It is responsible for accumulating entries and formatting the final plan for display.

A fifth class, `Scheduler`, was initially considered but removed. Its single responsibility — running the scheduling algorithm — was simple enough to live in a standalone `schedule_tasks(pet, available_minutes)` function, which reduced unnecessary complexity without losing any capability.

**b. Design changes**

Three changes were made after reviewing the skeleton against potential logic issues:

1. **Added a `Priority` enum** — `Task.priority` was originally a plain string (`"low"`, `"medium"`, `"high"`). This was replaced with a `Priority` enum (`LOW = 1`, `MEDIUM = 2`, `HIGH = 3`). Unvalidated strings can silently cause bugs: a typo like `"HIGH"` or `"urgent"` would pass without error but break any sort logic. The enum enforces valid values at the type level and makes priority comparison straightforward using its integer values.

2. **Changed `Schedule.explanations` from `dict` to `list[tuple[Task, str]]`** — the original `dict[str, str]` was intended to map task titles to reasons. However, if two tasks share the same title (e.g. two "Feeding" entries), the second would silently overwrite the first. Switching to a list of `(Task, reason)` tuples preserves every entry and keeps tasks and their explanations directly paired.

3. **Updated `schedule_tasks()` signature from `(pet, available_minutes)` to `(owner, pet)`** — the original signature accepted `available_minutes` as a loose integer, disconnecting the function from the `Owner` who owns that constraint. Passing `owner` directly makes the relationship explicit and lets the function access `owner.available_minutes` internally, reducing the burden on the caller.

4. **`Scheduler` was reinstated as a class** — initially dropped in favor of a standalone `schedule_tasks()` function, `Scheduler` was brought back during implementation as a dedicated class. It holds a reference to the `Owner` (giving it persistent access to time constraints) and exposes `generate_schedule(pet)`, `get_all_tasks(pet)`, and `summary(schedule, pet)`. This made the scheduling logic easier to extend and test compared to a loose function.

5. **Added `Owner.get_all_tasks()`** — a convenience method was added to `Owner` that flattens all tasks across every pet into a single list. This gives the `Scheduler` (and the UI) a straightforward way to get a full picture of all pending tasks without manually iterating over pets.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers three constraints:

1. **Time budget** — `Owner.available_minutes` is the hard ceiling. A task is only added to the schedule if its `duration_minutes` is less than or equal to the time remaining. This is evaluated greedily in priority order, so high-priority tasks claim time first.

2. **Priority** — Tasks are ranked `HIGH = 3`, `MEDIUM = 2`, `LOW = 1` using the `Priority` enum. Inside `generate_schedule`, tasks are pre-sorted by descending priority (and then by `preferred_time` as a tiebreaker), so the scheduler never skips a high-priority task to fit a low-priority one.

3. **Preferred time** — If a task has a `preferred_time` (`HH:MM`), that time is respected in the display order and flagged if two tasks share the same slot. It is a preference, not a hard constraint — the scheduler does not refuse to schedule a task solely because its preferred time has passed.

Time budget was the most important constraint to enforce correctly: a schedule that overflows the owner's day is useless, so that check runs before every insertion. Priority was the second most critical because it determines *which* tasks get the limited time. Preferred time is intentionally the weakest constraint — forcing exact-time compliance would cause too many tasks to be dropped, especially for owners who set times loosely.

**b. Tradeoffs**

The scheduler detects conflicts only when two tasks share the **exact same `HH:MM` start time**. It does not detect overlapping durations. For example, a 30-minute task starting at `07:30` runs until `08:00`, so a task starting at `07:45` would actually overlap — but the scheduler will not flag this because `07:30 ≠ 07:45`.

Catching true duration overlaps would require comparing each task's start time against the end times (`start + duration`) of every other task in the same window, turning an O(n) scan into an O(n²) pairwise check. For a pet care app where tasks are loosely spaced throughout the day (morning walk, midday feeding, evening play), exact-start-time matching catches the most common mistake — accidentally scheduling two things at the same time — without that added complexity. If tasks became fine-grained enough that 15-minute overlaps mattered, the `detect_all_conflicts` method is the right place to extend: replace the equality check with an interval-overlap check using each task's `preferred_time` and `duration_minutes`.

---

## 3. AI Collaboration

**a. How you used AI**

AI tools were used across every phase, but the role shifted depending on the phase:

- **Design phase** — Copilot Chat (with `#file:pawpal_system.py`) was used to pressure-test the UML before writing any code. Asking "what edge cases does this design miss?" surfaced the duplicate-title problem in `Schedule.explanations` early, before it could silently corrupt results at runtime.

- **Implementation phase** — Inline completions were most useful for boilerplate: dataclass field declarations, the `to_dict()` method body, and the `timedelta` arithmetic in `mark_complete()`. These are mechanical — the logic was already decided, and Copilot just typed it faster.

- **Debugging and testing** — Chat was used to ask "why would `get_tasks_by_priority` return an empty list?" when a test was failing. It identified that completed tasks were being included in the sort input, which led to the filter condition `if not t.is_completed` being added to the comprehension.

The most effective prompt pattern was **constraint + question**: *"Given that `preferred_time` is a plain `HH:MM` string, what is the simplest way to sort tasks chronologically without importing datetime?"* Narrow, specific prompts with the constraint stated upfront produced directly usable suggestions. Broad prompts like "how should I implement scheduling?" produced generic textbook answers that required significant translation.

**b. Judgment and verification**

When asking Copilot to help implement `detect_conflicts`, its first suggestion used `datetime.strptime` to parse each `preferred_time` string into a `datetime` object before comparing them. The logic was technically correct, but it added an import, introduced a new failure mode (malformed time strings would raise `ValueError`), and solved a problem that didn't exist — because `"HH:MM"` strings are already zero-padded and sort correctly as plain strings.

The suggestion was rejected and replaced with a direct equality check (`task.preferred_time == other.preferred_time`) grouped via a `dict`. To verify this was safe, I checked that all time inputs in the UI go through a single `st.text_input` with a placeholder of `"e.g. 07:30"`, meaning any format variation is a user error, not a system responsibility. The simpler implementation also made the method easier to test — no need to mock datetime parsing, and the test cases read clearly as string comparisons.

This pattern — accepting the shape of an AI suggestion while simplifying the implementation — came up repeatedly. Copilot defaults toward robustness and generality; the job of the architect is to ask whether that robustness is actually needed here.

---

## 4. Testing and Verification

**a. What you tested**

The test suite focused on the four algorithmic behaviors that could silently break without being obvious in the UI:

- **Chronological sorting** — verified that `sort_by_time` produces the correct order for mixed timed/untimed tasks, and that untimed tasks always land last regardless of their priority.
- **Priority filtering** — verified that `get_tasks_by_priority` returns tasks in HIGH → MEDIUM → LOW order and that completed tasks are excluded entirely, not just sorted to the bottom.
- **Recurrence** — tested all three branches: daily tasks produce a next occurrence due tomorrow, weekly tasks produce one due in 7 days, and one-off tasks return `None`. A fourth test verified that `recurrence_count` increments correctly on each completion.
- **Conflict detection** — tested the same-time conflict case, the no-conflict case (different times), the false-positive case (completed tasks sharing a time should not trigger a warning), and the cross-pet case via `detect_all_conflicts`.

These behaviors were prioritized because they are invisible to a casual user — a sorting bug or a false conflict warning would degrade the schedule quality without any obvious error message.

**b. Confidence**

**★★★★☆ (4 / 5)**

The core algorithmic behaviors are well covered and passing. The gap is in `generate_schedule` itself — the full greedy loop with time-budget tracking is not directly tested. Specific edge cases that remain unverified: a task that exactly fills the remaining budget (boundary condition), a pet with no tasks (empty input), and `filter_tasks` with combined pet-name and completion-status filters. If those were added, confidence would reach 5/5.

---

## 5. Reflection

**a. What went well**

The decision to reinstate `Scheduler` as a class (rather than a standalone function) paid off during the UI integration phase. Because `Scheduler` holds a reference to `Owner`, the Streamlit code only needed to instantiate it once per button click — no need to thread `available_minutes` through every call. The methods (`detect_conflicts`, `sort_by_time`, `generate_schedule`) all composed cleanly in `app.py` without any awkward parameter passing. Designing the class boundary carefully upfront saved friction at every later step.

**b. What you would improve**

Two things stand out:

1. **Duration-overlap detection** — the current conflict check only catches tasks at the exact same `HH:MM`. A task starting at `07:30` for 30 minutes overlaps with one starting at `07:45`, but the scheduler won't flag it. Adding an interval-overlap check inside `detect_conflicts` (comparing each task's start and `start + duration` against every other task's window) would make the warnings genuinely reliable.

2. **UI for completing tasks** — the app has no way to mark a task done from the Streamlit interface. The `Pet.complete_task()` method and recurrence logic are fully implemented, but they're only reachable from tests or the CLI. Adding a checkbox or button per task row would close that gap and make the app actually useful day-to-day.

**c. Key takeaway**

The most important thing I learned is that AI tools shift the bottleneck, not remove it. Copilot could generate a working `detect_conflicts` method in seconds — but it couldn't decide whether duration-overlap detection was worth the added complexity for this use case. It couldn't decide that `Schedule.explanations` should be a list of tuples instead of a dict. It couldn't decide when the `Scheduler` class was worth the overhead versus a plain function. Every one of those decisions required understanding the full system: what other code would depend on this, what failure modes were acceptable, how the UI would consume the output. AI handles the *how* quickly; the architect still owns the *why*.
