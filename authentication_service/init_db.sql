CREATE DATABASE IF NOT EXISTS convenienttrial;

USE convenienttrial;

CREATE TABLE IF NOT EXISTS authentication (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id TEXT NOT NULL,
    access_token TEXT NOT NULL
);
