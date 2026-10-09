# Feature: Course Catalog Database Migration

**Feature name:** `course-catalog-db-migration`
**Status:** planned (not started)
**Created:** 2026-10-08
**Objective:** Make the new course catalog database the only source of course data, and drive
notifications from `courses.updated_at` instead of `courses.modified_date`.

## Problem

The bot currently owns and populates the course data itself. It scrapes eMOVIES and AUSJAL,
translates their catalog codes into hand-maintained integer IDs
(`src/config/defaultValuesCatalog.py`, 315 lines), and writes into a `courses` table it created
via `scripts/seed.py`. Notification freshness is decided by `courses.modified_date`, a nullable,
unindexed `DATE` that is the sole freshness predicate and ordering key of both hot queries.

That ownership model is being replaced. An external system now owns the course catalog and
publishes it in a different schema. The bot becomes a **read-only consumer** of courses.

## Why

- The catalog is no longer the bot's responsibility; maintaining 183 universities, 72
  disciplinary fields and 17 countries by hand produced permanent translation bugs
  (`languages.id = 4` does not exist; AUSJAL level key `"education_levels"` does not exist;
  AUSJAL universities map is empty; eMOVIES `country` is always `NULL`).
- The new schema is institution-aware (`campus -> university -> city -> country`) and carries
  richer data (`modality`, `credits`, `available_seats`, `course_files`).
- `updated_at` is maintained by the owning system, so freshness no longer depends on how the bot
  scraped or translated a date.

## Confirmed decisions

1. **Two databases.** The new database is read-only for courses and their catalogs.
   `chatconfigs` and the per-user filters stay in the current database. Filter matching moves
   from a SQL `CROSS JOIN` to Python. Two connections are open.
2. **The external system writes courses.** Scraping, source repositories and all catalog
   translation are removed. The bot only reads.
3. **Notification message keeps today's shape.** The date line now shows `updated_at`.

### Consequences of decision 1

`chatconfigs` is the only remaining table of the old database. Its filter columns change from
integer foreign keys into the **natural keys of the new database**, because the old catalogs and
the new catalogs have unrelated ID spaces and there is no cross-database foreign key:

| Filter | Old column (INT FK) | New column | Value stored |
|---|---|---|---|
| country | `uni_countries` | `country_iso_code` | `countries.iso_code` (unique) |
| university | `course_university` | `course_university` | `universities.name` (unique) |
| language | `uni_languages` | `course_language_code` | `languages.code` (PK) |
| course level | `course_levels` | `course_level_id` | `academic_levels.id` (PK, text) |
| disciplinary field | `disciplinary_field` | `disciplinary_field` | `knowledge_areas.name` (unique) |

`lastrevision` changes from `DATE` to `TIMESTAMPTZ`, because `updated_at` is a timestamp.
Its default changes from `CURRENT_DATE` to `now()`; both mean "no backlog", `now()` is the
correct expression for a timestamp column.

### Consequences of decision 3

Forced by the new schema, not optional:

- `study_hours` does not exist in the new schema, so the **"Horas de estudio" line is removed**.
- `slots` maps to `courses.available_seats`.
- `modality`, `credits`, `instructions` and `course_files` exist but are **not shown** (decision 3).

## Scope

**In scope:** dual connection layer, read-only course repository, filter matching in Python,
watermark on `updated_at`, `chatconfigs` DDL and data migration, filter UI reading catalogs from
the new database, removal of the scraping pipeline, documentation.

**Out of scope:** Prisma, TypeScript, any ORM. The pasted Prisma schema is the *contract
description* of the target database; this Python client keeps using raw `psycopg`.
Changing the new database's DDL, seeds, or who owns it. `agreements` filtering.
Reviving the university filter in the UI (the column stays, with no UI, preserving today's
behavior). The four empty use-case files (`getLastUpdateUseCase.py`, `getUserCountUseCase.py`,
`resetFiltersUseCase.py`, `sendFiltersToUserUseCase.py`) are left untouched.

