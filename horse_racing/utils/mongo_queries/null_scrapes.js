db.price_scrape.aggregate(

	// Pipeline
	[
		// Stage 1
		{
			$match: {"LTP":null, "countrycode":"GB", "seconds_until_start": {"$lt":500
			}}
		},

		// Stage 2
		{
			$group: {
			"_id":"$marketid",
			"amount": {"$sum": 1}
			}
		},

	]

	// Created with Studio 3T, the IDE for MongoDB - https://studio3t.com/

);
