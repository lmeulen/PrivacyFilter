# PrivacyFilter
Privacy Filter for free text

This repository implements a privacy filter for text. It removes dates, numbers, names, places, streets, medicines and diseases from text. The dataset 
files are all in Dutch but can be replaced by datasets for other languages.

## Dependencies
- FlashText
- Osmnx

## Example usage
~~~~
pfilter = PrivacyFilter()
pfilter.initialize()

pfilter.filter("Het is 12-12-2021.", set_numbers_zero=False)

OUTPUT:

Het is <DATUM>. 
~~~~

Enjoy!