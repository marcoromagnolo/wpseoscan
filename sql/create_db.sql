CREATE DATABASE wpseoscan
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;
CREATE USER 'wpseoscan'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON wpseoscan.* TO 'wpseoscan'@'localhost';
FLUSH PRIVILEGES;