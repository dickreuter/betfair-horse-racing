<?php
require_once("config.php");

$data   = $db->query("select * from data where sheet=$sheet ORDER BY srow, scolumn ");
$sizes  = $db->query("select * from sizes where sheet=$sheet");
$spans  = $db->query("select * from spans where sheet=$sheet");
$styles = $db->query("select * from styles where sheet=$sheet");

function d2a($q){
	$res = [];
	if ($q)
		while ($row = $q->fetch(PDO::FETCH_ASSOC))
			$res[] = [ $row["srow"], $row["scolumn"], $row["svalue"], $row["style"] ];
	return $res;
}

function s2a($q){
	$res = [];
	if ($q)
		while ($row = $q->fetch(PDO::FETCH_ASSOC))
			$res[] = [ $row["name"], $row["value"] ];
	return $res;
}

function i2a($q){
	$res = [];
	if ($q)
		while ($row = $q->fetch(PDO::FETCH_ASSOC))
			$res[] = [ $row["srow"], $row["scolumn"], $row["size"] ];
	return $res;
}

function p2a($q){
	$res = [];
	if ($q)
		while ($row = $q->fetch(PDO::FETCH_ASSOC))
			$res[] = [ $row["srow"], $row["scolumn"], $row["x"], $row["y"] ];
	return $res;
}

echo json_encode([
	"data"   => d2a($data),
	"styles" => s2a($styles),
	"sizes"  => i2a($sizes),
	"spans"  => p2a($spans)
]);