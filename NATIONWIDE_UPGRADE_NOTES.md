# Uni-Connect: Nationwide Multi-Institution Upgrade — Developer Notes

This document explains what changed when Uni-Connect was upgraded from a
University of Nigeria, Nsukka (UNN)-only forum into a platform that supports
**every Nigerian university, polytechnic, college of education, and
monotechnic**. The visual design, templates, CSS, JS, and existing features
were left untouched wherever possible — only the data model and the views/
forms/admin needed to become "school-aware."

## 1. What changed at the model level

- **New `School` model** (`forum/models.py`): name, short_name (e.g. "UNN",
  "UNILAG"), slug, school_type (University / Polytechnic / College of
  Education / Monotechnic), state, is_active.
- **`Department`** now has a `school` ForeignKey. `code` is no longer
  globally unique — it's unique **per school** (`unique_together =
  ['school', 'code']`), so two schools can both have a "CSC" or "LAW"
  department code without conflict.
- **`User`** (`accounts/models.py`) now has a `school` ForeignKey, alongside
  the pre-existing `department` ForeignKey.
- **`Thread.school`** and **`Thread.department`** convenience properties
  were added (derived from `thread.course.department`), so templates/views
  don't need extra joins written out by hand.
- A **`User.can_access_department(department)`** helper centralizes the
  cross-institution permission check used throughout the views.

## 2. Migration strategy (no data was lost)

Four migrations implement the upgrade safely:

1. `forum/0003_...` — creates the `School` table and adds `Department.school`
   as **nullable** (so existing rows aren't broken), plus the new
   `unique_together`.
2. `forum/0004_backfill_default_school.py` — a **data migration** that
   creates a `School` row for "University of Nigeria, Nsukka" (short name
   `UNN`) and attaches every pre-existing `Department` that doesn't already
   have a school to it.
3. `accounts/0004_user_school.py` — adds the nullable `User.school` field.
4. `accounts/0005_backfill_user_school.py` — a **data migration** that gives
   every existing user a school: inherited from their department if they had
   one, otherwise defaulted to UNN.

Run them the normal way:

```bash
python manage.py migrate
```

This was tested against the real `db.sqlite3` shipped in this project: all
26 users, 9 departments, 18 courses, and 18 threads were preserved, and every
row now has a `school` correctly assigned.

If you are deploying against Postgres/another database, the same migrations
apply unchanged.

## 3. New/updated features

- **Registration** (`accounts/forms.py`, `templates/accounts/register.html`)
  now asks for **School** and **Department**, with the department dropdown
  populated live via `fetch()` against a new JSON endpoint
  (`accounts:ajax_load_departments`) — no page reload, matches the existing
  requirement to use Fetch API + `JsonResponse`.
- **Edit profile** works the same way, and lets a user change their school
  (e.g. transfer students) with the department list narrowed automatically.
- **Discussion creation** (`forum/views.py: create_thread`,
  `forum/forms.py: ThreadForm`) automatically limits the course picker to
  the logged-in user's own department/school — students can't manually pick
  a course from another institution, and the form's `clean_course()` rejects
  it server-side even if someone tampers with the submitted value.
- **Filtering everywhere**: `home`, `department_list`, `department_detail`,
  `course_detail`, `thread_list`, `thread_detail`, and `add_reply` all check
  `request.user.can_access_department(...)` or filter querysets by
  `request.user.school`. Anonymous/legacy users without a school set are not
  blocked (backward compatible).
- **Browsing across institutions**: `thread_list` defaults to the user's own
  school, but a "Include other institutions" checkbox (`?scope=all`) lets
  students opt into browsing every school's discussions — this satisfies
  "optionally show results from other schools if configured" from the
  requirements without hiding the toggle behind a page reload.
- **Search**: `SearchForm` gained a `department` filter (previously the
  "View All" link on a department page passed `?department=<id>` but the
  view silently ignored it — now fixed).
- **Admin panel** (`forum/admin.py`, `accounts/admin.py`): new `SchoolAdmin`
  with search/filter/list_display; `DepartmentAdmin` now filters/searches by
  school and uses `autocomplete_fields`; `CourseAdmin` and `ThreadAdmin`
  gained school-aware `list_filter`s; `CustomUserAdmin` shows/filters by
  school.
- **Seed scripts** (`seed.py`, `seed_expanded.py`) were updated to create the
  UNN school explicitly, and `seed_expanded.py` now also seeds a second
  demo institution (University of Lagos) with its own department, course,
  student, and thread — useful for manually verifying that cross-school
  isolation works.

## 4. Bugs fixed while upgrading (not related to the school feature)

- `accounts/views.py` imported `PasswordResetRequestForm`/
  `PasswordResetConfirmForm` but used `VerifyOTPForm` without importing it —
  a `NameError` waiting to happen if that view were ever wired up. Fixed the
  import.
- `SearchForm.q` was a **required** field. On the thread list page, if a
  user submitted the Course or Status filter without typing a search term,
  the whole form failed validation and *all* filters were silently ignored.
  `q` is now `required=False`.
- `department_detail.html`'s "View All" link already sent `?department=<id>`
  to the thread list, but `SearchForm`/`thread_list` had no `department`
  field to receive it. Added.
- `Department.code` was globally `unique=True`, which would have made it
  impossible for two different schools to both have, say, a "CSC"
  department. Changed to unique-per-school.

## 5. Testing performed

A full automated smoke test (Django test client against a throwaway test
database, seeded with two schools) verified:

- Registration page loads and successfully creates a user with the correct
  school/department.
- The AJAX department-loading endpoint returns only the departments for the
  requested school.
- Registering with a department that doesn't belong to the selected school
  is rejected.
- `thread_list` shows only the logged-in user's school by default, and shows
  every school's threads with `?scope=all`.
- Visiting another school's thread directly is blocked with a friendly
  message.
- The department listing and thread-creation pages render correctly.
- Submitting a thread-creation form with a tampered `course` id from another
  school is rejected.
- The Django admin's School, Department, and User list pages all load.

In addition:

- `python manage.py check` — no issues.
- The full existing SQLite database (26 users / 9 departments / 18 courses
  / 18 threads) was migrated in place with zero data loss, and the dev
  server was smoke-tested against it (`/`, `/departments/`,
  `/accounts/register/`, `/accounts/login/`, `/threads/`, `/admin/` all
  returned the expected status codes with no server errors in the log).

### Manual checklist for your own verification

- [ ] Register a new account for a school other than UNN and confirm the
      department dropdown updates without a page reload.
- [ ] Log in as a student from School A; confirm the thread list, home page,
      and department list only show School A's content by default.
- [ ] Tick "Include other institutions" and confirm School B's content
      appears too.
- [ ] Try to open a School B thread's URL directly while logged in as a
      School A student — you should be redirected with an error message.
- [ ] Create a new thread — confirm the course dropdown only shows courses
      from your own department/school.
- [ ] In Django admin, add a brand-new School (e.g. "Federal University of
      Technology, Minna") and a Department under it, then register a student
      for that school/department and confirm the whole flow works with no
      code changes.
- [ ] Confirm existing UNN users, threads, and replies still display
      correctly (nothing was deleted or renamed).

## 6. What was intentionally left unchanged

Per the "do not redesign" requirement: no CSS, color palette, Bootstrap/GSAP
usage, animations, icons, images, or template layout structure were altered
beyond adding the minimum new form fields/labels needed for School and
Department, and one line of marketing copy that referenced UNN by name
("Join UNN students..." → "Join students from universities, polytechnics,
and colleges of education across Nigeria...").

---

## 7. Second pass: nationwide data population + feature verification

You added 19 real Nigerian institutions through the admin panel (10
universities, 4 polytechnics, 3 colleges of education, 2 monotechnics).
This pass populates them with real departments/courses and re-verifies
every core feature, including the two you specifically asked about:
**forgot password** and **chat**.

### What was added: `seed_nationwide.py`

A new, idempotent script (safe to re-run — it only ever creates missing
rows, never duplicates) that, for every `School` already in your database:

- Creates a realistic set of **departments**, templated by institution type:
  - **Universities** (10 depts): Computer Science, Mechanical Engineering,
    Medicine & Surgery, Economics, Law, English & Literary Studies,
    Mathematics, Physics, Accountancy, Political Science.
  - **Polytechnics** (7 depts): Computer Science, Accountancy, Business
    Administration & Management, Mass Communication, Estate Management,
    Electrical/Electronics Engineering Technology, Mechanical Engineering
    Technology.
  - **Colleges of Education** (6 depts): Educational Foundations, English
    Education, Mathematics Education, Integrated Science Education, Social
    Studies Education, Computer Science Education.
  - **Monotechnics**: matched to the specific institution where recognizable
    (e.g. the Federal College of Fisheries & Marine Technology gets
    Fisheries Technology / Nautical Science / Marine Engineering; the
    Nigerian College of Aviation Technology gets Aircraft Maintenance
    Engineering / Air Traffic Control / Aviation Management), with a
    generic fallback for any other monotechnic.
- Creates **2 courses per department** (an intro 200-level and a
  300-level).
- Creates **1 demo student per school** (plus 1 demo lecturer for
  universities), correctly assigned to that school and one of its
  departments. All demo student passwords are `student123`; demo lecturer
  passwords are `lecturer123`.
- Creates **1 starter discussion thread per school**, so every institution
  has visible activity instead of an empty department page.

Run it any time with:
```bash
python manage.py shell < seed_nationwide.py
# or, equivalently:
python seed_nationwide.py
```

**Result:** 19 schools → **152 departments, 311 courses, 55 users, 37
threads.** Your original UNN data (26 users, 9 departments, 18 courses, 18
threads) is untouched and still present — nothing was deleted or
overwritten.

Demo student logins you can use to click around as different institutions
(all password `student123`), following the pattern
`{firstname}_{lastname}_{schoolslug}_student` — e.g.:

| Username | Institution | Department |
|---|---|---|
| `chinedu_okafor_absu_student` | ABSU | Computer Science |
| `ibrahim_adewale_abu_student` | ABU (Ahmadu Bello) | Computer Science |
| `funmilayo_garba_unilag_student` | "UNILAG" (as labeled in your data — see note below) | Computer Science |
| `chiamaka_abubakar_futa_student` | FUTA | Computer Science |
| `ngozi_yusuf_fcfmt_student` | FCFMT (Fisheries & Marine) | Fisheries Technology |
| `sani_adeyemi_ncat_student` | NCAT (Aviation) | Aircraft Maintenance Engineering |
| `amaka_bello_unn_student` | UNN | Computer Science |

Existing admin login is unchanged: `admin` / `admin123`.

> **Data note, not a bug:** one of the schools you entered is named "Lagos
> State University" but was given the short name `UNILAG`. In Nigeria those
> are two different institutions (Lagos State University = LASU; University
> of Lagos = UNILAG). I left your entry exactly as you typed it rather than
> silently changing data you added yourself — worth a quick look in
> `/admin/forum/school/` if that was a typo.

### Forgot password — verified working end-to-end

Tested the full OTP-based reset flow with Django's test client against
your real, seeded database:

- [x] Requesting a reset for a valid email creates a 6-digit OTP code and
      queues an email (using the file-based email backend in dev, written
      to `sent_emails/` — switch `EMAIL_BACKEND` to SMTP for production so
      these actually arrive in inboxes)
- [x] Requesting a reset for an email that doesn't exist is handled
      gracefully (no crash, no account-existence leak)
- [x] Submitting the wrong OTP code is rejected and the password stays
      unchanged
- [x] Submitting the correct OTP code changes the password successfully
- [x] A used OTP code is marked `is_used` and cannot be replayed a second
      time
- [x] The 20-minute OTP expiry (`OTPCode.is_valid()`) is honored

No bugs found in this flow — it already worked correctly; this was a
verification pass, not a rewrite.

### Chat — verified working end-to-end

- [x] Chat list page loads for a logged-in user
- [x] Starting a chat with another user (via `/chats/start/<username>/`)
      creates a `ChatRoom` with both participants
- [x] Re-opening a chat with the same person reuses the existing room
      instead of creating a duplicate
- [x] Sending a message persists it and displays it in the room
- [x] A user who is **not** a participant in a room is redirected away if
      they try to view it directly by URL
- [x] Attempting to start a chat with yourself is handled gracefully
- [x] Confirmed chatting works **between users at different institutions**
      (e.g. a UNN student and a student at the "UNILAG"-labeled school) —
      direct messaging was intentionally left nationwide/unscoped, unlike
      discussion threads, since DMs are a personal feature rather than a
      school discussion board. Let me know if you'd rather restrict DMs to
      same-school only.

No bugs found here either — verified rather than rewritten.

### Full-coverage regression scan

Beyond the two features called out specifically, every single department,
course, and thread page across all 19 schools was checked:

```
Checked 152 departments, 311 courses, 37 threads.
NO ERRORS — every department/course/thread page returns 200 OK
```

`python manage.py check` and a real `manage.py runserver` smoke test both
came back clean on the final database.

---

## 8. UNILAG / LASU naming fix

The school you'd entered as "Lagos State University" with short name
`UNILAG` has been corrected:

- **School #2** is now correctly named **"University of Lagos"** (short
  name `UNILAG` — these now actually match). All of its existing
  departments, courses, and its demo student/lecturer accounts were kept
  exactly as they were; only the school's display name and slug changed,
  so nothing was lost.
- **A new, separate School** was added for the real **"Lagos State
  University"** (short name `LASU`, Lagos state), since that's a genuinely
  different institution from the University of Lagos. It was seeded with
  the same 10 standard university departments, 20 courses, a demo student
  (`tunde_eze_lasu_student` / `student123`), a demo lecturer
  (`aisha_danladi_lasu_lecturer` / `lecturer123`), and a starter welcome
  thread — exactly like every other school.

You now have **20 schools** total (162 departments, 331 courses, 57 users,
38 threads), with UNILAG and LASU both present and correctly distinguished.

### Bug found and fixed while doing this: unstable demo-account naming

The first pass at re-running `seed_nationwide.py` after adding LASU
revealed a real bug in the script itself (not in the Uni-Connect
application): demo student/lecturer usernames were being picked from a
name list using a counter that incremented as the script walked through
schools in alphabetical order. Inserting a new school anywhere in that
alphabetical order shifted every subsequent school's counter position,
which meant every school after the insertion point got a **brand-new**
demo account instead of reusing its original one (the old account wasn't
deleted, so this silently doubled up several schools' users and welcome
threads).

Fixed by making the account lookup **pattern-based first**: the script now
searches for an existing username ending in `_<school-slug>_student` (or
`_lecturer`) for that school before ever generating a new name, and only
falls back to picking a name (deterministically, from the school's own
database ID rather than its position in a loop) if no such account exists
yet. I verified the fix three ways:

1. Ran the script twice in a row on the same data — identical usernames
   and identical totals both times (57 users, 38 threads either way).
2. Added a temporary extra school in the middle of the alphabetical order
   and re-ran — every pre-existing school's demo username stayed exactly
   the same; only the new school got new accounts.
3. Removed the temporary school again and confirmed the database returned
   to the expected clean totals (20 schools / 162 departments / 331
   courses / 57 users / 38 threads).

`seed_nationwide.py` is now safe to re-run at any time, in any order, as
you add more schools in the future.

---

## 9. Forgot-password and chat verified across all 20 schools

You asked specifically for this to be confirmed for *every* school, not
just a couple of spot checks — so it was tested exhaustively rather than
sampled.

### Forgot password — every school, individually

For each of the 20 schools' demo student accounts, the full cycle was run
end-to-end: request a reset → confirm a wrong code is rejected and the
password stays unchanged → confirm the correct code resets the password
successfully → restore the demo password back to `student123` afterward.

```
Forgot-password: 20/20 schools PASSED
```

### Chat — every school, chained together

Rather than testing chat in isolation per school (which wouldn't prove
anything about cross-institution messaging), each school's demo student
was chatted in a ring with the *next* school's demo student (school 1 ↔
school 2, school 2 ↔ school 3, ... wrapping back to school 1) — 20 pairs
covering every single school at least once, sending and persisting a real
message across the institution boundary each time.

```
Chat: 20/20 pairs PASSED
```

This also means your seeded database now has real, illustrative chat
activity between students at different institutions nationwide (32 chat
rooms, 48 messages) — a nice demonstration that direct messaging works
platform-wide, not just within one school, when you show this off.

No bugs were found in this pass — both features already worked correctly
for every school; this was a full verification sweep rather than a fix.
All demo account passwords (`student123` / `lecturer123` / `admin123`)
were restored to their documented values afterward.

---

## 10. Real email delivery for password reset (and email verification)

Previously, `EMAIL_BACKEND` was tied to `DEBUG`: in development it always
wrote emails to `.eml` files under `sent_emails/` and never actually sent
anything, regardless of whether you wanted real delivery. That's now fixed.

### What changed

- **`.env` support added.** `settings.py` now loads a `.env` file
  automatically via `python-dotenv` (already in `requirements.txt`, just
  wasn't wired up). Copy `.env.example` to `.env` and fill in your SMTP
  credentials — no other setup required.
- **Real SMTP is used whenever credentials are present — in dev or
  production alike.** The backend selection is no longer based on `DEBUG`:
  if `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD` are set (via `.env` or
  real environment variables), Django sends real emails over SMTP. If
  they're not set, it falls back to the file-based backend in development
  (so local dev never breaks) or the console backend in production (so
  failures are at least visible in your server logs instead of vanishing
  silently).
- **`.env.example`** walks through the two most common setups:
  - **Gmail** (free, quickest for a student project): enable 2-Step
    Verification, generate an **App Password** at
    https://myaccount.google.com/apppasswords, and use that 16-character
    password — not your normal Gmail password (Gmail rejects normal
    passwords for SMTP).
  - **SendGrid / Mailgun / Outlook / any other SMTP provider**: use the
    SMTP host, port, and API-key credentials they give you.
- **New management command to verify your setup before relying on it:**
  ```bash
  python manage.py send_test_email you@example.com
  ```
  This prints which backend is active and either confirms a real email was
  sent or gives a specific, actionable error (wrong credentials, wrong
  port, using a normal password instead of an App Password, etc.) instead
  of a raw traceback.
- **Failures are no longer silently swallowed.** Previously,
  `send_mail(..., fail_silently=True)` meant a broken SMTP configuration
  would look successful to the user — they'd be told "check your email"
  even though nothing was sent, and the OTP code would exist with no way
  to receive it. Now:
  - `send_otp_email()` catches SMTP/network errors, logs them, and returns
    `True`/`False` instead of assuming success.
  - If sending fails, the just-created OTP code is deleted again (no
    orphaned, undeliverable codes sitting in the database).
  - The password-reset (and email-verification) views check this result:
    on success the user sees "Check your email for the password reset
    code"; on failure they see a clear error asking them to try again,
    and they are **not** advanced to the "enter your code" screen with no
    way to actually get a code.
- **`.gitignore` added**, including `.env`, so real SMTP credentials are
  never accidentally committed.

### Verified

- With no SMTP credentials configured: confirmed the file-based fallback
  still works exactly as before (regression check) — request → OTP
  created → confirm → password changed successfully, `.eml` file written
  to `sent_emails/`.
- With SMTP credentials configured (fake ones, since this sandbox has no
  outbound SMTP access to test real delivery): confirmed Django correctly
  switches to the SMTP backend, confirmed a connection failure is caught
  and logged rather than crashing the request, confirmed the OTP row is
  rolled back, and confirmed the user sees the friendly error toast
  ("We couldn't send the reset email right now...") instead of a false
  "check your email" success message.
- `python manage.py send_test_email` tested in both the no-credentials
  and fake-credentials states — correctly reports which backend is active
  and gives an actionable error message on failure.

### To actually receive real emails

1. `cp .env.example .env`
2. Fill in `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` (Gmail App Password is
   the fastest option — see `.env.example` for the exact steps).
3. `python manage.py send_test_email you@example.com` — confirm you
   receive it.
4. That's it — `/accounts/password-reset/` will now send real emails with
   no further code changes.
