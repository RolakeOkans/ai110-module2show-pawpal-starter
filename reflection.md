# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

I used four classes: Task (one activity with its time, duration, priority, and
status), Pet (pet info plus its list of tasks), Owner (holds the pets), and
Scheduler (does the sorting, filtering, conflicts, and recurring tasks). I kept
all the logic in Scheduler so the other classes stay simple.

**b. Design changes**

Yes. I added due_date to Task once I realized recurring tasks need it, otherwise
today's walk and tomorrow's walk look identical. I also added duration_minutes so
conflicts could catch overlapping tasks instead of only exact same times.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

It considers time, duration, priority, frequency, and completion status. Time and
duration mattered most because the main question is "what's next and does anything
collide." Priority is a second way to sort the list.

**b. Tradeoffs**

Conflict detection compares every pair of tasks, which is slow in theory, but a
pet owner only has a handful of tasks, so I picked the simple version I could
actually read and verify.

---

## 3. AI Collaboration

**a. How you used AI**

Mostly chat. I had it draft the UML, generate the classes, and explain things like
st.session_state before I used them. I pasted the code into VS Code and ran it
myself. Specific prompts with my actual code in them worked way better than vague
ones.

**b. Judgment and verification**

The first conflict detection only caught exact time matches, but the README said
"overlapping time slots," so I had it redone with start + duration math. I checked
it with a test where a feeding starts in the middle of a walk (should flag) and
one where a task starts exactly when another ends (should not flag).

---

## 4. Testing and Verification

**a. What you tested**

11 tests: completing tasks, adding tasks, time sorting, priority sorting, daily
recurrence, one-time tasks not recurring, conflicts (same time, overlapping, and
back-to-back which shouldn't flag), filtering, and a pet with no tasks. These
matter because if the sorting or conflict logic broke, the app would still run
but give a wrong plan.

**b. Confidence**

4/5. The main logic is well tested. Next I'd test tasks crossing midnight and bad
time input like "25:99".

---

## 5. Reflection

**a. What went well**

Testing the logic in main.py before touching Streamlit. When the UI broke I knew
it was a UI problem, not a logic problem.

**b. What you would improve**

Persistence. Everything resets when the app restarts, so I'd add saving to JSON.
I'd also want conflicts to suggest a new time instead of just warning.

**c. Key takeaway**

AI writes code fast, but I still had to make the design decisions and use tests
to check that what it gave me actually worked.