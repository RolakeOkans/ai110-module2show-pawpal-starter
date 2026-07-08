"""PawPal+ logic layer.

Contains the four core classes of the system:
    Task      -- a single activity (feeding, walk, medication, appointment)
    Pet       -- a pet with its own list of tasks
    Owner     -- a person who manages one or more pets
    Scheduler -- the "brain" that sorts, filters, detects conflicts,
                 and handles recurring tasks across all of an owner's pets
"""

from dataclasses import dataclass, field, replace
from datetime import date, timedelta

# Lower number = more important. Used as a sort key for priority scheduling.
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


@dataclass
class Task:
    """A single scheduled activity for a pet."""

    description: str
    time: str  # 24-hour "HH:MM" string, e.g. "08:30"
    duration_minutes: int = 15
    priority: str = "medium"  # "low", "medium", or "high"
    frequency: str = "once"  # "once", "daily", or "weekly"
    completed: bool = False
    due_date: date = field(default_factory=date.today)

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def start_minutes(self) -> int:
        """Return the start time as minutes since midnight (for sorting/overlap math)."""
        hours, minutes = (int(part) for part in self.time.split(":"))
        return hours * 60 + minutes

    def end_minutes(self) -> int:
        """Return the end time (start + duration) as minutes since midnight."""
        return self.start_minutes() + self.duration_minutes

    def next_occurrence(self) -> "Task | None":
        """Return a fresh Task for the next occurrence of a recurring task.

        Returns None for one-time tasks.
        """
        if self.frequency == "daily":
            delta = timedelta(days=1)
        elif self.frequency == "weekly":
            delta = timedelta(weeks=1)
        else:
            return None
        return replace(self, completed=False, due_date=self.due_date + delta)

    def __str__(self) -> str:
        status = "✓" if self.completed else "•"
        return (
            f"[{status}] {self.time}  {self.description} "
            f"({self.duration_minutes} min, {self.priority}, {self.frequency}, due {self.due_date})"
        )


@dataclass
class Pet:
    """A pet with identifying details and its own task list."""

    name: str
    species: str
    age: int = 0
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a new task to this pet."""
        self.tasks.append(task)

    def pending_tasks(self) -> list[Task]:
        """Return this pet's incomplete tasks."""
        return [t for t in self.tasks if not t.completed]

    def task_count(self) -> int:
        """Return the total number of tasks for this pet."""
        return len(self.tasks)


@dataclass
class Owner:
    """A pet owner who manages multiple pets."""

    name: str
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Register a new pet under this owner."""
        self.pets.append(pet)

    def get_pet(self, pet_name: str) -> Pet | None:
        """Look up one of the owner's pets by name (case-insensitive)."""
        for pet in self.pets:
            if pet.name.lower() == pet_name.lower():
                return pet
        return None

    def all_tasks(self) -> list[tuple[Pet, Task]]:
        """Return every (pet, task) pair across all of the owner's pets."""
        return [(pet, task) for pet in self.pets for task in pet.tasks]


class Scheduler:
    """The brain of PawPal+: organizes tasks across all of an owner's pets."""

    def __init__(self, owner: Owner):
        self.owner = owner

    # ---------- retrieval ----------

    def get_all_tasks(self) -> list[tuple[Pet, Task]]:
        """Collect every (pet, task) pair from the owner."""
        return self.owner.all_tasks()

    # ---------- sorting ----------

    def sort_by_time(self, pairs: list[tuple[Pet, Task]] | None = None) -> list[tuple[Pet, Task]]:
        """Return tasks sorted chronologically by start time."""
        if pairs is None:
            pairs = self.get_all_tasks()
        return sorted(pairs, key=lambda pair: pair[1].start_minutes())

    def sort_by_priority(self, pairs: list[tuple[Pet, Task]] | None = None) -> list[tuple[Pet, Task]]:
        """Return tasks sorted by priority (high first), then by start time."""
        if pairs is None:
            pairs = self.get_all_tasks()
        return sorted(
            pairs,
            key=lambda pair: (
                PRIORITY_ORDER.get(pair[1].priority, 1),
                pair[1].start_minutes(),
            ),
        )

    # ---------- filtering ----------

    def filter_by_pet(self, pet_name: str) -> list[tuple[Pet, Task]]:
        """Return tasks belonging to a single pet."""
        return [
            (pet, task)
            for pet, task in self.get_all_tasks()
            if pet.name.lower() == pet_name.lower()
        ]

    def filter_by_status(self, completed: bool) -> list[tuple[Pet, Task]]:
        """Return tasks matching a completion status."""
        return [
            (pet, task)
            for pet, task in self.get_all_tasks()
            if task.completed == completed
        ]

    # ---------- recurring tasks ----------

    def mark_task_complete(self, pet_name: str, description: str) -> Task | None:
        """Complete a pet's task by description.

        If the task is recurring ("daily"/"weekly"), automatically schedule
        the next occurrence and return the newly created Task. Returns None
        if the task was one-time or not found.
        """
        pet = self.owner.get_pet(pet_name)
        if pet is None:
            return None
        for task in pet.tasks:
            if task.description.lower() == description.lower() and not task.completed:
                task.mark_complete()
                follow_up = task.next_occurrence()
                if follow_up is not None:
                    pet.add_task(follow_up)
                return follow_up
        return None

    # ---------- conflict detection ----------

    def detect_conflicts(self) -> list[str]:
        """Return warnings for pending tasks whose time windows overlap.

        Two tasks conflict when they share a due date and their
        [start, start + duration) windows intersect. Pairwise comparison
        is O(n^2) but returns friendly warnings instead of crashing, which
        is a reasonable tradeoff for a household-sized task list.
        """
        warnings: list[str] = []
        pending = [(p, t) for p, t in self.get_all_tasks() if not t.completed]
        for i, (pet_a, task_a) in enumerate(pending):
            for pet_b, task_b in pending[i + 1:]:
                if task_a.due_date != task_b.due_date:
                    continue
                overlaps = (
                    task_a.start_minutes() < task_b.end_minutes()
                    and task_b.start_minutes() < task_a.end_minutes()
                )
                if overlaps:
                    warnings.append(
                        f"⚠️  Conflict on {task_a.due_date}: "
                        f"'{task_a.description}' ({pet_a.name}, {task_a.time}, {task_a.duration_minutes} min) "
                        f"overlaps '{task_b.description}' ({pet_b.name}, {task_b.time}, {task_b.duration_minutes} min)"
                    )
        return warnings

    # ---------- display ----------

    def todays_schedule(self) -> str:
        """Return a formatted, time-sorted plan for today with conflict warnings."""
        today = date.today()
        pairs = [
            (pet, task)
            for pet, task in self.sort_by_time()
            if task.due_date == today and not task.completed
        ]
        if not pairs:
            return "No tasks scheduled for today. 🎉"
        lines = [f"📅 Daily plan for {self.owner.name} — {today}", "-" * 60]
        for pet, task in pairs:
            lines.append(
                f"  {task.time} — {pet.name}: {task.description} "
                f"({task.duration_minutes} min) [priority: {task.priority}]"
            )
        for warning in self.detect_conflicts():
            lines.append(warning)
        return "\n".join(lines)