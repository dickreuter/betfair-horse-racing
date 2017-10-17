<?php

interface iFileSystem {
	public function virtualRoot($name);
	public function ls($dir, $nested);
	public function rm($file);
	public function cp($source, $target);
	public function mv($source, $target);
	public function mkdir($source, $target);
	public function rename($source, $target);

	public function touch($path);
	public function cat($path);

	public function upload($path, $name, $temp);
	public function url($path);

	public function batch($source, $operation, $target);
}
interface iFileInfo{
	public function getSize();
	public function getName();
	public function getContent();
}


class RealFileInfo implements iFileInfo{
	private $content;
	private $name;

	function __construct($path){
		$this->content = file_get_contents($path);
		$this->name = pathinfo($path, PATHINFO_BASENAME);
		$this->ext = pathinfo($path, PATHINFO_EXTENSION);
		$this->myme = mime_content_type($path);
	}

	public function getName(){
		return $this->name;
	}
	public function getSize(){
		return strlen($this->content);
	}
	public function getContent(){
		return $this->content;
	}
	public function getExtension(){
        return $this->ext;
    }
    public function getBase64(){
        // Format the image SRC:  data:{mime};base64,{data};
        return 'data:'.($this->myme).';base64,'.base64_encode($this->content);
    }
}

?>