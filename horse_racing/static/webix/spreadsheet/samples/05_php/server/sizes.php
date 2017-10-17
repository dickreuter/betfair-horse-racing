<?php
require_once("config.php");

$row 	= $_POST["row"];
$column = $_POST["column"];
$size  = $_POST["size"];

$q1 = $db->prepare("delete from sizes where srow=? and scolumn=? and sheet=$sheet");
$q2 = $db->prepare("insert into sizes(srow, scolumn, size, sheet) VALUES(?,?,?,$sheet)");

$q1->execute([$row, $column]);
//do not recreate empty cells
if ($size !== "" && $size !== "0")
	$q2->execute([$row, $column, $size]);