"""CLI demo for PawPal+ — verifies the logic layer end to end."""

from pawpal_system import Owner, Pet, Scheduler, Task


def main() -> None:
    # --- setup: one owner, two pets ---
    owner = Owner(name="Jordan")
    mochi = Pet(name="Mochi", species="dog", age=3)
    biscuit = Pet(name="Biscuit", species="cat", age=5)
    owner.add_pet(mochi)
    owner.add_pet(biscuit)

    # --- add tasks deliberately OUT of order to prove sorting works ---
    mochi.add_task(Task("Evening walk", "18:00", duration_minutes=30, priority="medium", frequency="daily"))
    mochi.add_task(Task("Morning walk", "08:00", duration_minutes=30, priority="high", frequency="daily"))
    mochi.add_task(Task("Vet appointment", "14:30", duration_minutes=45, priority="high", frequency="once"))
    biscuit.add_task(Task("Litter box cleaning", "09:15", duration_minutes=10, priority="low", frequency="daily"))
    # Starts during Mochi's 08:00-08:30 walk -> overlap conflict
    biscuit.add_task(Task("Feeding", "08:15", duration_minutes=10, priority="high", frequency="daily"))

    scheduler = Scheduler(owner)

    # --- today's plan (time-sorted, with conflict warnings) ---
    print(scheduler.todays_schedule())

    # --- priority-based ordering ---
    print("\n⭐ Priority ordering (high first, then by time):")
    for pet, task in scheduler.sort_by_priority():
        print(f"  [{task.priority:^6}] {task.time}  {pet.name}: {task.description}")

    # --- filtering demos ---
    print("\n🔍 Filter: Mochi's tasks only")
    for pet, task in scheduler.filter_by_pet("Mochi"):
        print(f"  {task}")

    # --- recurring task demo ---
    print("\n✅ Completing Mochi's daily 'Morning walk'...")
    follow_up = scheduler.mark_task_complete("Mochi", "Morning walk")
    if follow_up:
        print(f"  Recurring task auto-rescheduled: {follow_up}")

    print("\n🔍 Filter: completed tasks")
    for pet, task in scheduler.filter_by_status(completed=True):
        print(f"  {pet.name}: {task}")

    # --- conflict detection after completion ---
    print("\n🚨 Conflict check after completing the walk:")
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        for warning in conflicts:
            print(f"  {warning}")
    else:
        print("  No conflicts remain — the overlapping walk is done.")


if __name__ == "__main__":
    main()