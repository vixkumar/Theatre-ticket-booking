-- Drop foreign key constraint
ALTER TABLE `Booking` DROP FOREIGN KEY `booking_ibfk_1`;

-- Modify the column
ALTER TABLE `Customer` MODIFY `c_id` INT AUTO_INCREMENT;

-- Add back foreign key constraint
ALTER TABLE `Booking` ADD CONSTRAINT `booking_ibfk_1` FOREIGN KEY (`c_id`) REFERENCES `Customer` (`c_id`); 