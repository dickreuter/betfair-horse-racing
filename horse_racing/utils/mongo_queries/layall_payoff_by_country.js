db.price_scrape_enriched.aggregate(

	// Pipeline
	[
		// Stage 1
		{
			$group: {
			"_id": "$countrycode",
			"lay": {"$avg": "$lay"}
			
			}
		},

	]

	// Created with Studio 3T, the IDE for MongoDB - https://studio3t.com/

);
