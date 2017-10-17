# Betfair horse racing

##
The code consists of the follwoing parts
* Collecting data from betfair and matchbook (below cronjobs need to run)
* Analyzing the pricing data of horse racing through neural networks and creating a model to make betting recommandations for backing or laying
* Executing bets according to the trained model
* Flask web interface that shows logging activity, graphical pnl overview and statistical analysis of past bets

## Building the venv
You can create a venv with the environment.yml file as follows:

* Download anaconda 64 python 3
* conda create env -f environment.yml -n horse_racing (or simply run update_venv.bat). On Linux you need to use conda env create -f environment.yml
* The env will be in anaconda/envs/horse_racing

## Commands

The application is controlled over app.py. The pnl overview web server is launched over webserver.py (but better use webserver.wsgi).
```
Usage:
  app.py ts train STRATEGY CLASS COUNTRYCODES [--batchsize=<>] [--from_year=<>] [--to_year=<>] [--localhost]
  app.py ts backtest STRATEGY CLASS COUNTRYCODES [MODEL_PATH] [--from_year=<>] [--to_year=<>] [--localhost]
  app.py collect_prices
  app.py bet [--armed] [--sandbox_key] [--config=<>]
  app.py update_unfilled_orders [--armed] [--config=<>]
  app.py collect_results
  app.py evaluate_pnl [--overwrite_calculated_pnls] [--config=<>]
  app.py email_summary
  app.py upload_tarball FILE [DESTINATION]
  app.py map_reduce SOURCE DESTINATION CLASS [--localhost] [--use_archive]
  app.py propagate_race_results_to_price_scrape

Exmaple
  app.py ts backtest lay FlyingSpiderBookie GB,IE --from_year 2018 --to_year 2018`
  app.py ts train lay FlyingSpider GB,IE,US,NZ --localhost --from_year 2015 --to_year 2017
  app.py ts backtest lay FlyingSpider GB,IE,US,NZ --localhost --from_year 2016 --to_year 2016
  app.py propagate_race_results_to_price_scrape   adds a winner and losers column to each price in price_scrape
  app.py map_reduce price_scrape price_scrape_enriched DEBookies --localhost
```


```
Cronjobs that need to be set up:
    * * * * * sh app.sh collect_prices
    * * * * * sh app.sh bet
    * * * * * sh app.sh update_unfilled_orders --armed
    5 * * * * sh app.sh collect_results
    6 * * * * sh app.sh evaluate_pnl
    7 22 * * * sh app.sh email_summary
    9 4 * * * sh app.sh propagate_race_results_to_price_scrape
    5 5 * * * sh app.sh map_reduce price_scrape price_scrape_enriched_bookies DEBookies
```


## Database
All data is collected onto a mongodb server which can be set up over config.ini.

## Example plots of neural network training:

![](/doc/chart_cumulative_year.png?raw=True)
![](/doc/chart_cumulative.png?raw=True)
![](/doc/chart.png?raw=True)
![](/horse_racing/neural_networks/plots/backtesting-20180323-222855.png?raw=True)
![](/horse_racing/neural_networks/plots/training-20180318-164301.png?raw=True)
![](/horse_racing/neural_networks/plots/training-20180318-184839.png?raw=True)
![](/horse_racing/neural_networks/plots/training-20180321-003043.png?raw=True)
![](/horse_racing/neural_networks/plots/training-20180426-150117.png?raw=True)
![](/horse_racing/neural_networks/plots/training-20180508-224228.png?raw=True)
![](/horse_racing/neural_networks/plots/training-20180508-224741.png?raw=True)