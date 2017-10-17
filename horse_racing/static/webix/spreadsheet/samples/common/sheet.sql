-- Valentina Studio --
-- MySQL dump --
-- ---------------------------------------------------------


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
-- ---------------------------------------------------------


-- CREATE TABLE "data" -------------------------------------
CREATE TABLE `data` ( 
	`sheet` Int( 255 ) NOT NULL,
	`math` VarChar( 255 ) NOT NULL,
	`style` VarChar( 255 ) NOT NULL,
	`srow` Int( 255 ) NOT NULL,
	`scolumn` Int( 255 ) NOT NULL,
	`svalue` VarChar( 255 ) NOT NULL )
ENGINE = InnoDB;
-- ---------------------------------------------------------


-- CREATE TABLE "sizes" ------------------------------------
CREATE TABLE `sizes` ( 
	`srow` Int( 255 ) NOT NULL,
	`scolumn` Int( 255 ) NOT NULL,
	`size` Int( 255 ) NOT NULL,
	`sheet` Int( 255 ) NOT NULL )
ENGINE = InnoDB;
-- ---------------------------------------------------------


-- CREATE TABLE "spans" ------------------------------------
CREATE TABLE `spans` ( 
	`srow` Int( 255 ) NOT NULL,
	`scolumn` Int( 255 ) NOT NULL,
	`x` Int( 255 ) NOT NULL,
	`y` Int( 255 ) NOT NULL,
	`sheet` Int( 255 ) NOT NULL )
ENGINE = InnoDB;
-- ---------------------------------------------------------


-- CREATE TABLE "styles" -----------------------------------
CREATE TABLE `styles` ( 
	`name` VarChar( 255 ) NOT NULL,
	`value` Text NOT NULL,
	`sheet` Int( 255 ) NOT NULL )
ENGINE = InnoDB;
-- ---------------------------------------------------------


-- Dump data of "data" -------------------------------------
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '1', '', 'wss4', '5', '5', '' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '1', '', 'wss4', '5', '6', '' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '1', '', 'wss4', '5', '4', '' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '1', '', 'wss4', '5', '7', '' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '1', '', 'wss5', '4', '4', '' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '1', '', 'wss5', '4', '7', '' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '1', '', 'wss5', '4', '6', '' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '1', '', 'wss5', '4', '5', '' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '1', '', 'wss6', '6', '4', '' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '1', '', 'wss6', '6', '6', '' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '1', '', 'wss6', '6', '7', '' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '1', '', 'wss6', '6', '5', '' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '1', '', 'wss8', '2', '3', '1' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '1', '', 'wss8', '3', '3', '2' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '1', '', 'wss8', '4', '3', '3' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '1', '', 'wss8', '5', '3', '4' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '1', '', 'wss8', '6', '3', '5' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '1', '', '', '3', '4', 'a' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '1', '', 'wss11', '2', '8', '1' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '1', '', 'wss11', '4', '8', '3' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '1', '', 'wss11', '3', '8', '2' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '1', '', 'wss11', '5', '8', '4' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '1', '', 'wss11', '6', '8', '5' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '1', '', 'wss12', '3', '7', 'd' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '1', '', 'wss15', '3', '6', 'c' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '1', '', 'wss18', '2', '6', 'Right' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '1', '', 'wss12', '8', '4', '' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '1', '', 'wss17', '3', '5', 'b' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '1', '', 'wss20', '2', '5', 'Left' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '1', '', '', '1', '6', '1' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '1', '', 'wss27', '1', '5', 'center' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '1', '', 'wss29', '1', '3', 'Header' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '1', '', 'wss12', '9', '5', '' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '3', '', 'wss3', '3', '4', '' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '3', '', 'wss3', '3', '3', '' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '2', '', '', '2', '4', '-' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '3', '', '', '2', '4', '-' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '3', '', 'wss1', '2', '2', '-' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '3', '', 'wss2', '2', '3', 'Page 1' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '2', '', 'wss1', '2', '2', '-' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '3', '', 'wss3', '3', '2', '' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '2', '', 'wss5', '2', '3', 'Page 2' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '2', '', 'wss6', '3', '2', '' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '2', '', 'wss6', '3', '3', '' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '2', '', 'wss6', '3', '4', '' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '4', '', 'wss3', '2', '4', '2015' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '4', '', 'wss3', '2', '3', '2014' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '4', '', 'wss3', '2', '2', '2013' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '4', '', '', '3', '1', 'Sport gears' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '4', '', '', '4', '1', 'Gadgets' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '4', '', '', '5', '1', 'Beverage' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '4', '', 'wss3', '2', '5', '2016' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '4', '', 'wss4', '1', '5', 'Prediction' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '4', '', 'wss6', '1', '2', '' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '4', '', 'wss7', '1', '3', 'Sales' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '4', '', 'wss6', '1', '4', '' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '4', '', 'wss1', '2', '1', 'Department' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '4', '', 'wss8', '1', '1', '' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '4', '', 'wss11', '6', '1', 'Total' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '4', '', 'wss5', '3', '2', '4550' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '4', '', 'wss5', '3', '3', '4780' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '4', '', 'wss5', '4', '3', '4483' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '4', '', 'wss5', '5', '2', '750' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '4', '', 'wss5', '4', '2', '2245' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '4', '', 'wss5', '4', '4', '7460' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '4', '', 'wss5', '5', '3', '640' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '4', '', 'wss12', '6', '2', '=SUM(B3:B5)' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '4', '', 'wss12', '6', '3', '=SUM(C3:C5)' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '4', '', 'wss12', '6', '4', '=SUM(D3:D5)' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '4', '', 'wss5', '3', '5', '=D3*1.2' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '4', '', 'wss14', '4', '5', '=D4*1.2' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '4', '', 'wss12', '6', '5', '=SUM(E3:E5)' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '4', '', '', '9', '5', '=' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '4', '', 'wss5', '5', '5', '=D5*1.1' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '4', '', 'wss5', '5', '4', '755' );
INSERT INTO `data`(`sheet`,`math`,`style`,`srow`,`scolumn`,`svalue`) VALUES ( '4', '', 'wss5', '3', '4', '4920' );
-- ---------------------------------------------------------


