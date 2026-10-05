-- Graylore VOD migration — run this ONCE on an existing database.
-- (Fresh installs don't need it: schema.sql already includes these columns.)
USE graylore;

ALTER TABLE Content
    ADD COLUMN tmdb_id INT UNIQUE,
    ADD COLUMN overview TEXT,
    ADD COLUMN poster_url VARCHAR(255),
    ADD COLUMN backdrop_url VARCHAR(255),
    ADD COLUMN trailer_key VARCHAR(50),
    ADD COLUMN video_url VARCHAR(255);

ALTER TABLE WatchHistory
    ADD COLUMN position_sec INT DEFAULT 0 AFTER watch_minutes;

-- Give the seeded titles playable streams (public-domain sample films)
UPDATE Content SET video_url = 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4'   WHERE content_id IN (1, 5, 9);
UPDATE Content SET video_url = 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4'  WHERE content_id IN (2, 6, 10);
UPDATE Content SET video_url = 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/Sintel.mp4'          WHERE content_id IN (3, 7);
UPDATE Content SET video_url = 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/TearsOfSteel.mp4'    WHERE content_id IN (4, 8);
