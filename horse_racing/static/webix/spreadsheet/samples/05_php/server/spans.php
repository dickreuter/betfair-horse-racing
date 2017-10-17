<?php
require_once("config.php");

$row 	= $_POST["row"];
$column = $_POST["column"];
$x	  	=  $_POST["x"];
$y	  	=  $_POST["y"];

$q1 = $db->prepare("delete from spans where srow=? and scolumn=? and sheet=$sheet");
$q2 = $db->prepare("insert into spans(srow, scolumn, x, y, sheet) VALUES(?,?,?,?,$sheet)");

$q1->execute([$row, $column]);
//do not recreate empty cells
if ($x > 1 || $y > 1)
	$q2->execute([$row, $column, $x, $y]);
