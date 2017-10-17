<?php
require_once("config.php");

$row 	= $_POST["row"];
$column = $_POST["column"];
$value  = $_POST["value"];
$style  = $_POST["style"];

$q1 = $db->prepare("delete from data where srow=? and scolumn=? and sheet=$sheet");
$q2 = $db->prepare("insert into data(srow,scolumn,svalue,style,sheet) VALUES(?,?,?,?,$sheet)");

$q1->execute([$row, $column]);
//do not recreate empty cells
if ($value !== "" || $style !== "")
	$q2->execute([$row, $column, $value, $style]);