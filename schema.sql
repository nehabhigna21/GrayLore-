-- Graylore OTT Platform — Full Schema

CREATE DATABASE IF NOT EXISTS graylore;
USE graylore;

DROP TABLE IF EXISTS Payouts;
DROP TABLE IF EXISTS Payments;
DROP TABLE IF EXISTS Ratings;
DROP TABLE IF EXISTS WatchHistory;
DROP TABLE IF EXISTS Sessions;
DROP TABLE IF EXISTS Licenses;
DROP TABLE IF EXISTS Profiles;
DROP TABLE IF EXISTS Subscriptions;
DROP TABLE IF EXISTS Content;
DROP TABLE IF EXISTS Users;

CREATE TABLE Users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Subscriptions (
    sub_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    plan_type VARCHAR(20) NOT NULL,      -- Basic / Standard / Premium
    device_limit INT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    status VARCHAR(20) DEFAULT 'active', -- active / expired / cancelled
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

CREATE TABLE Profiles (
    profile_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    profile_name VARCHAR(50) NOT NULL,
    is_kids BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

CREATE TABLE Content (
    content_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(150) NOT NULL,
    genre VARCHAR(50),
    language VARCHAR(30) DEFAULT 'English',
    age_rating VARCHAR(10) DEFAULT 'U',
    release_date DATE,
    duration_min INT,
    -- VOD / metadata fields (populated by import_tmdb.py or the admin panel)
    tmdb_id INT UNIQUE,                  -- TMDB movie id, NULL for hand-entered titles
    overview TEXT,
    poster_url VARCHAR(255),
    backdrop_url VARCHAR(255),
    trailer_key VARCHAR(50),             -- YouTube video key from TMDB
    video_url VARCHAR(255)               -- the stream the player actually plays (MP4 / HLS)
);

CREATE TABLE Licenses (
    license_id INT AUTO_INCREMENT PRIMARY KEY,
    content_id INT NOT NULL,
    region VARCHAR(50) NOT NULL,
    license_start DATE NOT NULL,
    license_end DATE NOT NULL,
    FOREIGN KEY (content_id) REFERENCES Content(content_id)
);

CREATE TABLE Sessions (
    session_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    device_id VARCHAR(100) NOT NULL,
    login_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

CREATE TABLE WatchHistory (
    watch_id INT AUTO_INCREMENT PRIMARY KEY,
    profile_id INT NOT NULL,
    content_id INT NOT NULL,
    watch_minutes INT DEFAULT 0,
    position_sec INT DEFAULT 0,          -- last playback position, used for "Resume from"
    watched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (profile_id) REFERENCES Profiles(profile_id),
    FOREIGN KEY (content_id) REFERENCES Content(content_id)
);

CREATE TABLE Ratings (
    rating_id INT AUTO_INCREMENT PRIMARY KEY,
    profile_id INT NOT NULL,
    content_id INT NOT NULL,
    rating INT CHECK (rating BETWEEN 1 AND 5),
    review TEXT,
    UNIQUE KEY uniq_profile_content (profile_id, content_id),
    FOREIGN KEY (profile_id) REFERENCES Profiles(profile_id),
    FOREIGN KEY (content_id) REFERENCES Content(content_id)
);

CREATE TABLE Payments (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    sub_id INT NOT NULL,
    amount DECIMAL(8,2) NOT NULL,
    payment_date DATE DEFAULT (CURRENT_DATE),
    status VARCHAR(20) DEFAULT 'paid',
    FOREIGN KEY (user_id) REFERENCES Users(user_id),
    FOREIGN KEY (sub_id) REFERENCES Subscriptions(sub_id)
);

-- Reporting table — intentionally outside strict 3NF (see project writeup).
-- Populated by periodic aggregation, not by the app's live queries.
CREATE TABLE Payouts (
    payout_id INT AUTO_INCREMENT PRIMARY KEY,
    content_id INT NOT NULL,
    total_minutes INT,
    rate_per_min DECIMAL(6,4) DEFAULT 0.05,
    payout_amount DECIMAL(10,2),
    period VARCHAR(20),
    FOREIGN KEY (content_id) REFERENCES Content(content_id)
);
