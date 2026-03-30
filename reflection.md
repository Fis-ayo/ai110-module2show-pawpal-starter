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

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