## Constraints

- Preserve clean architecture layering and the repo's folder names (`aplication`,
  `infraestructure`, `repositoryImp`).
- Keep the single-writer rule: one work-unit commit per task, directly on `main`, no feature
  branch and no PR chain.
- `autocommit=True` stays; the new database is never written to.
- No test infrastructure exists in the repository. TDD is **off** (no project configuration
  enables it), so each task runs ordinary functional checks. See Task 9.

## Reference: old -> new field mapping

| `ShowCourseModel` | Old column | New column |
|---|---|---|
| `source` | `courses_sources.source` | `sources.name` |
| `university` | `universities.university` | `universities.name` (via campus) |
| `country` | `countries.country` | `countries.name` (via campus -> city) |
| `language` | `languages.language` | `languages.name` |
| `disciplinaryFields` | `course_disciplinary_fields` | `course_knowledge_areas` -> `knowledge_areas.name` |
| `courseLevel` | `course_levels.course_level` | `academic_levels.name` |
| `title` | `courses.title` | `courses.title` |
| `url` | `courses.url` | `courses.site_url` |
| `startClassDate` | `courses.start_class_date` | `courses.course_start` |
| `endClassDate` | `courses.end_class_date` | `courses.course_end` |
| `startInscriptionDate` | `courses.start_inscription_date` | `courses.enrollment_start` |
| `endInscriptionDate` | `courses.end_inscription_date` | `courses.enrollment_end` |
| `description` | `courses.description` | `courses.description` |
| `studyHours` | `courses.study_hours` | **does not exist — line removed** |
| `slots` | `courses.slots` | `courses.available_seats` |
| `modifiedDate` | `courses.modified_date` | `courses.updated_at` |

## Tasks

Route per task is recorded from the mandatory delegation triggers.

### [x] T1 — Dual connection layer
**Route:** direct inline (2 mechanical files, no research).
**Route:** direct inline (2 mechanical files, no research).
- `src/infraestructure/dbConnection.py`: keep `get_db_connection()` for the `chatconfigs`
  database; add `get_courses_db_connection()` for the new database, reading `COURSES_DB_URL`.
  Both use the existing retry policy; keep `row_factory=dict_row`.
- `.env.example`: add `COURSES_DB_URL`; remove `EMOVIES_PAGE_RETRIES` and the stale
  `EMOVIES_BROWSER_COUNT` from the real `.env`.
- **Check:** both factories raise a clear error naming the missing variable; importing the
  module does not open a connection.
- **Verified:** importing the module opens no connection; both factories return live, distinct
  connections; each is reused as a singleton; an empty-but-present variable raises
  `Falta variable de entorno <NAME>` and registers no connection. `DB_URL` resolves to
  `electiveNotifier_db` and `COURSES_DB_URL` to `ElectivaInternacional`.
- **Commit:** see Progress.

### [x] T2 — Domain contracts and models
**Route:** delegated writer (4 files).
- New `src/domain/repository/coursesRepository.py`: read-only `CoursesRepository` ABC with
  `getCoursesUpdatedAfter(moment: datetime) -> List[CourseRecordDto]`,
  `getKnowledgeAreasByCourseIds(ids) -> Dict[str, List[str]]`,
  `getCountryCatalog()`, `getUniversityCatalog()`, `getLanguageCatalog()`,
  `getAcademicLevelCatalog()`, `getKnowledgeAreaCatalog()`.
- `src/domain/model/courseModel.py`: rename `modifiedDate` -> `updatedAt`, type `datetime`;
  drop `studyHours`; keep the rest of `ShowCourseModel`. Add `CourseRecordDto` (flat row shape).
- `src/domain/model/chatConfigModel.py`: filter fields become optional strings;
  `lastRevision: Optional[datetime]`.
- `src/domain/repository/databaseRepository.py`: `DatabaseRepository` keeps only the
  chat-config methods; drop `deleteCoursesBySource`, `saveCourses`, `getCourses`,
  `DatabaseCourseFilters`, `ChatNewCourses`.
