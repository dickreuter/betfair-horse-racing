<?php

	//connect to database
	$db = new SQLite3('kanban.sqlite');

	$operation = $_POST["webix_operation"];

	// get id and data
	//  !!! you need to escape data in real app, to prevent SQL injection !!!
	$id = @$_POST['id'];
	$text = $_POST["text"];
	$details = $_POST["details"];
	$status = $_POST["status"];
	$personId = $_POST["personId"];


	if ($operation == "insert"){
		//adding new record
		$db->query("INSERT INTO tasks(text, details, status, personId) VALUES('$text', '$details', '$status', '$personId')");
		echo '{ "id":"'.$id.'", "status":"success", "newid":"'.$db->lastInsertRowID().'" }';

	} else if ($operation == "update"){
		//updating record
		$db->query("UPDATE tasks SET text='$text', details='$details', status='$status', personId='$personId' WHERE id='$id'");
		echo '{ "id":"'.$id.'", "status":"success" }';

	} else if ($operation == "delete"){
		//deleting record
		$db->query("DELETE FROM tasks WHERE id='$id'");
		echo '{ "id":"'.$id.'", "status":"success" }';

	} else
		echo "Not supported operation";

?>