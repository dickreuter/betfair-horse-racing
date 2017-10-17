<?php

include_once "PHPFileSystem.php";

//read root folder from config file
include_once "./config.php";
$api = new PHPFileSystem($root_folder);

if (isset($_POST["action"])){
	if ($_POST["action"] == "upload"){
		$result = $api->upload(
			$_POST["target"],
			$_FILES['upload']['name'], 
			$_FILES['upload']['tmp_name']);

		echo json_encode($result);
	} else if ($_POST["action"] == "download"){

		$info = $api->download($_POST["source"]);
		header('Content-Description: File Transfer');
		header('Content-Type: application/octet-stream');
		header('Content-Disposition: attachment; filename="'.$info->getName().'"');
		header('Content-Transfer-Encoding: binary');
		header('Connection: Keep-Alive');
		header('Expires: 0');
		header('Cache-Control: must-revalidate, post-check=0, pre-check=0');
		header('Pragma: public');
		header('Content-Length: ' . $info->getSize());
		echo $info->getContent();
	} else if ($_POST["action"] == "preview"){
		$info = $api->download($_POST["source"]);
		$ext = $info->getExtension();
		$type = $api->extensions[$ext];
		if($type == "image"){
			echo $info->getBase64();
		}
		else if($type == "code" || $ext == "text"){
			echo htmlspecialchars($info->getContent());
		}
		else
			echo "";
    }else if ($_POST["action"] == "remove"){
		echo json_encode( $api->batch($_POST["source"], array($api, "rm")) );
	} else if ($_POST["action"] == "copy"){
		echo json_encode( $api->batch($_POST["source"], array($api, "cp"), $_POST["target"]) );
	} else if ($_POST["action"] == "move"){
		echo json_encode( $api->batch($_POST["source"], array($api, "mv"), $_POST["target"]) );
	} else if ($_POST["action"] == "create"){
		echo json_encode( $api->mkdir($_POST["source"], $_POST["target"]) );
	} else if ($_POST["action"] == "rename"){
		echo json_encode( $api->rename($_POST["source"], $_POST["target"]) );
	}
}
else{
    $api->virtualRoot("Files");
    echo json_encode( $api->ls("/", true));
}
?>