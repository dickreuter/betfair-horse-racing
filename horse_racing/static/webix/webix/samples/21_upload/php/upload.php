<?php

ini_set('max_execution_time', 120);
$destination = realpath('./files');

if (isset($_FILES['upload'])){
	$file = $_FILES['upload'];

	$filename = $destination."/".preg_replace("|[\\\/]|", "", $file["name"]);
	$sname = md5($file["name"]);

	//check that file name is valid
    if ($filename !== ""){
    	//overwrite existing files to prevent errors
    	//in real app, you will want to assign the unique names for files
    	if(file_exists($filename))
    		unlink($filename);

        //move_uploaded_file($file["tmp_name"], $filename);
        $res = array("status" => "server", "sname" => $sname);
    } else {
        $res = array("status" => "error");
    }

    echo json_encode($res);
}
	

?>