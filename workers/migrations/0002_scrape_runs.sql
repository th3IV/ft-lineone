-- Migration 0002: Add scrape_runs table and missing performance indexes
-- Run: wrangler d1 execute ft-lineone-db --file=./migrations/0002_scrape_runs.sql

CREATE TABLE IF NOT EXISTS scrape_runs (
    id TEXT PRIMARY KEY,
    store TEXT NOT NULL,
    started_at DATETIME NOT NULL,
    finished_at DATETIME NOT NULL,
    status TEXT NOT NULL,
    total_products INTEGER DEFAULT 0,
    upserted_products INTEGER DEFAULT 0,
    stale_deleted INTEGER DEFAULT 0,
    errors INTEGER DEFAULT 0,
    empty_queries INTEGER DEFAULT 0,
    duration_seconds REAL DEFAULT 0.0,
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_scrape_runs_store_started ON scrape_runs(store, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_scrape_runs_status ON scrape_runs(status);

-- Performance indexes (H7, H8, H9 from architectural audit)
CREATE INDEX IF NOT EXISTS idx_payments_transbank_token ON payments(transbank_token);
CREATE INDEX IF NOT EXISTS idx_vton_results_status_task ON vton_results(status, youcam_task_id);
CREATE INDEX IF NOT EXISTS idx_products_last_seen ON products(store, last_seen);
CREATE INDEX IF NOT EXISTS idx_products_created_at ON products(created_at DESC);
