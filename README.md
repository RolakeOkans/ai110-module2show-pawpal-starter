## 🖥️ Sample Output

```
📅 Daily plan for Jordan — 2026-07-08
------------------------------------------------------------
  08:00 — Mochi: Morning walk (30 min) [priority: high]
  08:15 — Biscuit: Feeding (10 min) [priority: high]
  09:15 — Biscuit: Litter box cleaning (10 min) [priority: low]
  14:30 — Mochi: Vet appointment (45 min) [priority: high]
  18:00 — Mochi: Evening walk (30 min) [priority: medium]
⚠️  Conflict on 2026-07-08: 'Morning walk' (Mochi, 08:00, 30 min) overlaps 'Feeding' (Biscuit, 08:15, 10 min)

⭐ Priority ordering (high first, then by time):
  [ high ] 08:00  Mochi: Morning walk
  [ high ] 08:15  Biscuit: Feeding
  [ high ] 14:30  Mochi: Vet appointment
  [medium] 18:00  Mochi: Evening walk
  [ low  ] 09:15  Biscuit: Litter box cleaning

✅ Completing Mochi's daily 'Morning walk'...
  Recurring task auto-rescheduled: [•] 08:00  Morning walk (30 min, high, daily, due 2026-07-09)

🚨 Conflict check after completing the walk:
  No conflicts remain — the overlapping walk is done.
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest
```

The suite covers: task completion, task addition, chronological sorting, priority-first
sorting, daily recurrence, one-time tasks not recurring, same-time conflicts,
duration-overlap conflicts, the back-to-back non-conflict boundary case, filtering
by pet/status, and the empty-pet edge case.

Sample test output:

```
============================= test session starts ==============================
collected 11 items

tests/test_pawpal.py::test_mark_complete_changes_status PASSED           [  9%]
tests/test_pawpal.py::test_adding_task_increases_pet_task_count PASSED   [ 18%]
tests/test_pawpal.py::test_sort_by_time_returns_chronological_order PASSED [ 27%]
tests/test_pawpal.py::test_sort_by_priority_puts_high_first PASSED       [ 36%]
tests/test_pawpal.py::test_daily_recurrence_creates_next_day_task PASSED [ 45%]
tests/test_pawpal.py::test_one_time_task_does_not_recur PASSED           [ 54%]
tests/test_pawpal.py::test_conflict_detection_flags_same_start_time PASSED [ 63%]
tests/test_pawpal.py::test_conflict_detection_flags_overlapping_durations PASSED [ 72%]
tests/test_pawpal.py::test_no_conflict_for_back_to_back_tasks PASSED     [ 81%]
tests/test_pawpal.py::test_filter_by_pet_and_status PASSED               [ 90%]
tests/test_pawpal.py::test_edge_case_pet_with_no_tasks PASSED            [100%]

============================== 11 passed in 0.03s ==============================
```

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time()`, `Scheduler.sort_by_priority()` | Time sort uses a lambda key on minutes-since-midnight; priority sort orders high → medium → low, tie-broken by time |
| Filtering | `Scheduler.filter_by_pet()`, `Scheduler.filter_by_status()` | Isolate one pet's tasks, or completed vs. pending |
| Conflict handling | `Scheduler.detect_conflicts()` | Duration-aware: flags any two pending same-day tasks whose [start, start+duration) windows overlap; returns warnings instead of raising |
| Recurring tasks | `Scheduler.mark_task_complete()` + `Task.next_occurrence()` | Completing a daily/weekly task creates the next occurrence via `timedelta` |

## 📸 Demo Walkthrough

1. Enter the owner's name, then add a pet (name + species) — this creates a real `Pet` object stored on an `Owner` in `st.session_state`, so it persists across reruns.
2. Add tasks for a pet: title, time, duration, priority, and frequency. Each submission calls `Pet.add_task()` with a `Task` dataclass instance.
3. Add a second task that overlaps the first in time (e.g., a 30-min walk at 08:00 and a feeding at 08:15) — the Scheduler surfaces a ⚠️ conflict warning via `st.warning`.
4. Click **Generate schedule** — the plan renders as a table sorted by time or by priority (toggle), with duration, priority, due date, and status columns.
5. Use **Complete a Task** on a daily task — a success message confirms the recurrence, and regenerating the schedule shows the new copy due tomorrow.

**Screenshot or video** *(optional)*: —