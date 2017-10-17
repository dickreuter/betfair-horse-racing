<?php
require_once("config.php");

$name = $_POST["name"];
$text = $_POST["text"];

$q1 = $db->prepare("insert into styles(name, value, sheet) VALUES(?,?,?)");
$q1->execute([$name, $text, $sheet]);