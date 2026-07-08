import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
PawPal+ is a pet care planning assistant. Add your pets and their care tasks below,
then generate a daily plan — sorted by time or priority, with warnings for
overlapping tasks and automatic recurrence for daily/weekly tasks.
"""
)

# ---------- Application "memory" ----------
# Streamlit reruns this script top-to-bottom on every interaction, so the Owner
# object lives in st.session_state to persist between reruns.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan")
if "scheduler" not in st.session_state:
    st.session_state.scheduler = Scheduler(st.session_state.owner)

owner: Owner = st.session_state.owner
scheduler: Scheduler = st.session_state.scheduler

st.divider()

# ---------- Owner and pets ----------
st.subheader("Owner & Pets")

owner_name = st.text_input("Owner name", value=owner.name)
owner.name = owner_name  # keep the Owner object in sync with the UI

col1, col2 = st.columns(2)
with col1:
    pet_name = st.text_input("Pet name", value="Mochi")
with col2:
    species = st.selectbox("Species", ["dog", "cat", "other"])

if st.button("Add pet"):
    if pet_name.strip() and owner.get_pet(pet_name) is None:
        owner.add_pet(Pet(name=pet_name.strip(), species=species))
        st.success(f"Added {pet_name}!")
    elif owner.get_pet(pet_name):
        st.warning(f"{pet_name} is already registered.")
    else:
        st.warning("Please enter a pet name.")

if owner.pets:
    st.caption("Registered pets: " + ", ".join(f"{p.name} ({p.species})" for p in owner.pets))

st.markdown("### Tasks")
st.caption("Add care tasks for your pets. These feed directly into the Scheduler.")

if not owner.pets:
    st.info("Add a pet first, then you can schedule tasks for it.")
else:
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        task_pet = st.selectbox("Pet", [p.name for p in owner.pets])
    with col2:
        task_title = st.text_input("Task title", value="Morning walk")
    with col3:
        task_time = st.time_input("Time")
    with col4:
        duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
    with col5:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
    frequency = st.selectbox("Frequency", ["once", "daily", "weekly"])

    if st.button("Add task"):
        if task_title.strip():
            pet = owner.get_pet(task_pet)
            pet.add_task(
                Task(
                    description=task_title.strip(),
                    time=task_time.strftime("%H:%M"),
                    duration_minutes=int(duration),
                    priority=priority,
                    frequency=frequency,
                )
            )
            st.success(f"Scheduled '{task_title}' for {task_pet}.")
        else:
            st.warning("Please enter a task title.")

st.divider()

# ---------- Smart schedule ----------
st.subheader("Build Schedule")
st.caption("Calls the sorting, filtering, and conflict detection methods from pawpal_system.py.")

show_completed = st.checkbox("Show completed tasks")
filter_pet = (
    st.selectbox("Filter by pet", ["All pets"] + [p.name for p in owner.pets])
    if owner.pets
    else "All pets"
)
sort_mode = st.radio("Sort by", ["Time", "Priority"], horizontal=True)

if st.button("Generate schedule"):
    pairs = (
        scheduler.get_all_tasks()
        if filter_pet == "All pets"
        else scheduler.filter_by_pet(filter_pet)
    )
    pairs = (
        scheduler.sort_by_time(pairs)
        if sort_mode == "Time"
        else scheduler.sort_by_priority(pairs)
    )
    if not show_completed:
        pairs = [(p, t) for p, t in pairs if not t.completed]

    # Conflict warnings from the algorithmic layer
    for warning in scheduler.detect_conflicts():
        st.warning(warning)

    if not pairs:
        st.success("No pending tasks — everyone is happy! 🎉")
    else:
        st.table(
            [
                {
                    "Time": t.time,
                    "Pet": p.name,
                    "Task": t.description,
                    "Duration": f"{t.duration_minutes} min",
                    "Priority": t.priority,
                    "Frequency": t.frequency,
                    "Due": str(t.due_date),
                    "Status": "✅ Done" if t.completed else "⏳ Pending",
                }
                for p, t in pairs
            ]
        )

# ---------- Complete a task (drives recurrence) ----------
pending = [(p, t) for p, t in scheduler.sort_by_time() if not t.completed]
if pending:
    st.subheader("Complete a Task")
    labels = [f"{p.name} — {t.description} @ {t.time}" for p, t in pending]
    choice = st.selectbox("Pick a task", labels)
    if st.button("Mark complete"):
        pet, task = pending[labels.index(choice)]
        follow_up = scheduler.mark_task_complete(pet.name, task.description)
        if follow_up:
            st.success(f"Done! Recurring task auto-rescheduled for {follow_up.due_date}.")
        else:
            st.success("Done!")
        st.rerun()