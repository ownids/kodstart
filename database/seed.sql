-- Начальные данные
USE kodstart;
SET NAMES utf8mb4;
INSERT INTO statuses (id, name) VALUES
 (1,'Новая'),(2,'Идёт обучение'),(3,'Обучение завершено'),(4,'Отменена');

INSERT INTO courses (title, description, duration_weeks, price) VALUES
 ('Python для начинающих','Синтаксис, функции, работа с файлами и первые проекты.',8,12000),
 ('Веб-разработка: HTML и CSS','Вёрстка, Flexbox, Grid и адаптивный дизайн.',6,9000),
 ('JavaScript с нуля','DOM, события, асинхронность и работа с API.',8,13000),
 ('Базы данных и SQL','Проектирование БД, нормализация, запросы MySQL.',4,8000);

-- Администратор: логин admin / пароль KodStart2026
INSERT INTO users (login, password_hash, full_name, phone, email, role) VALUES
 ('admin','scrypt:32768:8:1$U7LQRCCb1aO4GEfR$4cf09f663d5ea92a7a8d873dcc2d9bf4851a12da771e2db4cb80bd6ccbcb3a6ed38bc0362298395016d9e12184d451cefca4cf6fb95bc191a58efa02f77beef5','Администратор КодСтарт','8(900)000-00-00','admin@kodstart.local','admin');
