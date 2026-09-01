-- ============================================================
-- PTMS - Sample Data (plain SQL version of seed.py)
-- ============================================================
-- This is a small, illustrative dataset showing the SAME
-- structure seed.py generates (Project Managers, Team Members
-- reporting to them, projects, tasks, comments) - just written
-- as raw SQL INSERT statements instead of Python.
--
-- Every user's password is: password123
-- (the hash below is a REAL werkzeug hash for that password,
--  so these logins actually work if you run this file)
--
-- Run schema.sql first, then this file.
-- This does NOT replace seed.py - your app keeps using seed.py
-- as normal. This file exists only so you can show a reviewer
-- raw INSERT statements if asked.
-- ============================================================

USE ptms_db;

SET @pw = 'scrypt:32768:8:1$euj0ymQHQf6ATHsp$124c49333e856ee694333f8832b0c2ee1d1f7c7a7b19813d08ff51e9c61429dd47a2ed5ab20cf4184c2e2b7e3b6f6013b82365c2fa77dc21ea5ddf42b74b5ccb';

-- ---- Project Managers (no reports_to - they're at the top) ----
INSERT INTO user (name, email, password_hash, role, reports_to) VALUES
('Rahul Sharma', 'rahul.sharma@company.com', @pw, 'project_manager', NULL),
('Priya Nair',   'priya.nair@company.com',   @pw, 'project_manager', NULL);

-- ---- Team Members (reports_to points to the PM's id above) ----
INSERT INTO user (name, email, password_hash, role, reports_to) VALUES
('Amit Verma',   'amit.verma@company.com',   @pw, 'team_member', 1),
('Sneha Kapoor', 'sneha.kapoor@company.com', @pw, 'team_member', 1),
('Rohan Gupta',  'rohan.gupta@company.com',  @pw, 'team_member', 1),
('Kavya Menon',  'kavya.menon@company.com',  @pw, 'team_member', 2),
('Arjun Rao',    'arjun.rao@company.com',    @pw, 'team_member', 2);

-- ---- Projects (each owned by one PM) ----
INSERT INTO project (name, description, manager_id, deadline) VALUES
('Website Redesign', 'Modernizing the public-facing website with a new design system.', 1, '2026-10-15'),
('CRM Migration',    'Migrating customer data to a new unified platform.',              2, '2026-11-01');

-- ---- Project Members (which team members are on which project) ----
INSERT INTO project_member (project_id, user_id) VALUES
(1, 3), (1, 4), (1, 5),   -- Amit, Sneha, Rohan on Website Redesign
(2, 6), (2, 7);           -- Kavya, Arjun on CRM Migration

-- ---- Tasks ----
INSERT INTO task (project_id, title, description, assigned_to, status, priority, due_date) VALUES
(1, 'Design login page',       'Create the new login page mockup.',        3, 'done',        'medium', '2026-09-10'),
(1, 'Implement dashboard UI',  'Build the dashboard layout in Tailwind.',  4, 'in_progress',  'high',   '2026-09-20'),
(1, 'Test payment flow',       'QA pass on the checkout process.',         5, 'to_do',        'medium', '2026-09-25'),
(2, 'Migrate customer records','Move legacy CRM data to new schema.',      6, 'in_progress',  'high',   '2026-10-05'),
(2, 'Document API endpoints',  'Write API docs for the CRM integration.',  7, 'to_do',        'low',    '2026-10-15');

-- ---- Comments (status updates / reports on tasks) ----
INSERT INTO comment (task_id, user_id, text) VALUES
(1, 3, 'Finished the login page mockup, ready for review.'),
(2, 4, 'Dashboard layout is about 70% done, working on responsiveness next.'),
(4, 6, 'Migrated the first batch of 500 customer records successfully.');