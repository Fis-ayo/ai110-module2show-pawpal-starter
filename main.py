from pawpal_system import Task, Pet, Owner, Scheduler, Priority

# --- Setup ---
owner = Owner(name="Jordan", available_minutes=90)

# --- Pet 1 ---
mochi = Pet(name="Mochi", species="dog")
mochi.add_task(Task("Morning walk",    duration_minutes=30, priority=Priority.HIGH))
mochi.add_task(Task("Feeding",         duration_minutes=10, priority=Priority.HIGH))
mochi.add_task(Task("Enrichment play", duration_minutes=20, priority=Priority.MEDIUM))
mochi.add_task(Task("Bath time",       duration_minutes=45, priority=Priority.LOW))

# --- Pet 2 ---
luna = Pet(name="Luna", species="cat")
luna.add_task(Task("Feeding",          duration_minutes=10, priority=Priority.HIGH))
luna.add_task(Task("Litter box clean", duration_minutes=10, priority=Priority.HIGH))
luna.add_task(Task("Brush coat",       duration_minutes=15, priority=Priority.MEDIUM))
luna.add_task(Task("Laser pointer play", duration_minutes=20, priority=Priority.LOW))

owner.add_pet(mochi)
owner.add_pet(luna)

# --- Schedule ---
scheduler = Scheduler(owner)

print("=" * 40)
print("        TODAY'S SCHEDULE")
print("=" * 40)

for pet in owner.pets:
    schedule = scheduler.generate_schedule(pet)
    print(f"\n{pet.name} ({pet.species})")
    print("-" * 40)
    print(schedule.display())

print("\n" + "=" * 40)
