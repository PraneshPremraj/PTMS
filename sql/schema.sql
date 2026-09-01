-- ============================================================
-- PTMS (Project Task Management System) - Database Schema
-- ============================================================
-- This file is a plain-SQL mirror of what models.py + SQLAlchemy
-- already create automatically when you run create_tables.py.
-- It changes NOTHING in the running app - it exists so you can
-- show a reviewer the raw schema directly in MySQL Workbench,
-- without needing to explain the Python ORM layer.
--
-- How to use:
--   Open a new query tab in MySQL Workbench and run this file.
--   (Safe to run on a fresh database. If ptms_db already exists
--    with data from the app, you don't need to run this at all -
--    your existing tables already match this exactly.)
-- ============================================================

CREATE DATABASE IF NOT EXISTS ptms_db;
USE ptms_db;

-- ------------------------------------------------------------
-- Table: user
-- Stores both Project Managers and Team Members (role column
-- decides which). reports_to is a self-referencing FK: a Team
-- Member's reports_to points to their Project Manager's id.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(30) NOT NULL,                 -- 'project_manager' or 'team_member'
    reports_to INT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (reports_to) REFERENCES user(id)
);

-- ------------------------------------------------------------
-- Table: project
-- Each project belongs to exactly one Project Manager.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS project (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    description TEXT NULL,
    manager_id INT NOT NULL,
    deadline DATE NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (manager_id) REFERENCES user(id)
);

-- ------------------------------------------------------------
-- Table: project_member
-- Many-to-many link: which team members are on which project.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS project_member (
    id INT AUTO_INCREMENT PRIMARY KEY,
    project_id INT NOT NULL,
    user_id INT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES project(id),
    FOREIGN KEY (user_id) REFERENCES user(id)
);

-- ------------------------------------------------------------
-- Table: task
-- status: 'to_do' | 'in_progress' | 'done'
-- priority: 'low' | 'medium' | 'high'
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS task (
    id INT AUTO_INCREMENT PRIMARY KEY,
    project_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT NULL,
    assigned_to INT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'to_do',
    priority VARCHAR(10) NOT NULL DEFAULT 'medium',
    due_date DATE NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES project(id),
    FOREIGN KEY (assigned_to) REFERENCES user(id)
);

-- ------------------------------------------------------------
-- Table: comment
-- Used as a lightweight status-update / report thread on a task.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS comment (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_id INT NOT NULL,
    user_id INT NOT NULL,
    text TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES task(id),
    FOREIGN KEY (user_id) REFERENCES user(id)
);