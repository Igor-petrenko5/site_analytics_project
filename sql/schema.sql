CREATE TABLE IF NOT EXISTS monthly_metrics (
    month_date TEXT PRIMARY KEY,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    visits INTEGER NOT NULL,
    visitors INTEGER NOT NULL,
    bounce_rate REAL,
    pages_per_visit REAL,
    avg_duration_sec INTEGER
);

CREATE TABLE IF NOT EXISTS annual_summary (
    year INTEGER PRIMARY KEY,
    visits INTEGER,
    unique_visitors INTEGER,
    bounce_rate REAL,
    pages_per_visit REAL,
    avg_duration_sec INTEGER
);
