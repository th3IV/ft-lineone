-- FT-LineOne D1 Database Schema

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    body_measurements TEXT, -- JSON as TEXT
    preferences TEXT, -- JSON as TEXT
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Products table
CREATE TABLE IF NOT EXISTS products (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    external_id TEXT NOT NULL,
    store TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    price REAL NOT NULL,
    currency TEXT DEFAULT 'CLP',
    original_url TEXT DEFAULT '',
    image_url TEXT,
    image_urls TEXT, -- JSON as TEXT
    category TEXT DEFAULT '',
    sizes TEXT, -- JSON as TEXT
    colors TEXT, -- JSON as TEXT
    availability BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- VTON Results table
CREATE TABLE IF NOT EXISTS vton_results (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    user_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    input_image_url TEXT,
    output_image_url TEXT,
    garment_image_url TEXT,
    error_message TEXT,
    youcam_task_id TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_products_store ON products(store);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_price ON products(price);
CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_vton_results_user_id ON vton_results(user_id);
CREATE INDEX IF NOT EXISTS idx_vton_results_product_id ON vton_results(product_id);