-- Dump data of "sizes" ------------------------------------
INSERT INTO `sizes`(`srow`,`scolumn`,`size`,`sheet`) VALUES ( '1', '0', '95', '1' );
INSERT INTO `sizes`(`srow`,`scolumn`,`size`,`sheet`) VALUES ( '0', '2', '115', '1' );
INSERT INTO `sizes`(`srow`,`scolumn`,`size`,`sheet`) VALUES ( '14', '0', '94', '1' );
INSERT INTO `sizes`(`srow`,`scolumn`,`size`,`sheet`) VALUES ( '0', '1', '169', '4' );
-- ---------------------------------------------------------


-- Dump data of "spans" ------------------------------------
INSERT INTO `spans`(`srow`,`scolumn`,`x`,`y`,`sheet`) VALUES ( '1', '3', '6', '1', '1' );
-- ---------------------------------------------------------


-- Dump data of "styles" -----------------------------------
INSERT INTO `styles`(`name`,`value`,`sheet`) VALUES ( 'wss1', ';#ACAC00', '1' );
INSERT INTO `styles`(`name`,`value`,`sheet`) VALUES ( 'wss2', '#FFFFFF;#ACAC00', '1' );
INSERT INTO `styles`(`name`,`value`,`sheet`) VALUES ( 'wss3', '#FF3E3E;', '1' );
INSERT INTO `styles`(`name`,`value`,`sheet`) VALUES ( 'wss4', ';#FF9E3E', '1' );
INSERT INTO `styles`(`name`,`value`,`sheet`) VALUES ( 'wss5', '#FF3E3E;#FE860E', '1' );
INSERT INTO `styles`(`name`,`value`,`sheet`) VALUES ( 'wss6', ';#FFCE9E', '1' );
INSERT INTO `styles`(`name`,`value`,`sheet`) VALUES ( 'wss7', ';#DD6E00', '1' );
INSERT INTO `styles`(`name`,`value`,`sheet`) VALUES ( 'wss8', '#FFFFFF;#DD6E00', '1' );
INSERT INTO `styles`(`name`,`value`,`sheet`) VALUES ( 'wss9', ';#DD6E00;', '1' );
INSERT INTO `styles`(`name`,`value`,`sheet`) VALUES ( 'wss10', '#FFFFFF;#DD6E00;left', '1' );
INSERT INTO `styles`(`name`,`value`,`sheet`) VALUES ( 'wss11', '#FFFFFF;#DD6E00;right', '1' );
INSERT INTO `styles`(`name`,`value`,`sheet`) VALUES ( 'wss12', ';;right', '1' );
INSERT INTO `styles`(`name`,`value`,`sheet`) VALUES ( 'wss13', ';;center', '1' );
INSERT INTO `styles`(`name`,`value`,`sheet`) VALUES ( 'wss14', '#000;#3E7C00;center', '1' );
INSERT INTO `styles`(`name`,`value`,`sheet`) VALUES ( 'wss15', '#000;#FFFFFF;center', '1' );
INSERT INTO `styles`(`name`,`value`,`sheet`) VALUES ( 'wss16', '#000;#fff;left', '1' );
INSERT INTO `styles`(`name`,`value`,`sheet`) VALUES ( 'wss17', '#000;#fff;center', '1' );
INSERT INTO `styles`(`name`,`value`,`sheet`) VALUES ( 'wss18', '#000;#fff;right', '1' );
INSERT INTO `styles`(`name`,`value`,`sheet`) VALUES ( 'wss19', ';;left', '1' );
INSERT INTO `styles`(`name`,`value`,`sheet`) VALUES ( 'wss20', '#DD0000;#fff;left', '1' );
INSERT INTO `styles`(`name`,`value`,`sheet`) VALUES ( 'wss21', '#AC5600;;', '1' );
INSERT INTO `styles`(`name`,`value`,`sheet`) VALUES ( 'wss22', '#AC5600;#AC0000;left', '1' );
INSERT INTO `styles`(`name`,`value`,`sheet`) VALUES ( 'wss23', '#FFFFFF;#AC0000;left', '1' );
INSERT INTO `styles`(`name`,`value`,`sheet`) VALUES ( 'wss24', '#FFFFFF;#3E7C00;left', '1' );
INSERT INTO `styles`(`name`,`value`,`sheet`) VALUES ( 'wss25', '#FFFFFF;#0000AC;left', '1' );
INSERT INTO `styles`(`name`,`value`,`sheet`) VALUES ( 'wss26', '#FFFFFF;#DDDD00;left', '1' );
INSERT INTO `styles`(`name`,`value`,`sheet`) VALUES ( 'wss27', '#FFFFFF;#AC00AC;left', '1' );
INSERT INTO `styles`(`name`,`value`,`sheet`) VALUES ( 'wss28', ';#0000AC;center', '1' );
INSERT INTO `styles`(`name`,`value`,`sheet`) VALUES ( 'wss29', '#FFFFFF;#0000AC;center', '1' );
INSERT INTO `styles`(`name`,`value`,`sheet`) VALUES ( 'wss1', ';;right', '3' );
INSERT INTO `styles`(`name`,`value`,`sheet`) VALUES ( 'wss2', ';;center', '3' );
INSERT INTO `styles`(`name`,`value`,`sheet`) VALUES ( 'wss1', ';;right', '2' );
INSERT INTO `styles`(`name`,`value`,`sheet`) VALUES ( 'wss2', ';;center', '2' );
INSERT INTO `styles`(`name`,`value`,`sheet`) VALUES ( 'wss3', ';#FFB66E;', '3' );
INSERT INTO `styles`(`name`,`value`,`sheet`) VALUES ( 'wss3', ';#9E3EFF;', '2' );
INSERT INTO `styles`(`name`,`value`,`sheet`) VALUES ( 'wss4', '#000;#fff;right', '2' );
INSERT INTO `styles`(`name`,`value`,`sheet`) VALUES ( 'wss5', '#000;#fff;center', '2' );
INSERT INTO `styles`(`name`,`value`,`sheet`) VALUES ( 'wss6', '#000;#3E9EFF;left', '2' );
INSERT INTO `styles`(`name`,`value`,`sheet`) VALUES ( 'wss1', ';#CEFEFE;', '4' );
INSERT INTO `styles`(`name`,`value`,`sheet`) VALUES ( 'wss2', ';#CEE6FE;', '4' );
INSERT INTO `styles`(`name`,`value`,`sheet`) VALUES ( 'wss3', '#000;#CEE6FE;center', '4' );
INSERT INTO `styles`(`name`,`value`,`sheet`) VALUES ( 'wss4', '#000;#CEFEFE;center', '4' );
INSERT INTO `styles`(`name`,`value`,`sheet`) VALUES ( 'wss5', ';;center', '4' );
INSERT INTO `styles`(`name`,`value`,`sheet`) VALUES ( 'wss6', '#000;#CEFEE6;left', '4' );
INSERT INTO `styles`(`name`,`value`,`sheet`) VALUES ( 'wss7', '#000;#CEFEE6;center', '4' );
INSERT INTO `styles`(`name`,`value`,`sheet`) VALUES ( 'wss8', '#000;#FFFFFF;left', '4' );
INSERT INTO `styles`(`name`,`value`,`sheet`) VALUES ( 'wss9', '#FFFFFF;;', '4' );
INSERT INTO `styles`(`name`,`value`,`sheet`) VALUES ( 'wss10', '#FFFFFF;#424242;', '4' );
INSERT INTO `styles`(`name`,`value`,`sheet`) VALUES ( 'wss11', '#FFFFFF;#424242;right', '4' );
INSERT INTO `styles`(`name`,`value`,`sheet`) VALUES ( 'wss12', '#FFFFFF;#424242;center', '4' );
INSERT INTO `styles`(`name`,`value`,`sheet`) VALUES ( 'wss13', '#000;#fff;left', '4' );
INSERT INTO `styles`(`name`,`value`,`sheet`) VALUES ( 'wss14', '#000;#fff;center', '4' );
-- ---------------------------------------------------------


-- CREATE INDEX "index_sheet" ------------------------------
CREATE INDEX `index_sheet` USING BTREE ON `data`( `sheet` );
-- ---------------------------------------------------------


-- CREATE INDEX "index_sheet1" -----------------------------
CREATE INDEX `index_sheet1` USING BTREE ON `spans`( `sheet` );
-- ---------------------------------------------------------


/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
-- ---------------------------------------------------------


