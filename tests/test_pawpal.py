"""Automated tests for the PawPal+ logic layer."""

from datetime import date, timedelta

import pytest

from pawpal_system import Owner, Pet, Scheduler, Task


@pytest.fixture
def scheduler_setup():
    """Build a small Owner/Pet/Task world shared by several tests."""
    owner = Owner(name="Jordan")
    mochi = Pet(name="Mochi", species="dog")
    biscuit = Pet(name="Biscuit", species="cat")
    owner.add_pet(mochi)
    owner.add_pet(biscuit)
    return owner, mochi, biscuit, Scheduler(owner)


# ---------- core class behavior ----------

def test_mark_complete_changes_status():
    """Calling mark_complete() flips a task's completed flag."""
    task = Task("Morning walk", "07:30")
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_adding_task_increases_pet_task_count():
    """Adding a task to a Pet increases that pet's task count."""
    pet = Pet(name="Mochi", species="dog")
    assert pet.task_count() == 0
    pet.add_task(Task("Breakfast", "08:00"))
    assert pet.task_count() == 1


# ---------- sorting ----------

def test_sort_by_time_returns_chronological_order(scheduler_setup):
    """Tasks added out of order come back sorted by start time."""
    _, mochi, biscuit, scheduler = scheduler_setup
    mochi.add_task(Task("Evening walk", "18:00"))
    mochi.add_task(Task("Breakfast", "08:00"))
    biscuit.add_task(Task("Midday play", "12:30"))

    times = [task.time for _, task in scheduler.sort_by_time()]
    assert times == ["08:00", "12:30", "18:00"]


def test_sort_by_priority_puts_high_first(scheduler_setup):
    """Priority sorting orders high > medium > low, then by time within a level."""
    _, mochi, _, scheduler = scheduler_setup
    mochi.add_task(Task("Grooming", "10:00", priority="low"))
    mochi.add_task(Task("Medication", "20:00", priority="high"))
    mochi.add_task(Task("Walk", "09:00", priority="high"))
    mochi.add_task(Task("Play", "12:00", priority="medium"))

    ordered = [t.description for _, t in scheduler.sort_by_priority()]
    assert ordered == ["Walk", "Medication", "Play", "Grooming"]


# ---------- recurrence ----------

def test_daily_recurrence_creates_next_day_task(scheduler_setup):
    """Completing a daily task auto-creates a copy due tomorrow."""
    _, mochi, _, scheduler = scheduler_setup
    mochi.add_task(Task("Breakfast", "08:00", frequency="daily"))

    follow_up = scheduler.mark_task_complete("Mochi", "Breakfast")

    assert follow_up is not None
    assert follow_up.completed is False
    assert follow_up.due_date == date.today() + timedelta(days=1)
    assert mochi.task_count() == 2  # original (completed) + new occurrence


def test_one_time_task_does_not_recur(scheduler_setup):
    """Completing a 'once' task should NOT create a follow-up."""
    _, mochi, _, scheduler = scheduler_setup
    mochi.add_task(Task("Vet appointment", "14:30", frequency="once"))

    follow_up = scheduler.mark_task_complete("Mochi", "Vet appointment")

    assert follow_up is None
    assert mochi.task_count() == 1


# ---------- conflict detection ----------

def test_conflict_detection_flags_same_start_time(scheduler_setup):
    """Two pending tasks starting at the same time trigger a warning."""
    _, mochi, biscuit, scheduler = scheduler_setup
    mochi.add_task(Task("Breakfast", "08:00"))
    biscuit.add_task(Task("Medication", "08:00"))

    warnings = scheduler.detect_conflicts()
    assert len(warnings) == 1
    assert "08:00" in warnings[0]


def test_conflict_detection_flags_overlapping_durations(scheduler_setup):
    """A task starting during another task's duration window is flagged."""
    _, mochi, biscuit, scheduler = scheduler_setup
    mochi.add_task(Task("Morning walk", "08:00", duration_minutes=30))
    biscuit.add_task(Task("Feeding", "08:15", duration_minutes=10))

    warnings = scheduler.detect_conflicts()
    assert len(warnings) == 1
    assert "overlaps" in warnings[0]


def test_no_conflict_for_back_to_back_tasks(scheduler_setup):
    """A task starting exactly when another ends is NOT a conflict."""
    _, mochi, biscuit, scheduler = scheduler_setup
    mochi.add_task(Task("Morning walk", "08:00", duration_minutes=30))
    biscuit.add_task(Task("Feeding", "08:30", duration_minutes=10))

    assert scheduler.detect_conflicts() == []


# ---------- filtering & edge cases ----------

def test_filter_by_pet_and_status(scheduler_setup):
    """Filtering isolates one pet's tasks and completed/pending tasks."""
    _, mochi, biscuit, scheduler = scheduler_setup
    mochi.add_task(Task("Breakfast", "08:00"))
    biscuit.add_task(Task("Dinner", "18:00"))
    mochi.tasks[0].mark_complete()

    mochi_tasks = scheduler.filter_by_pet("Mochi")
    assert len(mochi_tasks) == 1
    assert mochi_tasks[0][1].description == "Breakfast"

    completed = scheduler.filter_by_status(completed=True)
    assert len(completed) == 1
    assert completed[0][0].name == "Mochi"


def test_edge_case_pet_with_no_tasks(scheduler_setup):
    """A pet with no tasks doesn't break sorting or conflict detection."""
    _, _, _, scheduler = scheduler_setup
    assert scheduler.sort_by_time() == []
    assert scheduler.detect_conflicts() == []