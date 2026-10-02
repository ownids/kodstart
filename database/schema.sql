-- ============================================================
-- ИС «КодСтарт» — запись на курсы программирования
-- Модуль 1. Схема базы данных (MySQL 8 / MariaDB 10.6+)
-- ============================================================
CREATE DATABASE IF NOT EXISTS kodstart
  DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE kodstart;
SET NAMES utf8mb4;

-- Пользователи (клиенты и администратор)
CREATE TABLE users (
    id            INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    login         VARCHAR(50)  NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name     VARCHAR(150) NOT NULL,
    phone         VARCHAR(20)  NOT NULL,
    email         VARCHAR(100) NOT NULL,
    role          ENUM('user','admin') NOT NULL DEFAULT 'user',
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Курсы
CREATE TABLE courses (
    id             INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    title          VARCHAR(100) NOT NULL,
    description    TEXT,
    duration_weeks TINYINT UNSIGNED NOT NULL,
    price          DECIMAL(10,2) NOT NULL
) ENGINE=InnoDB;

-- Справочник статусов заявки
CREATE TABLE statuses (
    id   TINYINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
) ENGINE=InnoDB;

-- Заявки на обучение
CREATE TABLE applications (
    id             INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id        INT UNSIGNED NOT NULL,
    course_id      INT UNSIGNED NOT NULL,
    start_date     DATE NOT NULL,
    payment_method ENUM('cash','card','transfer') NOT NULL,
    comment        VARCHAR(255),
    status_id      TINYINT UNSIGNED NOT NULL DEFAULT 1,
    created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_app_user   FOREIGN KEY (user_id)   REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_app_course FOREIGN KEY (course_id) REFERENCES courses(id),
    CONSTRAINT fk_app_status FOREIGN KEY (status_id) REFERENCES statuses(id)
) ENGINE=InnoDB;
