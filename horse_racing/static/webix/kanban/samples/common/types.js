webix.type(webix.ui.kanbanlist,{
	name: "icons",
	icons:[
		{ id:"vote", icon:"thumbs-o-up", show: function(obj){ return !!obj.votes }, template:"#votes#"},
		{ id:"comments", icon:"comment-o", show: function(obj){ return !!obj.comments }, template:"#comments.length#"},
		{ id:"edit", icon:"edit"}
	]
});
webix.type(webix.ui.kanbanlist,{
	name: "avatars",
	icons:[
		{icon: "comment" , show: function(obj){ return !!obj.comments }, template:"#comments.length#"},
		{icon: "pencil"}
	],
	templateAvatar: function(obj){
		if(obj.personId){
			var name = "";
			for(var i=0; i < staff.length && !name;i++){
				if(staff[i].id == obj.personId){
					name = staff[i].name;
				}
			}
			return '<img class="avatar" src="../common/imgs/'+obj.personId+'.jpg" title="'+name+'"/>';
		}
		return "";
	}
});
webix.type(webix.ui.kanbanlist,{
	name: "users",
	icons:[
		{icon: "comment" , show: function(obj){ return !!obj.comments }, template:"#comments.length#"},
		{icon: "pencil-square-o"}
	],
	templateAvatar: function(obj){
		if(obj.user){
			return '<img class="avatar" src="../common/photos/'+obj.user+'.png" title="'+name+'"/>';
		}
		return "";
	}
});

webix.type(webix.ui.dataview,{
	name: "avatars",
	width: 80,
	height: 80,
	template: function(obj){
		var name = obj.name.split(" ");
		return '<img class="large_avatar" src="../common/imgs/'+obj.id+'.jpg" title="'+obj.name+'"/><div class="name">'+name[0]+'</div>'
	}
});
