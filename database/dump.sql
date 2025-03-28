-- This table stores user information, including their name, email, phone number, and registration date.
CREATE TABLE Users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- This table holds data about the stations, including their name, address, and geographic coordinates.
CREATE TABLE Stations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    address VARCHAR(255) NOT NULL,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8)
);

-- This table contains information about the power banks, such as their serial number, status, and the station they are associated with.
CREATE TABLE PowerBanks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    serial_number VARCHAR(50) UNIQUE NOT NULL,
    status ENUM('available', 'rented', 'maintenance') DEFAULT 'available',
    station_id INT,
    FOREIGN KEY (station_id) REFERENCES Stations(id)
);

-- This table records the orders, including the user who made the order, the power bank rented, the start and end times of the rental, and the status of the order.
CREATE TABLE Orders (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    powerbank_id INT,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    status ENUM('active', 'completed', 'canceled') DEFAULT 'active',
    FOREIGN KEY (user_id) REFERENCES Users(id),
    FOREIGN KEY (powerbank_id) REFERENCES PowerBanks(id)
);

-- This table logs payment transactions, including the order associated with the transaction, the amount paid, the time of the transaction, and the status of the transaction.
CREATE TABLE PaymentTransactions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT,
    amount DECIMAL(10, 2),
    transaction_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('success', 'failed') DEFAULT 'success',
    FOREIGN KEY (order_id) REFERENCES Orders(id)
);

-- This table describes the venues where the stations are located, including the station ID, venue name, and venue type.
CREATE TABLE StationLocations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    station_id INT,
    venue_name VARCHAR(255),
    venue_type VARCHAR(100),
    FOREIGN KEY (station_id) REFERENCES Stations(id)
);

-- Inserting test data into the Users table
INSERT INTO Users (name, email, phone) VALUES
('Ivan Ivanov', 'ivan@example.com', '1234567890'),
('Maria Petrova', 'maria@example.com', '0987654321'),
('Alexey Sidorov', 'alexey@example.com', '1122334455');

-- Inserting test data into the Stations table
INSERT INTO Stations (name, address, latitude, longitude) VALUES
('Station 1', 'Pushkin St., 1', 55.7558, 37.6173),
('Station 2', 'Lermontov St., 2', 55.7580, 37.6200),
('Station 3', 'Tolstoy St., 3', 55.7600, 37.6250');

-- Inserting test data into the PowerBanks table
INSERT INTO PowerBanks (serial_number, status, station_id) VALUES
('PB001', 'available', 1),
('PB002', 'rented', 1),
('PB003', 'maintenance', 2),
('PB004', 'available', 3);

-- Inserting test data into the Orders table
INSERT INTO Orders (user_id, powerbank_id, end_time, status) VALUES
(1, 2, NOW() + INTERVAL 1 HOUR, 'active'),
(2, 1, NULL, 'completed'),
(3, 4, NOW() + INTERVAL 2 HOUR, 'canceled');

-- Inserting test data into the PaymentTransactions table
INSERT INTO PaymentTransactions (order_id, amount, status) VALUES
(1, 100.00, 'success'),
(2, 50.00, 'failed'),
(3, 75.00, 'success');

-- Inserting test data into the StationLocations table
INSERT INTO StationLocations (station_id, venue_name, venue_type) VALUES
(1, 'Cafe "Cozy"', 'cafe'),
(2, 'Shopping Mall "Mega"', 'shopping mall'),
(3, 'Park "Green"', 'park');
