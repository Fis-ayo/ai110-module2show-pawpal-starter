import streamlit as st
from datetime import date
from pawpal_system import Owner, Pet, Task, Scheduler, Priority

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.divider()


def priority_badge(priority: Priority) -> str:
    """Return an emoji label for visual priority scanning in tables."""
    badges = {
        Priority.HIGH: "🔴 HIGH",
        Priority.MEDIUM: "🟡 MEDIUM",
        Priority.LOW: "🟢 LOW",
    }
    return badges.get(priority, priority.name)

# --- Session state init ---
if "owner" not in st.session_state:
    st.session_state.owner = None
if "pet" not in st.session_state:
    st.session_state.pet = None

# --- Owner + Pet setup ---
st.subheader("Owner & Pet Info")

owner_name = st.text_input("Owner name", value="Jordan")
available_minutes = st.number_input("Available minutes today", min_value=10, max_value=480, value=60)
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])

if st.button("Save Owner & Pet"):
    pet = Pet(name=pet_name, species=species)
    owner = Owner(name=owner_name, available_minutes=int(available_minutes))
    owner.add_pet(pet)
    st.session_state.owner = owner
    st.session_state.pet = pet
    st.success(f"Saved! {owner_name} is caring for {pet_name}.")

st.divider()

# --- Add tasks ---
st.subheader("Tasks")

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority_str = st.selectbox("Priority", ["LOW", "MEDIUM", "HIGH"], index=2)

col4, col5 = st.columns(2)
with col4:
    preferred_time = st.text_input("Time (HH:MM, optional)", value="", placeholder="e.g. 07:30")
with col5:
    frequency = st.selectbox("Recurrence", ["one-off", "daily", "weekly"], index=0)

if st.button("Add task"):
    if st.session_state.pet is None:
        st.warning("Save an owner and pet first.")
    else:
        task = Task(
            title=task_title,
            duration_minutes=int(duration),
            priority=Priority[priority_str],
            preferred_time=preferred_time,
            frequency="" if frequency == "one-off" else frequency,
            due_date=date.today() if frequency != "one-off" else None,
        )
        st.session_state.pet.add_task(task)
        st.success(f"Added: {task_title}")

if st.session_state.pet and st.session_state.pet.tasks:
    pet = st.session_state.pet
    owner = st.session_state.owner

    # --- Conflict warnings shown inline with task list ---
    if owner:
        scheduler = Scheduler(owner)
        conflicts = scheduler.detect_conflicts(pet)
        if conflicts:
            st.error(f"⚠️ {len(conflicts)} time conflict(s) detected — review before generating your schedule.")
            for conflict in conflicts:
                # Parse out the time and task names for a helpful message
                # conflict format: "WARNING [PetName] HH:MM: 'task1, task2' overlap"
                clean = conflict.replace("WARNING ", "").replace(f"[{pet.name}] ", "")
                st.warning(
                    f"**Scheduling conflict:** {clean}\n\n"
                    "_Two tasks are set for the same time. Consider changing one task's time "
                    "or marking it as 'anytime' so PawPal+ can fit it around the other._"
                )

    col_filter, col_sort = st.columns(2)
    with col_filter:
        status_filter = st.radio("Filter tasks", ["All", "Pending", "Completed"], horizontal=True)
    with col_sort:
        sort_mode = st.radio("Sort by", ["Priority", "Time"], horizontal=True)

    if status_filter == "Pending":
        tasks_to_show = pet.get_tasks_by_status(completed=False)
    elif status_filter == "Completed":
        tasks_to_show = pet.get_tasks_by_status(completed=True)
    else:
        tasks_to_show = list(pet.tasks)

    # Apply Scheduler-based sorting
    if owner and tasks_to_show:
        scheduler = Scheduler(owner)
        if sort_mode == "Priority":
            # Use get_tasks_by_priority (pending only) or fall back to raw list
            pending_sorted = scheduler.get_all_tasks(pet)
            completed_tasks = [t for t in tasks_to_show if t.is_completed]
            pending_in_view = [t for t in pending_sorted if t in tasks_to_show]
            tasks_to_show = pending_in_view + completed_tasks
        else:
            tasks_to_show = scheduler.sort_by_time(tasks_to_show)

    if tasks_to_show:
        task_rows = []
        for task in tasks_to_show:
            row = task.to_dict()
            row["priority"] = priority_badge(task.priority)
            task_rows.append(row)
        st.table(task_rows)
    else:
        st.info("No tasks match this filter.")
