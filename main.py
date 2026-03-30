from datetime import date
from pawpal_system import Task, Pet, Owner, Scheduler, Priority

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
owner = Owner(name="Jordan", available_minutes=120)

# --- Pet 1: Mochi (dog) ---
# Tasks added deliberately OUT OF ORDER to test sort_by_time.
# Some tasks are recurring (daily / weekly) with an explicit due_date.
mochi = Pet(name="Mochi", species="dog")
mochi.add_task(Task("Evening walk",    duration_minutes=30, priority=Priority.MEDIUM, preferred_time="18:00"))
mochi.add_task(Task("Feeding",         duration_minutes=10, priority=Priority.HIGH,   preferred_time="07:00",
                    frequency="daily",  due_date=date.today()))
mochi.add_task(Task("Enrichment play", duration_minutes=20, priority=Priority.MEDIUM, preferred_time="14:30",
                    frequency="weekly", due_date=date.today()))
mochi.add_task(Task("Morning walk",    duration_minutes=30, priority=Priority.HIGH,   preferred_time="07:30",
                    frequency="daily",  due_date=date.today()))
mochi.add_task(Task("Bath time",       duration_minutes=45, priority=Priority.LOW))   # one-off, no time set

# --- Pet 2: Luna (cat) ---
luna = Pet(name="Luna", species="cat")
luna.add_task(Task("Brush coat",         duration_minutes=15, priority=Priority.MEDIUM, preferred_time="19:00"))
luna.add_task(Task("Feeding",            duration_minutes=10, priority=Priority.HIGH,   preferred_time="08:00",
                   frequency="daily", due_date=date.today()))
luna.add_task(Task("Litter box clean",   duration_minutes=10, priority=Priority.HIGH,   preferred_time="08:00"))  # same-pet conflict at 08:00
luna.add_task(Task("Laser pointer play", duration_minutes=20, priority=Priority.LOW,    preferred_time="15:00"))
# Cross-pet conflict: Mochi already has "Evening walk" at 18:00
luna.add_task(Task("Evening brush",      duration_minutes=10, priority=Priority.MEDIUM, preferred_time="18:00"))  # cross-pet conflict with Mochi

owner.add_pet(mochi)
owner.add_pet(luna)

scheduler = Scheduler(owner)

# ---------------------------------------------------------------------------
# 1. sort_by_time
#    "HH:MM" strings are zero-padded, so lexicographic order == chronological.
#    Tasks with no preferred_time receive sentinel "99:99" and sort last.
# ---------------------------------------------------------------------------
print("=" * 55)
print("  SORT BY TIME DEMO")
print("=" * 55)

for pet in owner.pets:
    print(f"\n{pet.name} — tasks sorted by time:")
    print("-" * 45)
    for task in scheduler.sort_by_time(pet.tasks):
        time_label = task.preferred_time if task.preferred_time else "(no time)"
        freq_label = f"  [{task.frequency}]" if task.frequency else ""
        print(f"  {time_label:>10}  [{task.priority.name:<6}]  {task.title}{freq_label}")

# ---------------------------------------------------------------------------
# 2. filter_tasks — filter by pet name and/or completion status
# ---------------------------------------------------------------------------
print("\n" + "=" * 55)
print("  FILTER TASKS DEMO")
print("=" * 55)

# Mark one task complete before filtering so the status filter is meaningful
feeding = mochi.tasks[1]   # Feeding (07:00) — daily recurring
print(f"\nCompleting '{feeding.title}' for {mochi.name}...")
next_task = mochi.complete_task(feeding)
if next_task:
    print(f"  -> Next occurrence auto-created: '{next_task.title}' due {next_task.due_date}")

print("\nAll tasks across all pets:")
for t in scheduler.filter_tasks():
    status = "done" if t.is_completed else "pending"
    print(f"  [{status}]  {t.title}")

print("\nMochi's tasks only:")
for t in scheduler.filter_tasks(pet_name="Mochi"):
    print(f"  {t.title}")

print("\nPending tasks only (all pets):")
for t in scheduler.filter_tasks(completed=False):
    print(f"  {t.title}")

print("\nCompleted tasks only (all pets):")
completed = scheduler.filter_tasks(completed=True)
if completed:
    for t in completed:
        print(f"  {t.title}")
else:
    print("  (none)")

print("\nLuna's pending tasks:")
for t in scheduler.filter_tasks(pet_name="Luna", completed=False):
    print(f"  {t.title}")

# ---------------------------------------------------------------------------
# 3. Recurring task automation demo
#    Complete every recurring task and show the chain of next due dates.
# ---------------------------------------------------------------------------
print("\n" + "=" * 55)
print("  RECURRING TASK AUTOMATION DEMO")
print("=" * 55)

print("\nCompleting all remaining recurring tasks for Mochi:")
for task in list(mochi.tasks):   # snapshot — complete_task may append to mochi.tasks
    if task.frequency and not task.is_completed:
        next_t = mochi.complete_task(task)
        if next_t:
            print(
                f"  '{task.title}' done (count={task.recurrence_count}) "
                f"-> next due {next_t.due_date} [{next_t.frequency}]"
            )

print(f"\nMochi now has {len(mochi.tasks)} task entries (original + next occurrences):")
for t in mochi.tasks:
    status = "done" if t.is_completed else "pending"
    due = f"  due {t.due_date}" if t.due_date else ""
    print(f"  [{status}]  {t.title}{due}")

# ---------------------------------------------------------------------------
# 4. Conflict detection — same-pet AND cross-pet
# ---------------------------------------------------------------------------
print("\n" + "=" * 55)
print("  CONFLICT DETECTION DEMO")
print("=" * 55)

print("\nSame-pet conflicts (per pet):")
for pet in owner.pets:
    per_pet = scheduler.detect_conflicts(pet)
    if per_pet:
        for w in per_pet:
            print(f"  {w}")
    else:
        print(f"  {pet.name}: no same-pet conflicts")

print("\nAll conflicts across every pet (including cross-pet):")
all_conflicts = scheduler.detect_all_conflicts()
if all_conflicts:
    for w in all_conflicts:
        print(f"  {w}")
else:
    print("  No conflicts found.")

# ---------------------------------------------------------------------------
# 5. Full schedule with inline conflict notes
# ---------------------------------------------------------------------------
print("\n" + "=" * 55)
print("  TODAY'S SCHEDULE")
print("=" * 55)

for pet in owner.pets:
    schedule = scheduler.generate_schedule(pet)
    print(f"\n{pet.name} ({pet.species})")
    print("-" * 55)
    print(scheduler.summary(schedule, pet))

print("\n" + "=" * 55)