- **Check:** no remaining import references the removed contract members.
- **Verified:** domain layer imports cleanly; `buildMessage()` output is byte-identical to today's
  except the "Horas de estudio" line is gone and the date line reads `updated_at`. A course with
  no country (51% of the catalog) simply omits the country line. `CourseRecordDto` accepts only
  `id` and `updatedAt`.
- **Deliberate:** `CourseModel` (the scraper output model) was left untouched. Renaming it would
  break five files that T7 deletes anyway, so the breakage surface stays limited to the file that
  genuinely had to change.
- **Known temporary breakage, fixed in T4/T5:** `postgresDatabaseRepositoryImp.py`,
  `chatConfigMapper.py`, `chatConfigsDto.py`, `updateUserFilterUseCase.py`,
  `sendCourseToSubcriptorsUseCase.py`, `syncCoursesUseCase.py`, `filtersCommand.py`.
- **Commit:** see Progress.

### [x] T3 — chatconfigs DDL and data migration
**Route:** delegated writer (script + seed).
- `scripts/seed.py`: drop all course DDL and all catalog DDL; keep only the `chatconfigs`
  table with the new column types and `now()` default.
- New `scripts/migrate_chatconfigs_filters.py`: for each existing `chatconfigs` row, look up the
  old INT value in the old catalog tables, then resolve the equivalent natural key in the new
  database by name. **Unresolvable values become `NULL` (filter widened to "any") and are listed
  in a per-value report.** Chats, subscriptions and resolvable filters are preserved.
- **Check:** the script is idempotent and prints a per-value report of what resolved and what did
  not.
- **Applied to the live database.** `chatconfigs` renamed to `chatconfigs_legacy`, new schema
  created, 12 rows migrated, **`chatconfigs_legacy` retained as a safety net** and NOT dropped.
  The old `courses` (2893 rows), `course_disciplinary_fields`, `courses_sources` and the five
  catalog tables are untouched.
- **Verified:** 12 rows in, 12 out; 7 subscribed preserved; no `lastrevision` or `is_subscribed`
  differs from legacy; every surviving filter value resolves in the new database; the `CO` filter
  matches 721 real courses. Idempotent: a second run skips with exit 0, a missing table exits 1
  with a message and no traceback.
- **Migration result: zero losses.** All 16 filter values in use resolved. The known `Brazil`
  failure exists in the catalog but no chat used country id 4.
- **Note:** `seed.py`'s unused `insert()` helper was removed after review rather than left as
  dead code.
- **Commit:** see Progress.

### [x] T4 — Course repository implementation and mapper
**Route:** delegated writer (2 non-trivial files, SQL-heavy).
- New `src/infraestructure/repositoryImp/coursesRepositoryImp.py`:
  - Candidate query: `courses` joined to `campuses`, `universities`, `cities`, `countries`,
    `languages`, `academic_levels`, `sources`, filtered by `is_active = TRUE AND updated_at > %s`,
    `ORDER BY updated_at DESC`.
  - Knowledge areas in a **second** query by course id — joining the M:N into the main query
    would multiply rows and break the flat row mapping, and it avoids today's N+1 correlated
    `string_agg`.
  - Catalog reads for the filter UI.
- New `src/infraestructure/mapper/courseRecordMapper.py`: row -> `CourseRecordDto` ->
  `ShowCourseModel`, applying the table above.
- **Check:** the queries run against the new database and the row mapping is asserted against a
  representative fixture row.
- **Verified against live data:** 1409 courses updated after 2026-10-05, matching a plain SQL
  count. All 1409 get knowledge areas from one batched query. **743 of the 1409 have no country
  and still come back** — the LEFT JOINs on `cities`/`countries` work, and their messages omit
  the country line instead of breaking. Catalogs return 249/190/5/6/73 entries, and every value
  stored by the 12 live chats is present. Empty inputs return `[]` and `{}` without a query.
- **No write path exists** in either new file; both queries are SELECT-only.
- **Commit:** see Progress.

