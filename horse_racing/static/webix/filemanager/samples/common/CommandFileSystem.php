<?php
require_once("FileSystem.php");

class CommandFileSystem implements iFileSystem{
	public  $debug = false;
	public $batchSeparator = ",";
	public $extensions = array(
		"docx" 	=> "doc",
		"xsl" 	=> "excel",
		"xslx" 	=> "excel",
		"txt"	=> "text", "md"=>"text",
		"html"	=> "code", "js"=>"code", "json"=>"code", "css"=>"code", "php"=>"code", "htm"=>"code",
		"mpg"	=> "video", "mp4"=>"video","avi"=>"video","mkv"=>"video",
		"png"	=> "image", "jpg"=>"image", "gif"=>"image",
		"mp3"	=> "audio", "ogg"=>"audio",
		"zip"	=> "archive", "rar"=>"archive", "7z"=>"archive", "tar"=>"archive", "gz"=>"archive"
	);

	private $top;
	private $url;
	private $win;
	protected $sep;
	private $vroot = false;

	function __construct($topdir = "/", $topurl = "/"){
		$this->top = realpath($topdir);
		$this->url = $topurl;
		$this->win = (strtoupper(substr(PHP_OS, 0, 3)) === 'WIN');
		$this->sep = $this->win ? "\\" : "/";

		if (substr($this->top, -1) != $this->sep)
			$this->top .= $this->sep;
	}

	function virtualRoot($name){
		$this->vroot = $name;
	}

	private function get_type($entry){
		$ext = pathinfo($entry, PATHINFO_EXTENSION);
		if ($ext && isset($this->extensions[$ext]))
			return $this->extensions[$ext];
		return $ext;
	}

	private function top_dir($source){
		$data = explode($this->sep, $source);
		return $data[sizeof($data)-1];
	}

	private function file_id($full){
 		return str_replace($this->top, "", $full);
	}

	private function safe_name($name){
		$name = str_replace("..","",preg_replace("|[^a-z0-9-_\\.\\/\\:]|i", "", str_replace("\\","/",$name)));
		if ($this->win)
			$name = str_replace("/", "\\", $name);
		else
			$name = str_replace("\\", "/", $name);

		return preg_replace('#[\\\\\\/]+#', $this->sep, $name);
	}
	private function check_path($path, $folder = false, $file = false){
		$path = $this->safe_name($this->top.$path);
		
		if (!$path || strpos($path, $this->top) !== 0)
			throw new Exception("Path is outside of sandbox: ".$path);

		if ($folder && $file){
			if (!file_exists($path))
				throw new Exception("Path is invalid: ".$path);
		}
		else {
			if ($folder){
				/*if (!is_dir($path))
					throw new Exception("Path is not a Directory: ".$path);*/
				if (is_dir($path))
					if (substr($path, -1) != $this->sep)
						$path .= $this->sep;
			}

			if ($file && !is_file($path))
				throw new Exception("Path is not a File : ".$path);
		}
		return $path;
	}

	private function exec($command){
		if ($this->debug)
			echo $command."\n";
		else
			exec($command);
	}
	private function log($message){
		if ($this->debug)
			echo $message."\n";
	}

    protected function unlink($path){
		if ($this->win){
			if (is_file($path))
				$this->exec("del /s $path");
			else
				$this->exec("rd /s /q $path");
		}
		else
			$this->exec("rm -rf $path");

	}
    protected function makedir($target){
		$this->exec("mkdir $target");
	}
	protected function ren($source, $target, $name){
		if ($this->win)
			$this->exec("rename $source $name");
		else
			$this->exec("mv -rf $source $target");
	}
    protected function move($source, $target){
		if ($this->win){
			if (is_file($source))
				$this->exec("move $source $target");
			else
				$this->exec("robocopy $source ".$this->safe_name($target.$this->sep.$this->top_dir($source))." /e /move");
		}
		else
			$this->exec("mv -rf $source $target");
	}
    protected function copy($source, $target){

		if ($this->win){
			if (is_file($source))
				$this->exec("copy $source $target");
			else
				$this->exec("robocopy $source ".$this->safe_name($target.$this->sep.$this->top_dir($source))." /e");
		}
		else
			$this->exec("cp -rf $source $target");
	}

	private function check_child_dirs($dir){
		$result = false;
        $dir = $this->check_path($dir, true);
        if(!file_exists($dir))
            return false;

        $d = dir($dir);

        while($result == false && false != ($entry = $d->read())){
            if ($entry == "." || $entry == "..") continue;

            $file = $d->path.$entry;
            $isdir = is_dir($file);
            if($isdir)
                $result = true;
        }

        $d->close();

        return $result;
	}

