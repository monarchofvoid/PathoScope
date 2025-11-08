-- PathoScope Database Initialization Script
-- This script creates the initial database structure and seed data

-- Create database if it doesn't exist (handled by PostgreSQL environment)
-- Extensions required for UUID generation and other features
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create indexes for better performance
-- These will be created automatically by SQLAlchemy but we can add them here for reference

-- Example admin user creation (for development only)
-- In production, users should be created through the application
INSERT INTO users (
    id,
    email,
    password_hash,
    full_name,
    role,
    is_active,
    created_at
) VALUES (
    uuid_generate_v4(),
    'admin@pathoscope.hospital',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3QJflHQrxW', -- password: Admin123!
    'System Administrator',
    'ict_admin',
    true,
    NOW()
) ON CONFLICT (email) DO NOTHING;

-- Sample infection case for development (optional)
-- In production, all cases should be created through the application

-- Sample analytics snapshot for development
INSERT INTO analytics_snapshots (
    id,
    snapshot_date,
    total_alerts_24h,
    high_risk_alerts_24h,
    moderate_risk_alerts_24h,
    low_risk_alerts_24h,
    tek_upload_compliance_rate,
    total_active_cases,
    new_cases_24h,
    calculated_at
) VALUES (
    uuid_generate_v4(),
    CURRENT_DATE,
    0,
    0,
    0,
    0,
    0.0,
    0,
    0,
    NOW()
) ON CONFLICT (snapshot_date) DO NOTHING;

-- Sample system health record for development
INSERT INTO system_health (
    id,
    service_name,
    status,
    response_time_ms,
    last_check,
    error_count,
    uptime_percentage,
    created_at
) VALUES (
    uuid_generate_v4(),
    'verification-server',
    'healthy',
    45,
    NOW(),
    0,
    100.0,
    NOW()
) ON CONFLICT DO NOTHING;

INSERT INTO system_health (
    id,
    service_name,
    status,
    response_time_ms,
    last_check,
    error_count,
    uptime_percentage,
    created_at
) VALUES (
    uuid_generate_v4(),
    'distribution-server',
    'healthy',
    62,
    NOW(),
    0,
    100.0,
    NOW()
) ON CONFLICT DO NOTHING;