### [x] T5 — Python filter matching and the updated_at watermark
**Route:** delegated writer (3 non-trivial files, highest-risk task).
- `src/aplication/sendCourseToSubcriptorsUseCase.py`: fetch subscribed chats, compute
  `min(lastrevision)`, fetch candidate courses newer than that, then match each chat in Python
  across country, university, language, level, knowledge areas (any-of) and keyword
  (case-insensitive substring on title or description).
- Watermark: advance to `max(updated_at)` over **all candidate courses fetched**, not only the
  matched ones. Today's code advances only to the newest *matched* course, so a chat whose
  filters match nothing keeps re-scanning its whole history on every run. With the timestamp
  watermark this is fixed for free.
- `src/aplication/updateUserFilterUseCase.py`: filter values are natural keys.
- `src/infraestructure/mapper/chatConfigMapper.py`: new columns and `datetime`.
- **Check:** matching is exercised against a fixture set covering each filter dimension, the
  "filters match nothing" case, and the watermark advance.
- **Verified against a SQL oracle, independently re-run:** with 51 candidates, the Python matcher
  and an equivalent SQL query agree on **all 7 subscribed chats — 0 discrepancies**. Match
  counts: 1, 51, 0, 0, 0, 0, 0.
- **Country gap holds:** a `CO` filter matches 34 candidates, every one of them `CO`, all from
  Bogotá. **0 of the 17 country-less candidates pass**, so half the catalog cannot leak past a
  filter the user set.
- **Watermark fix verified:** a chat whose filters match nothing still advances to the maximum
  `updated_at`; a chat already ahead of the maximum does not move; with no candidates the current
  value is kept. It never regresses.
- **Idempotence verified end-to-end:** run 1 sends 52 messages, run 2 sends **0**. Live rows were
  snapshotted and restored byte-identically afterwards — `chatconfigs` is back to 12 rows with
  the original watermarks, so the deploy-time watermark advance remains outstanding.
- **Bug found and fixed during verification:** `updateChatConfig` built its UPDATE from
  `model_dump()`, which yields DTO field names (`last_revision`) rather than column names
  (`lastrevision`). Every watermark write raised `KeyError`, and the use case's broad
  `except Exception` swallowed it, so runs reported success while no watermark ever advanced.
  The idempotence test caught it as "run 2 sent the same 52 messages". Now an explicit
  column-to-value dict.
- **Judgment calls:** a null `lastRevision` means "nothing new" and the chat is skipped (the old
  SQL treated null as match-everything; the new column defaults to `now()`, so null only appears
  if set explicitly). `_asUtc` is required, not defensive — `courses.updated_at` is
  `timestamp without time zone` while `lastrevision` is `timestamptz`, and comparing them raw
  raises `TypeError`. Both servers run GMT, but this assumes the owning system writes UTC.
- **Commit:** see Progress.

### [x] T6 — Filter UI reads catalogs from the new database
**Route:** delegated writer (1 non-trivial file).
- `src/port/telegramBot/command/filtersCommand.py`: replace the
  `defaultValuesCatalog` imports with the new database catalogs; keep the four dimensions, the
  `filtro_valor:<key>:<value|none>` callback shape, and the `university` dimension absent from
  the menu as it is today.
- **Check:** every offered value is a value that exists in the new database.
- **Bug found and fixed here: Telegram's 64-byte `callback_data` limit.** Filter values are now
  names instead of integer ids, and 3 of the 73 knowledge areas no longer fit:
  `Agronomía y estudios de la tierra` (66 B), `Ciencias económico-administrativas` (67 B) and
  `Otra Ciencia económico-administrativa` (70 B). Those three areas were literally unselectable.
  **Fixed with index-based callbacks** — the button carries the catalog index and the real value
  is resolved on press. Longest callback is now 36 B globally, and no label is truncated. Index
  callbacks were chosen over truncating names because two distinct areas would otherwise render
  identical text while filtering differently.