	private function dir($dir, $nested, $mode="all"){
		$requestDir = $dir;
		$dir = $this->check_path($dir, true);
		$this->log("List $dir");

		$data = array();
		if(!is_dir($dir))
		    return [];
		$d = dir($dir);
		$folder = str_replace("\\","/",str_replace($this->top, "", $dir));

		while(false != ($entry = $d->read())){
			if ($entry == "." || $entry == "..") continue;

			$file = $d->path.$entry;
			$isdir = is_dir($file);
			$temp = false;
			if(($mode == "folders"&&$isdir) || ($mode == "all")|| ($mode == "branch") || ($mode == "files" && !$isdir)){
				$temp = array(
					"id" => $folder.$entry,
					"value" => $entry,
					"type" => $isdir ? "folder" : $this->get_type($entry),
					"size" => $isdir ? 0 : filesize($file),
					"date" => filemtime($file)
				);
				if($mode == "folders"){
					$temp["webix_files"] = "1";
				}
				if($mode == "branch"&&$isdir){
                    $temp["webix_branch"] = "1";
                    if($this->check_child_dirs($folder.$entry))
                        $temp["webix_child_branch"] = "1";
                }

                if(!file_exists($this->check_path($temp["id"], true)))
                    $temp= false;

			}

			if ( $temp){
			    if($isdir && $nested && $mode != "files"){
			        $temp["data"] = $this->dir($temp["id"], $nested, $mode);
			    }
			    $data[] = $temp;

			}


		}
		$d->close();

		usort($data, array($this, "sort"));

		return ( $mode == "files" || ($mode == "branch" &&!$this->vroot) ? array( "parent" => $requestDir, "data"=> $data ) : $data );
	}
	
	public function ls($dir, $nested = false, $mode="all"){
		$data = $this->dir($dir, $nested, $mode);
		if ($this->vroot)
			return array(
				array( 
					"value" => $this->vroot,
					"type" => "folder",
					"size" => 0,
					"date" => 0,
					"id" => "/",
					"data" => &$data,
					"open" => true
				)
			);
		
		return $data;
	}

	public function sort($a, $b){
		$af = $a["type"] == "folder";
		$bf = $b["type"] == "folder";
		if ($af && !$bf) return -1;
		if ($bf && !$af) return 1;

		return $a["value"] > $b["value"] ? 1 : ($a["value"] < $b["value"] ? -1 : 0);
	}

	public function batch($source, $operation, $target = null){
		if (!is_array($source))
			$source = explode($this->batchSeparator, $source);

		$result = array();
		for ($i=0; $i < sizeof($source); $i++)
			if ($target !== null)
				$result[] = call_user_func($operation, $source[$i], $target);
			else
				$result[] = call_user_func($operation, $source[$i]);
		
		return $result;
	}

	public function rm($file){
		$file = $this->check_path($file, true, true);

		//do not allow root deletion
		if ($this->file_id($file) !== "")
			$this->unlink($file);

		return "ok";
	}

	private function set_unique_name($source, $target, $filename){
	    $new_name = '';

        if(is_dir($this->check_path($source))){
            $new_name = $this->resolve_existent_folder($target,$filename);
        }
        else{
            $new_name = $this->resolve_existent_file($target,$filename);
        }

		if($new_name != $filename){
		    $this->rename($target.$this->sep.$filename,$new_name);
		}


        return $new_name;
	}

	private function copy_paste_rename($source, $target, $filename, $new_name){
		// rename the moved file
        $temp_name = $this->set_unique_name($source, $target, $filename);
        // restore teh name of the existent file
        $this->rename($target.$this->sep.$new_name,$filename);
        // set the unique name to the new file
        $this->rename($target.$this->sep.$temp_name,$new_name);

	}

	public function cp($source, $target){
		$filename = basename($source);

		// rename an existent file in target
        // to avoid deleting files with same names
        $new_name = $this->set_unique_name($source, $target, $filename);

		$s = $this->check_path($source, true, true);

		$t = $this->check_path($target);

		$this->copy($s, $t);

		if($new_name != $filename){
			$this->copy_paste_rename($source, $target, $filename, $new_name);
		}

		$id = str_replace("\\","/",str_replace($this->top, "", $t.$this->sep.$new_name));

    	return array( "id" => $id, "value" => $new_name);
	}
	public function mv($source, $target){

		$filename = basename($source);

		// rename an existent file in target
		// to avoid deleting files with same names
        $new_name = $this->set_unique_name($source, $target, $filename);


		$s = $this->check_path($source, true, true);
		$t = $this->check_path($target);

		$this->move($s, $t);

		if($new_name != $filename){
			$this->copy_paste_rename($source, $target, $filename, $new_name);
		}

		$id = str_replace("\\","/",str_replace($this->top, "", $t.$this->sep.$new_name));
		return array( "id" => $id, "value" => $new_name);
	}

