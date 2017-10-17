<?php
	include ('../../common/config.php');
	
	$scheduler = new JSONDataConnector($conn, $dbtype);
	//$scheduler->enable_log("log.txt",true);
	$scheduler->render_table("events","event_id","start_date,end_date,event_name(text),details");
?>