- **Verified, independently re-run:** every one of the 333 value buttons resolves back to its
  own label with no loss; max callback bytes 25/26/30/36 per dimension, 0 over the limit; the
  three previously-broken areas render with full labels. An out-of-range or malformed index
  answers with an alert instead of raising.
- **A stale stored value is reported, not silently widened.** If a saved filter value is no
  longer in the catalog, the summary shows `⚠️ No disponible (<value>)` instead of pretending it
  means "Cualquiera" — a filter that widens itself quietly is worse than one the user knows is
  stale.
- **Commit:** see Progress.

### [x] T7 — Remove the scraping pipeline
**Route:** direct inline (bulk deletion, mechanical, 27 files).
- Deleted: both source repositories, `sourceRepository.py`, `syncCoursesUseCase.py`,
  `syncCoursesTask.py`, `mapper/emovies/**`, `mapper/ausjal/**`, `dto/emovies/**`,
  `dto/ausjal/**`, `courseDtoMapper.py`, `defaultValuesCatalog.py`, `courseDto.py`, the five
  never-instantiated catalog DTOs, `requirements-scraper.txt`, `.github/workflows/sync-courses.yml`,
  and the scratch captures `ausjalHtmlCourse.txt`, `respuesta.json`.
- `CourseModel` (the scraper output model) deleted from the domain once nothing referenced it.
- `EMOVIES_PAGE_RETRIES` removed from `.env.example`; the stale `EMOVIES_BROWSER_COUNT` removed from
  the real `.env`.
- The send workflow now receives `COURSES_DB_URL`, and `sendCoursesToSubcriptorsTask` validates
  both database variables instead of only `DB_URL` — without this the workflow would have failed
  at the first connection.
- **Check:** a walk of every module under `src/` imports cleanly — **0 failures**, not just the
  two entry points. `sendCoursesToSubcriptorsTask` and `telegramBot.main` both import.
- **Verified end-to-end after deletion:** against live data, run 1 sends 52, run 2 sends 0.
  Live rows restored byte-identically.
- **Commit:** see Progress.

### [x] T8 — Documentation
**Route:** direct inline (docs only).
- `AGENTS.md`: rewritten. The old version documented a `courses` table the bot no longer owns, a
  five-catalog schema that no longer exists, a `courseRepository.py` that never existed, and
  repositories under names the code never used. Now covers the two-database setup, the read-only
  catalog schema, why the filters are natural keys, the `updated_at` notification rule, the
  `updated_at`/`lastrevision` timezone trap, the country gap, and the four gotchas worth knowing.
- `README.md`: dropped the scraper, `requirements-scraper.txt`, Playwright, `EMOVIES_PAGE_RETRIES`
  and the whole sync step; added the two-database table, `COURSES_DB_URL`, and the migration script.
- **Check:** every documented command and variable exists in the repository.
- **Verified:** all five `python -m` module references in the README import successfully, and the
  one workflow path exists. `requirements.txt` exists; the removed scraper requirements do not
  appear in either document.
- **Commit:** see Progress.

### [ ] T9 — Minimal test harness (RECOMMENDED, still unapproved)
**Route:** delegated writer.
- Add `pytest` and cover `courseRecordMapper` and `courseMatchesChat` / `nextWatermark`. The
  repository has zero tests and T5 replaced a SQL predicate with Python logic — the highest-risk
  change in this feature has no automated safety net. It was verified against a live SQL oracle
  and by end-to-end idempotence instead, but neither runs in CI.
- Skipped unless the user approves the scope.

## Acceptance criteria

All verified on 2026-10-08 against the live databases.

- [x] No SQL anywhere references the old `courses`, `course_disciplinary_fields`,
  `courses_sources`, `countries`, `universities`, `languages`, `course_levels` or
  `disciplinary_fields` tables of our own database. `chatconfigs` SQL lives in exactly one file.
- [x] Notifications are driven only by `courses.updated_at > chatconfigs.lastrevision`.
- [x] `chatconfigs` holds natural keys from the new database, and every value in it resolves there.
- [x] The Telegram message keeps its current structure, with `updated_at` as the date line and no
  "Horas de estudio" line.
