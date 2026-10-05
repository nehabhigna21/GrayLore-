# Graylore — Full OTT DBMS Project

A working OTT platform backend wired to all 5 UI pages, implementing the locked 17-feature
scope with real MySQL queries, triggers, and the Graylore glassmorphism UI.


## What's wired up 

| Feature | Route | DB logic |
|---|---|---|
| Registration / Login | `/register`, `/login` | Password hashing (Werkzeug), new users auto-get a Basic subscription |
| Multiple profiles incl. Kids | `/profiles` | Insert/list `Profiles` |
| Content catalog, region licensing | `/home` | JOIN `Content`+`Licenses`, filtered by region + current date |
| Recommended for You | `/home` | Self-join on `WatchHistory` — co-watch correlation |
| Trending Now | `/home` | `SUM(watch_minutes)` aggregate, grouped by title |
| Continue Watching | `/home` | Most recent `WatchHistory` row per title, per profile |
| **VOD playback** | `/play/<id>` | HTML5 `<video>` streams `Content.video_url`; license check before playback; inserts into `Sessions` and opens a `WatchHistory` row |
| **Resume + progress tracking** | `/progress` (JSON, called by the player) | Updates `WatchHistory.position_sec` / `watch_minutes` every 10 s, on pause and on page close; next play resumes from the last position |
| **TMDB metadata import** | `import_tmdb.py`, `/admin/import_tmdb` | Upserts posters, backdrops, overview, trailer, genre, runtime, age rating into `Content` (keyed on `tmdb_id`) + auto-creates a regional `License` |
| **Device limit enforcement** | `trg_device_limit` (MySQL trigger) | Fires on `Sessions` insert — force-logs-out oldest session past the plan's device cap |
| Rate / Review | `/rate` | Upsert into `Ratings` (unique per profile+content) |
| Subscription / Billing | `/billing` | Insert new `Subscriptions` row + `Payments` row |
| **Single active subscription** | `trg_single_active_sub` (MySQL trigger) | Fires on `Subscriptions` insert — auto-cancels the previous one |
| Admin dashboard | `/admin` | Live stats + content table |
| **Royalty payout report** | `/admin` | `SUM(watch_minutes) × rate_per_min`, computed live (not stored — see schema note) |
| Add content (admin) | `/admin/add_content` | Insert into `Content` + `Licenses` |

## Files

- `app.py` — Flask application, all routes
- `tmdb.py` — TMDB API client + `Content` upsert helper
- `import_tmdb.py` — CLI importer (`--popular N`, `--search TITLE`, `--id TMDB_ID`)
- `schema.sql` — 10-table schema (Content carries VOD columns: `video_url`, `poster_url`, `tmdb_id`, …)
- `migrate_vod.sql` — one-off ALTERs for databases created before the VOD columns existed
- `triggers.sql` — device-limit and single-subscription triggers
- `seed_data.sql` — dummy data across all tables (2 regular users + 1 admin, pre-hashed passwords)
- `templates/` — the 5 Graylore pages (auth, profile, home, player, admin), now Jinja-driven
- `requirements.txt` — Python dependencies

## Where the video comes from

TMDB provides metadata only (posters, synopsis, trailers) , not the full films. Every title
therefore carries its own url, which the player streams directly. Seeded and imported
titles point at public-domain sample films , so playback works
immediately; swap in your own MP4 / HLS URLs via the admin "Add Title" form.

