db.price_scrape.aggregate(

	// Pipeline
	[
		// Stage 1
		{
			$match: {"bookies": {"$exists":"true"}}
		},

		// Stage 2
		{
			$unwind: "$bookies"
		},

		// Stage 3
		{
			$project: {"bookies_value": "$bookies.price","bookies_name": "$bookies.name",
			  "LTP":1, "back_prices0":1, "lay_prices0":1, "median_bookie_price":1,"seconds_until_start":1,
			  "mean_bookie_price":1,"diff":{"$subtract":["$lay_prices0","$bookies.price"]}}
		},

		// Stage 4
		{
			$match: {"diff":{"$lt":0},
			"bookies_name":"Matchbook"}
		},

	]

	// Created with Studio 3T, the IDE for MongoDB - https://studio3t.com/

);
