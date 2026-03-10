USE testi;

-- Create the Player table for saving game progress
CREATE TABLE IF NOT EXISTS Player (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    level INT DEFAULT 1,
    fuel INT DEFAULT 100,
    resources INT DEFAULT 0,
    current_planet_id INT DEFAULT 1,
    last_played TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);