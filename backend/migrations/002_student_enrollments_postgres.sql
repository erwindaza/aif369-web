CREATE TABLE IF NOT EXISTS student_enrollments (
    id UUID PRIMARY KEY,
    product_id TEXT NOT NULL,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT,
    country TEXT,
    role TEXT,
    company TEXT,
    message TEXT,
    source_page TEXT,
    signup_status TEXT NOT NULL DEFAULT 'pending',
    payment_status TEXT NOT NULL DEFAULT 'pending',
    payment_reference TEXT,
    access_status TEXT NOT NULL DEFAULT 'locked',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (email, product_id)
);

CREATE INDEX IF NOT EXISTS idx_student_enrollments_email_product
    ON student_enrollments (email, product_id);
