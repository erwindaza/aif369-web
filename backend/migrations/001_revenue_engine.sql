-- AIF369 Revenue Engine MVP schema.
-- Target: PostgreSQL/Supabase. Adapt types if deployed to BigQuery.

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    phone_optional TEXT,
    country TEXT,
    role TEXT NOT NULL DEFAULT 'student',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS products (
    id TEXT PRIMARY KEY,
    slug TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    description TEXT,
    currency TEXT NOT NULL,
    price NUMERIC(12,2) NOT NULL,
    status TEXT NOT NULL,
    payment_required BOOLEAN NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id TEXT REFERENCES products(id),
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'draft',
    certificate_enabled BOOLEAN NOT NULL DEFAULT false
);

CREATE TABLE IF NOT EXISTS course_modules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID REFERENCES courses(id),
    module_number INTEGER NOT NULL,
    title TEXT NOT NULL,
    content_url_or_reference TEXT,
    status TEXT NOT NULL DEFAULT 'draft'
);

CREATE TABLE IF NOT EXISTS payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    product_id TEXT REFERENCES products(id),
    provider TEXT NOT NULL DEFAULT 'PayPal',
    provider_order_id TEXT UNIQUE NOT NULL,
    provider_capture_id TEXT,
    currency TEXT NOT NULL,
    amount NUMERIC(12,2) NOT NULL,
    status TEXT NOT NULL,
    raw_event_reference TEXT,
    paid_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS enrollments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    course_id UUID REFERENCES courses(id),
    payment_id UUID REFERENCES payments(id),
    payment_status TEXT NOT NULL,
    access_status TEXT NOT NULL,
    enrolled_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ,
    CHECK (
        (payment_status = 'COMPLETED' AND access_status = 'ACTIVE')
        OR (payment_status <> 'COMPLETED' AND access_status <> 'ACTIVE')
    )
);

CREATE TABLE IF NOT EXISTS bookings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    product_id TEXT REFERENCES products(id),
    payment_id UUID REFERENCES payments(id),
    date_time TIMESTAMPTZ,
    duration_minutes INTEGER NOT NULL DEFAULT 60,
    meeting_url TEXT,
    status TEXT NOT NULL DEFAULT 'pending'
);

CREATE TABLE IF NOT EXISTS certificates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    certificate_id TEXT UNIQUE NOT NULL,
    user_id UUID REFERENCES users(id),
    course_id UUID REFERENCES courses(id),
    issued_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    verification_slug TEXT UNIQUE NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    pdf_url_optional TEXT,
    project_verified BOOLEAN NOT NULL DEFAULT false,
    completion_status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    company TEXT,
    role TEXT,
    source TEXT,
    interest TEXT,
    status TEXT NOT NULL DEFAULT 'new',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS corporate_inquiries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company TEXT NOT NULL,
    contact_name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT,
    number_of_participants INTEGER,
    training_interest TEXT,
    budget_optional NUMERIC(12,2),
    status TEXT NOT NULL DEFAULT 'new',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);
CREATE INDEX IF NOT EXISTS idx_enrollments_access ON enrollments(user_id, access_status);
CREATE INDEX IF NOT EXISTS idx_certificates_certificate_id ON certificates(certificate_id);