else:
    st.info("No tasks yet. Add one above.")

st.divider()

# --- Next available slot helper ---
st.subheader("Find Next Available Slot")

slot_duration = st.number_input(
    "New task duration (minutes)",
    min_value=1,
    max_value=240,
    value=20,
    key="slot_duration",
)

if st.button("Suggest slot"):
    if st.session_state.owner is None or st.session_state.pet is None:
        st.warning("Save an owner and pet first.")
    else:
        owner = st.session_state.owner
        pet = st.session_state.pet
        scheduler = Scheduler(owner)
        slot = scheduler.find_next_available_slot(
            pet,
            duration_minutes=int(slot_duration),
            day_start="06:00",
            day_end="22:00",
        )
        if slot:
            st.success(f"Earliest open slot: {slot}")
        else:
            st.warning("No free slot found between 06:00 and 22:00 for that duration.")

st.divider()

# --- Generate schedule ---
st.subheader("Build Schedule")

if st.button("Generate schedule"):
    if st.session_state.owner is None or st.session_state.pet is None:
        st.warning("Save an owner and pet before generating a schedule.")
    elif not st.session_state.pet.tasks:
        st.warning("Add at least one task before generating a schedule.")
    else:
        owner = st.session_state.owner
        pet = st.session_state.pet
        scheduler = Scheduler(owner)

        # Show conflict warnings prominently before the schedule
        conflicts = scheduler.detect_conflicts(pet)
        if conflicts:
            st.error(f"⚠️ {len(conflicts)} conflict(s) found in your schedule. Tasks with the same time will be flagged below.")
            for conflict in conflicts:
                clean = conflict.replace("WARNING ", "").replace(f"[{pet.name}] ", "")
                st.warning(
                    f"**Conflict:** {clean}\n\n"
                    "_Both tasks will still be scheduled, but you may want to adjust "
                    "one of them to avoid a real-time rush._"
                )

        schedule = scheduler.generate_schedule(pet)

        if not schedule.scheduled_tasks:
            st.warning("No tasks fit within your available time. Try increasing available minutes or reducing task durations.")
        else:
            # Summary metrics
            remaining = owner.available_minutes - schedule.total_duration
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Tasks scheduled", len(schedule.scheduled_tasks))
            col_b.metric("Time used (min)", schedule.total_duration)
            col_c.metric("Time remaining (min)", remaining)

            st.success(f"Schedule ready for {pet.name}!")

            # Render each scheduled entry as a structured table
            rows = []
            for task, reason in schedule.explanations:
                has_conflict = "CONFLICT" in reason
                rows.append({
                    "Time": task.preferred_time if task.preferred_time else "anytime",
                    "Task": task.title,
                    "Duration (min)": task.duration_minutes,
                    "Priority": priority_badge(task.priority),
                    "Recurrence": task.frequency if task.frequency else "one-off",
                    "Note": "⚠️ Conflict" if has_conflict else "✓ Scheduled",
                })

            st.table(rows)

            # Separate callout for any conflicting entries in the schedule
            conflicted = [(t, r) for t, r in schedule.explanations if "CONFLICT" in r]
            if conflicted:
                st.warning(
                    f"**{len(conflicted)} task(s) in your schedule overlap with another task's time slot.** "
                    "They are still included — but you should check whether your pet can realistically "
                    "do both at the same time, or reschedule one to a different hour."
                )
                for task, reason in conflicted:
                    st.caption(f"• **{task.title}** at {task.preferred_time}: {reason}")
