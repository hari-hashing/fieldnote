CREATE TABLE IF NOT EXISTS subscribers (
 id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT NOT NULL UNIQUE,
 timezone TEXT NOT NULL, delivery_hour INTEGER NOT NULL DEFAULT 9 CHECK(delivery_hour BETWEEN 8 AND 11),
 status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','active','unsubscribed')),
 consent_at TEXT NOT NULL, created_at TEXT NOT NULL, verified_at TEXT,
 verification_token_hash TEXT, unsubscribe_token TEXT NOT NULL, last_sent_week TEXT
);
CREATE INDEX IF NOT EXISTS idx_subscribers_active ON subscribers(status,timezone,delivery_hour);
CREATE TABLE IF NOT EXISTS signup_attempts(id INTEGER PRIMARY KEY AUTOINCREMENT,email_hash TEXT NOT NULL,attempted_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_signup_attempts ON signup_attempts(email_hash,attempted_at);
