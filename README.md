# PrivacyFilter
Privacy Filter for free text

This repository implements a privacy filter for text. It removes dates, numbers, names, places, streets, medicines and diseases from text. The dataset 
files are all in Dutch but can be replaced by datasets for other languages.

## Dependencies
- FlashText

And for downloading and creating new datafiles
- Osmnx
- Pandas
- GeoPandas
- Numpy
- BeautifoulSoup
- cbsodata

## Example usage
~~~~
pfilter = PrivacyFilter()
pfilter.initialize()

pfilter.filter("Het is 12-12-2021.", set_numbers_zero=False)

OUTPUT:

Het is <DATUM>. 
~~~~

## Updating datasets

The script DataUpdater.py updates the datasets. The following sources are used:
- Names: https://www.naamkunde.net
- Places: https://www.cbs.nl, dataset 84992
- Streets: Open Streepmap 
- Diseases: https://nl.wikibooks.org/wiki/Geneeskunde/Lijst_van_aandoeningen
- Medicines: https://www.ema.europa.eu/sites/default/files/Medicines_output_referrals.xlsx

A new resource for medicines is 
Enjoy!