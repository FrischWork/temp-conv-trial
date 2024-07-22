CREATE DATABASE IF NOT EXISTS convenienttrial;

USE convenienttrial;

CREATE TABLE IF NOT EXISTS encryptions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    message_id TEXT NOT NULL,
    message_key TEXT NOT NULL
);
