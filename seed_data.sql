USE graylore;

-- Users (password for both: "password123")
INSERT INTO Users (name, email, password_hash) VALUES
('Aditi Menon', 'aditi@example.com', 'scrypt:32768:8:1$ZyxunVJASqiuQ4eX$8f06b7b8a1ee1f781d1ddc8bc7d62ee821ed736fefe930286b543934c614981562a2365fcdb1f8dad645631bb441aa40c9bb1ce091fd946585d0c98bb77e0b71'),
('Rohan Das', 'rohan@example.com', 'scrypt:32768:8:1$ZyxunVJASqiuQ4eX$8f06b7b8a1ee1f781d1ddc8bc7d62ee821ed736fefe930286b543934c614981562a2365fcdb1f8dad645631bb441aa40c9bb1ce091fd946585d0c98bb77e0b71');

-- Admin account (email checked in app.py to grant admin dashboard access)
INSERT INTO Users (name, email, password_hash) VALUES
('Admin', 'admin@graylore.com', 'scrypt:32768:8:1$ZyxunVJASqiuQ4eX$8f06b7b8a1ee1f781d1ddc8bc7d62ee821ed736fefe930286b543934c614981562a2365fcdb1f8dad645631bb441aa40c9bb1ce091fd946585d0c98bb77e0b71');

-- Subscriptions
INSERT INTO Subscriptions (user_id, plan_type, device_limit, start_date, end_date, status) VALUES
(1, 'Standard', 2, '2026-01-01', '2026-12-31', 'active'),
(2, 'Premium', 4, '2026-02-01', '2026-12-31', 'active');

-- Profiles
INSERT INTO Profiles (user_id, profile_name, is_kids) VALUES
(1, 'Aditi', FALSE),
(1, 'Kiddo', TRUE),
(2, 'Rohan', FALSE);

-- Content catalog
-- video_url points at public-domain sample films so playback works out of the box.
-- Run `python import_tmdb.py --popular 20` afterwards to add real titles with posters.
SET @bbb = 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4';
SET @ed  = 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4';
SET @sin = 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/Sintel.mp4';
SET @tos = 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/TearsOfSteel.mp4';

INSERT INTO Content (title, genre, language, age_rating, release_date, duration_min, overview, video_url) VALUES
('Crimson Static', 'Thriller', 'English', '16+', '2024-03-10', 112, 'A radio engineer intercepts a broadcast that predicts crimes before they happen.', @bbb),
('Paperglass', 'Drama', 'English', 'U', '2023-06-21', 104, 'Two estranged sisters rebuild their late mother''s glass studio over one summer.', @ed),
('The Long Interval', 'Sci-Fi', 'English', '13+', '2025-01-15', 128, 'A deep-space relay crew wakes from stasis to find Earth has gone silent.', @sin),
('Halfway to Kepler', 'Adventure', 'English', 'U', '2022-05-02', 118, 'A teenage pilot and her grandfather race a homemade rocket across the outback.', @tos),
('Low Tide', 'Mystery', 'English', '16+', '2024-02-18', 109, 'A coastal town''s secrets surface when the tide pulls back further than ever before.', @bbb),
('Amber Line', 'Drama', 'English', '13+', '2023-09-09', 121, 'A night-shift tram driver and a regular passenger share a year of quiet conversations.', @ed),
('Nightglass', 'Thriller', 'English', '16+', '2025-03-01', 115, 'An art forger is hired to replace a painting that may never have existed.', @sin),
('Sable & Ash', 'Fantasy', 'English', 'U', '2022-11-11', 132, 'Twin foxes guard the last ember of a dying forest kingdom.', @tos),
('The Quiet Registry', 'Mystery', 'English', '13+', '2023-04-04', 106, 'A records clerk notices the same name appearing in every unsolved file.', @bbb),
('Fault Lines', 'Drama', 'English', '16+', '2024-06-06', 119, 'A family reunion on the eve of an earthquake forces old grudges into the open.', @ed);

-- Licenses (region + validity window)
INSERT INTO Licenses (content_id, region, license_start, license_end) VALUES
(1, 'IN', '2024-01-01', '2027-12-31'),
(1, 'US', '2024-01-01', '2026-12-31'),
(2, 'IN', '2023-06-01', '2027-03-31'),
(3, 'US', '2025-01-01', '2026-11-30'),
(3, 'UK', '2025-01-01', '2026-11-30'),
(4, 'IN', '2022-05-01', '2026-08-31'),
(4, 'UK', '2022-05-01', '2026-08-31'),
(5, 'IN', '2024-02-01', '2026-10-31'),
(6, 'US', '2023-09-01', '2026-09-30'),
(7, 'IN', '2025-03-01', '2027-01-31'),
(8, 'IN', '2022-11-01', '2026-07-31'),
(9, 'US', '2023-04-01', '2026-12-31'),
(10, 'IN', '2024-06-01', '2027-02-28');

-- Watch history (drives recommendations + royalty report)
INSERT INTO WatchHistory (profile_id, content_id, watch_minutes, position_sec, watched_at) VALUES
(1, 1, 112, 0,   '2026-09-20 20:00:00'),
(1, 2, 104, 0,   '2026-09-21 19:30:00'),
(1, 3, 60,  180, '2026-09-25 21:00:00'),
(3, 1, 112, 0,   '2026-09-18 18:00:00'),
(3, 4, 118, 0,   '2026-09-19 20:00:00'),
(3, 6, 121, 0,   '2026-09-22 21:00:00'),
(1, 6, 121, 0,   '2026-09-27 20:00:00'),
(3, 2, 104, 0,   '2026-09-28 19:00:00');

-- Ratings
INSERT INTO Ratings (profile_id, content_id, rating, review) VALUES
(1, 1, 5, 'Gripping from start to finish.'),
(1, 2, 4, 'Quietly moving.'),
(3, 4, 4, 'Great chemistry between leads.'),
(3, 6, 5, 'Best drama this year.');

-- Payments
INSERT INTO Payments (user_id, sub_id, amount, payment_date, status) VALUES
(1, 1, 399.00, '2026-01-01', 'paid'),
(2, 2, 649.00, '2026-02-01', 'paid');
