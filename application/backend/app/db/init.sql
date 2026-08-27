-- Initialize default data for the Enterprise QE Platform

-- Insert default priorities
INSERT INTO priorities (name, display_name, sla_hours, color, is_active) VALUES
('P1', 'Critical - Immediate', 1, '#DC2626', true),
('P2', 'High - Urgent', 4, '#EA580C', true),
('P3', 'Medium - Normal', 8, '#CA8A04', true),
('P4', 'Low - Low Priority', 24, '#16A34A', true)
ON CONFLICT (name) DO NOTHING;

-- Insert default categories
INSERT INTO categories (name, description, is_active) VALUES
('Hardware', 'Hardware related issues (laptops, monitors, peripherals)', true),
('Software', 'Software installation, licensing, and configuration', true),
('Network', 'Network connectivity, VPN, WiFi issues', true),
('Access', 'Account access, permissions, password resets', true),
('Security', 'Security incidents, phishing, malware', true),
('Facilities', 'Office facilities, HVAC, lighting, furniture', true),
('HR', 'Human resources, benefits, payroll', true),
('Finance', 'Finance systems, expenses, invoices', true),
('General', 'General inquiries and other requests', true)
ON CONFLICT (name) DO NOTHING;

-- Insert default SLA rules
INSERT INTO sla_rules (category_id, priority_id, response_time_hours, resolution_time_hours, is_active)
SELECT c.id, p.id, 
    CASE p.name 
        WHEN 'P1' THEN 0.5
        WHEN 'P2' THEN 1
        WHEN 'P3' THEN 4
        WHEN 'P4' THEN 8
    END,
    CASE p.name 
        WHEN 'P1' THEN 4
        WHEN 'P2' THEN 8
        WHEN 'P3' THEN 24
        WHEN 'P4' THEN 72
    END,
    true
FROM categories c
CROSS JOIN priorities p
WHERE c.is_active = true AND p.is_active = true
ON CONFLICT DO NOTHING;

-- Create default admin user (password: Admin@123)
INSERT INTO users (email, username, full_name, hashed_password, role, is_active)
VALUES (
    'admin@eqe.com',
    'admin',
    'System Administrator',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PZvO.S',
    'admin',
    true
)
ON CONFLICT (email) DO NOTHING;

-- Create default agent user (password: Agent@123)
INSERT INTO users (email, username, full_name, hashed_password, role, is_active)
VALUES (
    'agent@eqe.com',
    'agent',
    'Support Agent',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PZvO.S',
    'agent',
    true
)
ON CONFLICT (email) DO NOTHING;

-- Create default employee user (password: Employee@123)
INSERT INTO users (email, username, full_name, hashed_password, role, is_active)
VALUES (
    'employee@eqe.com',
    'employee',
    'John Employee',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PZvO.S',
    'employee',
    true
)
ON CONFLICT (email) DO NOTHING;