- [x] The bot performs no write against the new database: zero write verbs in the courses
  repository, mapper and contract, and the catalog is byte-for-byte unchanged (4167 courses, 0
  updated during this work).
- [x] `scripts/migrate_chatconfigs_filters.py` is idempotent and reports every unresolved value.
- [x] Every module under `src/` imports cleanly (0 failures).
- [x] The Python matcher agrees with an equivalent SQL query on all 7 subscribed chats.

## Outstanding before going live

1. **Advance the watermark at deploy time** (decision already taken). Set each subscribed chat's
   `lastrevision` to the catalog's max `updated_at`, or the first run delivers 198 messages.
2. **Drop `chatconfigs_legacy`** once the feature is verified in production. It is the only
   remaining copy of the old integer filters.
3. **Ask the catalog's owning system** for an index on `(is_active, updated_at)` and `pg_trgm`
   GIN indexes on `title`/`description`. Neither exists, and the notification query filters and
   orders by `updated_at` while the keyword filter does `ILIKE`.
4. **T9 tests**, if approved.

## Delivery forecast

Roughly 1,000 authored changed lines (about 800 added or edited, about 2,500 deleted across the
scraping pipeline). Delivered as sequential work-unit commits on `main`, one per task, per the
delivery strategy above.

## Delivery strategy

- **Direct commits to `main`.** No feature branches, no chained PRs. Each task closes with one
  work-unit commit on `main`, using a Conventional Commit message, with tests and docs
  alongside the behavior.
- This overrides the initially selected `auto-chain`: the user chose direct-to-main delivery, so
  the review-budget split does not apply. The ~1,000 authored changed lines land across several
  sequential work-unit commits rather than in a PR chain.
- Push, pull request creation and merge remain the user's decisions under ordinary repository
  policy.

## Resolved decisions

- **D1 — existing rows: best effort with report.** Old INT filter values are resolved to new
  natural keys by name. Unresolvable values become `NULL` and are reported value by value. The
  accepted consequence is that lost filters widen to "any", so affected subscribers receive more
  notifications than before, not fewer.
- **D2 — delivery: direct commits to `main`, no PRs.**

## Risks

- **Filter coverage loss (accepted).** New university and knowledge-area names are unknown, so
  best-effort migration will widen some filters to "any". Affected subscribers get more
  notifications. The per-value report from T3 is the mitigation and must be reviewed after the
  first run.
- **Timestamp precision (medium).** `updated_at` is a `DateTime`; two courses updated in the same
  instant would be ordered arbitrarily. The watermark uses `max(updated_at)`, so a course sharing
  the exact maximum timestamp with an already-notified course could be skipped on a later run if
  ordering is unstable. Mitigation: keep the `ORDER BY updated_at DESC` and treat this as a
  duplicate-suppression question, not a data-loss one.
- **Missing indexes in the new database (medium, not ours to change).** There is no index on
  `updated_at` and no trigram index for the keyword filter on `title`/`description`. The owning
  team should be asked to add `(is_active, updated_at)` and `pg_trgm` GIN indexes.
- **Performance regression (low).** Matching moves from one SQL statement to one query plus
  in-memory work. Mitigated by pushing the date predicate down to SQL and fetching once for all
  chats instead of `chatconfigs x courses`.
- **No tests (medium).** See Task 9.

## Live database findings

Verified against the real `ElectivaInternacional` database on 2026-10-08 (PostgreSQL 18.6):

| Fact | Value |
|---|---|
| courses | 4167 total, 2905 active, 2 sources |
| `updated_at` range | 2026-10-02 13:24 to 2026-10-07 13:19 |
| catalogs | 249 countries, 38 cities, 190 universities, 191 campuses, 73 knowledge areas, 5 languages, 6 academic levels, 2 sources |
| `course_knowledge_areas` | 5876 rows; **0 courses without a knowledge area** |
| `academic_levels.id` | text: `undergraduate`, `postgraduate`, `doctorate`, `continuing_education`, `technical_technological`, `undefined` |
| `languages.code` | text `'1','2','3','5','6'` — identical to the old app language IDs |
| `sources` | `1 Emovies`, `2 Ausjal` — identical to the old app source IDs |

