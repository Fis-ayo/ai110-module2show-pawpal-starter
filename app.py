import streamlit as st
from datetime import date
from pawpal_system import Owner, Pet, Task, Scheduler, Priority

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.divider()

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
    status_filter = st.radio("Filter tasks", ["All", "Pending", "Completed"], horizontal=True)
    pet = st.session_state.pet
    if status_filter == "Pending":
        tasks_to_show = pet.get_tasks_by_status(completed=False)
    elif status_filter == "Completed":
        tasks_to_show = pet.get_tasks_by_status(completed=True)
    else:
        tasks_to_show = pet.tasks
    st.write("Current tasks:")
    st.table([t.to_dict() for t in tasks_to_show])
else:
    st.info("No tasks yet. Add one above.")

st.divider()

# --- Generate schedule ---
st.subheader("Build Schedule")

if st.button("Generate schedule"):
    if st.session_state.owner is None or st.session_state.pet is None:
        st.warning("Save an owner and pet before generating a schedule.")
    elif not st.session_state.pet.tasks:
        st.warning("Add at least one task before generating a schedule.")
    else:
        scheduler = Scheduler(st.session_state.owner)
        pet = st.session_state.pet
        conflicts = scheduler.detect_conflicts(pet)
        for c in conflicts:
            st.warning(c)
        schedule = scheduler.generate_schedule(pet)
        st.success("Schedule generated!")
        st.text(scheduler.summary(schedule, pet))