	public function touch($path, $content = ""){
		$path = $this->check_path($path);

		file_put_contents($path, $content);
		return "ok";
	}

	public function mkdir($name, $path){
		$name = $this->resolve_existent_folder($path, $name);
		$path = $this->check_path($path.$this->sep.$name);
		$this->makedir($path);
		$id = str_replace("\\","/",str_replace($this->top, "", $path));
		return array( "id" => $id, "value" => $name );
	}

	public function rename($source, $target){
		$name_name = $target;
		if(is_dir($this->check_path($source))){
			$name_name = $this->resolve_existent_folder(dirname($source), $target);
		} else {
			$name_name = $this->resolve_existent_file(dirname($source), $target);
		}
		$name = $this->safe_name($name_name);
		$target = $this->check_path(dirname($source).$this->sep.$name_name);
		$source = $this->check_path($source, true, true);

		$this->ren($source, $target, $name);
		$id = str_replace("\\","/",str_replace($this->top, "", $target));
		return array( "id" => $id, "value" =>  $name_name);
	}

	public function cat($path){
		$path = $this->check_path($path, false, true);

		return file_get_contents($path);
	}

	private function resolve_existent_folder($path, $name){
		$filename = $name;
        $full = $this->check_path($path.$this->sep.$name);
        $increment = ''; //start with no suffix

        while(file_exists($full)) {
            $name = $filename . $increment;
            $full = $this->check_path($path.$this->sep.$name);
            $increment++;
        }
        return $name;
    }
	private function resolve_existent_file($path, $name){
		$filename = pathinfo($name, PATHINFO_FILENAME);
        $extension = pathinfo($name, PATHINFO_EXTENSION);
		$full = $this->check_path($path.$this->sep.$name);
        $increment = ''; //start with no suffix

        while(file_exists($full)) {
        	$full = $this->check_path($path.$this->sep.$filename . $increment . '.' . $extension);
        	$name = $filename . $increment . '.' . $extension;
            $increment++;
        }

        return $name;
	}

	public function upload($path, $name, $temp){
		$this->check_path($path, true, false);

		$name = $this->resolve_existent_file($path, $name);

		$full = $this->check_path($path.$this->sep.$name);

		move_uploaded_file($temp, $full);

		$id = str_replace("\\","\\\\",$this->file_id($full)); // Flash upload solution

		$folder = str_replace("\\","/",$this->safe_name($path));
		$file = str_replace("\\","/",$this->safe_name($name));
		$id = str_replace("\\","/",$this->file_id($full));
		return array(
            "folder" => $folder,
            "value"   => $file,
            "id"     => $id,
            "type"   => $this->get_type($name),
            "status" => "server"
        );
	}

	public function download($file){
		$file = $this->check_path($file, false, true);
		return new RealFileInfo($file);
	}

	public function url($path){
		$path = $this->check_path($path, false, true);

		return $this->url.$path;
	}

    protected function sort_search($a, $b){
		$result = $this->sort($a, $b);
		if(!$result){
			$result = $a["parent"] > $b["parent"] ? 1 : ($a["parent"] < $b["parent"] ? -1 : 0);
		}
        return $result;
    }

	public function find($dir, $text){
		$parentId = $dir;
        $dir = $this->check_path($dir, true);
        $this->log("List $dir");

        $data = array();
        $d = dir($dir);
        $folder = str_replace("\\","/",str_replace($this->top, "", $dir));
        while(false != ($entry = $d->read())){
            if ($entry == "." || $entry == "..") continue;

            $file = $d->path.$entry;
            $isdir = is_dir($file);
            $temp = false;


			if(strpos($entry,$text) !== false)
	            $temp = array(
	                "id" => $folder.$entry,
	                "value" => $entry,
	                "type" => $isdir ? "folder" : $this->get_type($entry),
	                "size" => $isdir ? 0 : filesize($file),
	                "date" => filemtime($file),
	                "parent" => $parentId
	            );

            if ($isdir){
                $data = array_merge($data, $this->find($folder.$entry, $text));

            }

            if($temp)
                $data[] = $temp;
        }
        $d->close();

        usort($data, array($this, "sort_search"));

        return $data;
    }
}
?>