-- Migration: Add gender column + missing indexes
-- Run: wrangler d1 execute ft-lineone-db --file=./migrations/0001_add_gender_and_indexes.sql

-- Add gender column (safe — defaults to NULL for existing rows)
ALTER TABLE users ADD COLUMN gender TEXT;

-- Add missing indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_usage_user_id ON user_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);
