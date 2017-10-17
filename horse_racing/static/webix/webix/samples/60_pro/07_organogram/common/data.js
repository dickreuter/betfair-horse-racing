chart_data = [
	{id:"root", value:"Board of Directors",  data:[
		{ id:"1", value:"Managing Director", data:[
			{id:"1.1", value:"Base Manager", data:[
				{ id:"1.1.1", value:"Store Manager" },
				{ id:"1.1.2", value:"Office Assistant", data:[
					{ id:"1.1.2.1", value:"Dispatcher", data:[
						{ id:"1.1.2.1.1", value:"Drivers" }
					] }

				] },
				{ id:"1.1.3", value:"Security" }
			]},
			{ id:"1.2", value:"Business Development Manager", data:[
				{ id:"1.2.1", value:"Marketing Executive" }
			]},
			{ id:"1.3", value:"Finance Manager", data:[
				{ id:"1.3.1", value:"Accountant", data:[
					{ id:"1.3.1.1", value:"Accounts Officer" }
				] }
			] },
			{ id:"1.4", value:"Project Manager", data:[
				{ id:"1.4.1", value:"Supervisors",data:[
					{ id:"1.4.1.1", value:"Foremen"}
				]}
			] }
		]}
	]}
];
chart_data_style = [
	{id:"root", value:"Board of Directors", $css: "top",  data:[
		{ id:"1", value:"Managing Director", $css:{background: "#ffe0b2", "border-color": "#ffcc80"}, data:[
			{id:"1.1", value:"Base Manager", data:[
				{ id:"1.1.1", value:"Store Manager" },
				{ id:"1.1.2", value:"Office Assistant", data:[
					{ id:"1.1.2.1", value:"Dispatcher", data:[
						{ id:"1.1.2.1.1", value:"Drivers" }
					] }

				] },
				{ id:"1.1.3", value:"Security" }
			]},
			{ id:"1.2", value:"Business Development Manager", data:[
				{ id:"1.2.1", value:"Marketing Executive" }
			]},
			{ id:"1.3", value:"Finance Manager", data:[
				{ id:"1.3.1", value:"Accountant", data:[
					{ id:"1.3.1.1", value:"Accounts Officer" }
				] }
			] },
			{ id:"1.4", value:"Project Manager", data:[
				{ id:"1.4.1", value:"Supervisors",data:[
					{ id:"1.4.1.1", value:"Foremen"}
				]}
			] }
		]}
	]}
];