**Country coverage is the one real gap.** `courses` reaches `countries` only through
`campus -> city -> country`, and **2117 of 4167 courses (51%) have `city_id IS NULL`**, so they
resolve to no country at all. A country filter can therefore only ever match the other ~49%. The
country filter must treat an unresolvable country as "matches nothing" rather than "matches any",
otherwise those courses would leak past the filter.

**Old-to-new catalog resolution, measured (feeds T3):**

| Catalog | Resolves |
|---|---|
| countries | 16/17 — only `id 4 Brazil` fails, because the new database has `Brasil` and the old catalog listed both |
| universities | 183/183 |
| knowledge areas | 72/72 |
| academic levels | 5/5 by semantic map |
| languages | 5/5 — codes are unchanged |

Current `chatconfigs` holds 12 rows, 7 subscribed (1 country filter, 0 university, 2 language,
6 level, 7 disciplinary field). Filter-coverage loss from the migration is therefore small and
fully enumerable.

## Progress

- [x] **T1 — Dual connection layer.** Verified and committed. `DB_URL` -> `electiveNotifier_db`
  (subscriptions and filters), `COURSES_DB_URL` -> `ElectivaInternacional` (read-only catalog).
- [x] **T2 — Domain contracts and models.** Verified and committed.
- [x] **T3 — chatconfigs DDL and data migration.** Verified and committed. Zero filter losses.
  `chatconfigs_legacy` retained.
- [x] **T4 — Course repository implementation and mapper.** Verified and committed.
- [x] **T5 — Python filter matching and the updated_at watermark.** Verified and committed.
  Python matcher agrees with SQL on all 7 chats, 0 discrepancies.
- [x] **T6 — Filter UI reads catalogs from the new database.** Verified and committed. Fixed the
  64-byte `callback_data` limit that made 3 knowledge areas unselectable.
- [x] **T7 — Remove the scraping pipeline.** Verified and committed. 27 files deleted; the send
  workflow now gets `COURSES_DB_URL`.
- [x] **T8 — Documentation.** Verified and committed.

All eight code tasks are complete. T9 (tests) remains unapproved, and the deploy-time steps above
are still outstanding.

### Note for T6 (resolved)

`UpdateUserFilterUseCase` stores filter values as raw strings and normalizes blank input to
`NULL`. `filtersCommand.py` no longer parses callback values as `int`, so the trap that would
have saved every filter as `NULL` is gone.

### Known trade-off: index callbacks and catalog changes

Telegram keeps a rendered keyboard alive, and the catalogs are ordered by name. If the owning
system inserts or renames an entry between render and press, an index can shift and store a
value different from the label the user saw. An out-of-range index is already contained (it alerts
instead of crashing). Closing the window completely would require a fingerprint inside the
callback, which costs bytes in an already-tight budget; not implemented.

### First-run notification burst: RESOLVED

Measured on the live database before deciding: the burst is far smaller than the worst case,
because `lastrevision` landed at 2026-10-06 and the catalog's newest `updated_at` is
2026-10-07 13:19:13. Not 4167 courses — **198 messages with filters applied** across the 7
subscribed chats (51 to the least-filtered chat, 18-20 to the filtered ones), or 357 unfiltered.

**Decision: advance the watermark at deploy time.** A one-shot UPDATE sets each subscribed
chat's `lastrevision` to the catalog's max `updated_at`, so the first real run only notifies
courses published from then on. Nothing meaningful is lost: the catalog entries being skipped
were already delivered to these subscribers through the old pipeline months ago.

This is a deploy-time data step, not application code, so it does not belong in a task's
acceptance criteria. It must be run before the send-courses workflow goes live.