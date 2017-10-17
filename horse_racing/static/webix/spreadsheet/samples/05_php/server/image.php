<?php

if(isset($_FILES['upload'])){
	$name = basename($_FILES['upload']['name']);
	$ext = explode(".", $name);
    $filename = "images/".md5($name.microtime()).".".$ext[1];
    $httpname = "server/".$filename;

    if (move_uploaded_file($_FILES['upload']['tmp_name'], $filename)) {
        echo json_encode([ "status" => "server", "imageURL" => $httpname ]);
    } else {
        echo "{ status:'error' }";
    }
 }

 ?>