db.price_scrape_enriched.aggregate(

	// Pipeline
	[
		// Stage 1
		{
			$bucket: {
			   "groupBy": "$marketstarttime",
			   
			                    "boundaries": [new Date (2015-1-1), new Date (2016-1-1), new Date (2017-1-1), new Date(2018-1-1), new Date(2019-1-1)],
			                    
			                    "default": "other",
			                    "output": {
			                        "avg_ltp": {"$avg": "$lay"}
			                    }
			                    
			
			}
		},

	]

	// Created with Studio 3T, the IDE for MongoDB - https://studio3t.com/

);
