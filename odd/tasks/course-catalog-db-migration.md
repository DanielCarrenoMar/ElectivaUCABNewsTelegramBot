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

### [ ] T5 — Python filter matching and the updated_at watermark
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

### [ ] T6 — Filter UI reads catalogs from the new database
**Route:** delegated writer (1 non-trivial file).
- `src/port/telegramBot/command/filtersCommand.py`: replace the
  `defaultValuesCatalog` imports with the new database catalogs; keep the four dimensions, the
  `filtro_valor:<key>:<value|none>` callback shape, and the `university` dimension absent from
  the menu as it is today.
- **Check:** every offered value is a value that exists in the new database.

### [ ] T7 — Remove the scraping pipeline
**Route:** delegated writer (bulk deletion, mechanical).
- Delete: `emoviesSourceRepositoryImp.py`, `ausjalSourceRepositoryImp.py`,
  `sourceRepository.py`, `syncCoursesUseCase.py`, `syncCoursesTask.py`, `mapper/emovies/**`,
  `mapper/ausjal/**`, `dto/emovies/**`, `dto/ausjal/**`, `courseDtoMapper.py`,
  `defaultValuesCatalog.py`, the six unused/newly-unused `dto/database/*` files,
  `requirements-scraper.txt`, `.github/workflows/sync-courses.yml`, and the scratch captures
  `ausjalHtmlCourse.txt`, `respuesta.json`.
- **Check:** no dangling imports; `python -m src.port.task.sendCoursesToSubcriptorsTask` still
  imports cleanly. Deletions are reversible through git if the user wants any file kept.

### [ ] T8 — Documentation
**Route:** direct inline (docs only).
- `AGENTS.md`: replace the course DDL and catalog tables with the new read-only schema, the
  two-connection setup, and the `updated_at` notification rule.
- `README.md`, `intructure.md`: drop the scraper, the seed and the sync step; add
  `COURSES_DB_URL`.
- **Check:** every documented command and variable exists in the repository.

### [ ] T9 — Minimal test harness (recommended, pending approval)
**Route:** delegated writer.
- Add `pytest` and cover `courseRecordMapper` and the T5 matching function. Today the repository
  has zero tests, and T5 replaces a SQL predicate with Python logic — the highest-risk change in
  this feature has no safety net. Skipped unless the user approves the scope.

## Acceptance criteria

- No SQL anywhere references the old `courses`, `course_disciplinary_fields`,
  `courses_sources`, `countries`, `universities`, `languages`, `course_levels` or
  `disciplinary_fields` tables.
- Notifications are driven only by `courses.updated_at > chatconfigs.lastrevision`.
- `chatconfigs` holds natural keys from the new database, and every value in it resolves there.
- The Telegram message keeps its current structure, with `updated_at` as the date line and no
  "Horas de estudio" line.
- The bot performs no write against the new database.
- `scripts/migrate_chatconfigs_filters.py` is idempotent and reports every unresolved value.

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

### Open issue: first-run notification burst (needs a decision before T5 goes live)

Our `courses` table holds 2893 rows with `modified_date` watermarks in Aug/Oct 2026. The external
catalog holds 4167 rows whose `updated_at` maxes at 2026-10-07. The migrated `lastrevision`
values are 2026-08-19 (5 chats) and 2026-10-06 (7 chats), so **every subscribed chat will treat
the entire external catalog as new on the first run** and receive a very large burst.

Options for T5: leave it (users get one large catch-up, then normal operation), or advance
`lastrevision` to the catalog's max `updated_at` during deployment so only genuinely new courses
notify. This must be decided before the pipeline goes live.