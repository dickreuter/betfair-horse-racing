<?php

$sheet=1;
if (isset($_GET["sheet"]))
	$sheet = $_GET["sheet"];

$db = new PDO('mysql:host=127.0.0.1;dbname=spreadsheet;charset=utf8', 'root', '1');
