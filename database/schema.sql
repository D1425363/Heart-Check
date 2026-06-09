-- SQLite Database Schema for Heart Check
-- Enable Foreign Key Support (Must be run per connection: PRAGMA foreign_keys = ON;)

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL,
    student_id TEXT NOT NULL UNIQUE,
    department TEXT,
    heart_balance INTEGER NOT NULL DEFAULT 100,
    popularity INTEGER NOT NULL DEFAULT 0,
    qr_code_token TEXT NOT NULL UNIQUE,
    avatar TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- 2. Heart Transactions Table
CREATE TABLE IF NOT EXISTS heart_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id INTEGER NOT NULL,
    receiver_id INTEGER NOT NULL,
    heart_amount INTEGER NOT NULL CHECK(heart_amount > 0),
    thank_you_message TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE RESTRICT,
    FOREIGN KEY (receiver_id) REFERENCES users(id) ON DELETE RESTRICT
);

-- 3. Items (Lost & Found) Table
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    image_url TEXT,
    location TEXT NOT NULL,
    item_type TEXT NOT NULL CHECK(item_type IN ('lost', 'found')),
    status TEXT NOT NULL CHECK(status IN ('unclaimed', 'claimed')),
    user_id INTEGER NOT NULL,
    contact_info TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 4. Announcements Table
CREATE TABLE IF NOT EXISTS announcements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    category TEXT NOT NULL CHECK(category IN ('dorm', 'campus')),
    author_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE RESTRICT
);

-- Indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_heart_transactions_sender ON heart_transactions(sender_id);
CREATE INDEX IF NOT EXISTS idx_heart_transactions_receiver ON heart_transactions(receiver_id);
CREATE INDEX IF NOT EXISTS idx_items_user ON items(user_id);
CREATE INDEX IF NOT EXISTS idx_items_type_status ON items(item_type, status);
CREATE INDEX IF NOT EXISTS idx_announcements_category ON announcements(category);
CREATE INDEX IF NOT EXISTS idx_announcements_author ON announcements(author_id);
