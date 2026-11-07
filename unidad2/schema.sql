PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS import_batch (
    id INTEGER PRIMARY KEY,
    source_sha256 TEXT NOT NULL,
    evidence_sha256 TEXT NOT NULL,
    platform TEXT NOT NULL,
    account_id TEXT NOT NULL,
    account_label TEXT NOT NULL,
    source_kind TEXT NOT NULL CHECK (source_kind IN ('official_export', 'authorized_api', 'public_web_capture')),
    authorization_reference TEXT,
    public_source_url TEXT,
    affiliation_evidence TEXT NOT NULL,
    exported_at TEXT NOT NULL,
    imported_at TEXT NOT NULL,
    row_count INTEGER NOT NULL CHECK (row_count >= 0),
    UNIQUE(source_sha256, platform, account_id)
);

CREATE TABLE IF NOT EXISTS dim_platform (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS dim_account (
    id INTEGER PRIMARY KEY,
    platform_id INTEGER NOT NULL REFERENCES dim_platform(id),
    external_id TEXT NOT NULL,
    label TEXT NOT NULL,
    UNIQUE(platform_id, external_id)
);
CREATE TABLE IF NOT EXISTS dim_project (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS dim_content_type (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS dim_date (
    date_key TEXT PRIMARY KEY,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    day INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_post (
    id INTEGER PRIMARY KEY,
    platform_id INTEGER NOT NULL REFERENCES dim_platform(id),
    account_id INTEGER NOT NULL REFERENCES dim_account(id),
    project_id INTEGER REFERENCES dim_project(id),
    content_type_id INTEGER REFERENCES dim_content_type(id),
    date_key TEXT REFERENCES dim_date(date_key),
    external_id TEXT NOT NULL,
    post_url TEXT NOT NULL,
    published_at TEXT,
    published_label TEXT,
    topic TEXT,
    first_batch_id INTEGER NOT NULL REFERENCES import_batch(id),
    UNIQUE(platform_id, external_id)
);

CREATE TABLE IF NOT EXISTS fact_metric_snapshot (
    id INTEGER PRIMARY KEY,
    post_id INTEGER NOT NULL REFERENCES fact_post(id),
    captured_at TEXT NOT NULL,
    likes INTEGER CHECK (likes IS NULL OR likes >= 0),
    comments INTEGER CHECK (comments IS NULL OR comments >= 0),
    shares INTEGER CHECK (shares IS NULL OR shares >= 0),
    reach INTEGER CHECK (reach IS NULL OR reach >= 0),
    impressions INTEGER CHECK (impressions IS NULL OR impressions >= 0),
    batch_id INTEGER NOT NULL REFERENCES import_batch(id),
    UNIQUE(post_id, captured_at)
);

CREATE INDEX IF NOT EXISTS idx_post_date ON fact_post(date_key);
CREATE INDEX IF NOT EXISTS idx_snapshot_post_time ON fact_metric_snapshot(post_id, captured_at DESC);

CREATE VIEW IF NOT EXISTS report_post_latest AS
SELECT p.id, p.external_id, p.post_url, p.published_at, p.published_label, p.date_key,
       d.year, d.month, d.day, pl.name AS platform, a.label AS account,
       pr.name AS project, ct.name AS content_type, p.topic,
       s.captured_at AS metrics_captured_at,
       s.likes, s.comments, s.shares, s.reach, s.impressions,
       b.source_kind, b.source_sha256, b.evidence_sha256,
       b.authorization_reference, b.public_source_url, b.affiliation_evidence
FROM fact_post p
LEFT JOIN dim_date d ON d.date_key = p.date_key
JOIN dim_platform pl ON pl.id = p.platform_id
JOIN dim_account a ON a.id = p.account_id
LEFT JOIN dim_project pr ON pr.id = p.project_id
LEFT JOIN dim_content_type ct ON ct.id = p.content_type_id
LEFT JOIN fact_metric_snapshot s ON s.id = (
    SELECT s2.id FROM fact_metric_snapshot s2
    WHERE s2.post_id = p.id ORDER BY s2.captured_at DESC, s2.id DESC LIMIT 1
)
JOIN import_batch b ON b.id = COALESCE(s.batch_id, p.first_batch_id);
