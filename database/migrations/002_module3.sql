-- ============================================================
-- Модуль 3. Доработка БД под все сценарии модулей 1–2
-- ============================================================
USE kodstart;
SET NAMES utf8mb4;

-- Уникальность email и индексы для фильтров/поиска админ-панели
ALTER TABLE users ADD CONSTRAINT uq_users_email UNIQUE (email);
CREATE INDEX idx_app_status  ON applications(status_id);
CREATE INDEX idx_app_created ON applications(created_at);

-- Время последнего изменения заявки
ALTER TABLE applications
    ADD COLUMN updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP AFTER created_at;

-- Ограничения целостности
ALTER TABLE courses ADD CONSTRAINT chk_course_price    CHECK (price >= 0);
ALTER TABLE courses ADD CONSTRAINT chk_course_duration CHECK (duration_weeks BETWEEN 1 AND 52);

-- История смены статусов (кто и когда изменил)
CREATE TABLE status_history (
    id             INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    application_id INT UNSIGNED NOT NULL,
    status_id      TINYINT UNSIGNED NOT NULL,
    changed_by     INT UNSIGNED NOT NULL,
    changed_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_hist_app    FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE,
    CONSTRAINT fk_hist_status FOREIGN KEY (status_id)      REFERENCES statuses(id),
    CONSTRAINT fk_hist_user   FOREIGN KEY (changed_by)     REFERENCES users(id)
) ENGINE=InnoDB;
