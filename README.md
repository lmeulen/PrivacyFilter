# PrivacyFilter
Privacy Filter for free text

This repository implements a privacy filter for text. It removes dates, numbers, names, places, streets, medicines 
and diseases from text. The dataset files are all in Dutch but can be replaced by datasets for other languages.

A PrivacyFilter class is available with limited external dependencies (only FlashText). There is also a secure webservice
implemented (FreeTextAPI).

There are two type of replacements; first regular expression based, then the forbidden word lists are removed using the
FlashText KeywordProcessor is used (Aho-Corasick algorithm based).

Regular expression based replacements:
- URL
- Email addresses
- Dates
- Postal codes (Dutch format)
- Numbers

Keywords to be replaced ('forbidden words'):
- Street names
- Places (cities, regions, etc)
- First names
- Last names
- Medicines
- Diseases
- Nationalities
- Countries

Named Entity REcognition with Spacy (optional)

## Dependencies
For using the PrivacyFilter class:
- FlashText
- Spacy, inclusief nl_core_news_lg 

Make sure to run "python -m spacy download nl_core_news_lg" after installing Spacy if you want
to use the NLP filter.

For using the API:
- FastAPI
- Uvicorn

And for downloading and creating new datafiles
- Osmnx (if pip/conda install fails, download code from github and put in proejct directory)
- Pandas
- GeoPandas
- Numpy
- BeautifoulSoup
- cbsodata

## Example usage
~~~~
pfilter = PrivacyFilter()
pfilter.initialize(clean_accents=True, nlp_filter=True)

pfilter.filter("Het is 12-12-2021.", set_numbers_zero=False, remove_accents=True)

OUTPUT:

Het is <DATUM>. 
~~~~

The option set_number_zero determines whether numbers are replaced by the tag <NUMBER> or are 
replaced by zeros. Setting the option remove_accents assures all accents are removed before 
executing the filtering.  
The option clean_accents determines if all accents are removed from the text to filter before
filtering. The option nlp_filter determines whether or not to run the Spacy model. Using this
model increases accuracy but reduces performance.

## Updating datasets

The script DataUpdater.py updates the datasets. The following sources are used:
- Names: https://www.naamkunde.net
- Places: https://www.cbs.nl, dataset 84992
- Streets: Open Street Map (python package osmnx) 
- Diseases: https://nl.wikibooks.org/wiki/Geneeskunde/Lijst_van_aandoeningen
- Medicines: https://www.apotheek.nl/zoeken?
- Nationalities: https://www.cbs.nl, dataset 03743
- Countries: https://nl.wikipedia.org/wiki/Lijst_van_landen_in_2020

## Performance

The initialisation of the PrivacyFilter is expensive, it takes almost 3 seconds on my computer 
(Intel i5-1035G7, 8GB, SSD).

Parsing a sentence and replacing privacy related information is fast, It takes approx 0.5 ms 
without the NLP step and 20 ms with the NLP step. With NLP, initialisation time increases to 11 seconds.

## API

The class PrivacyFilterAPI implements a HTTPS REST service around the PrivacyFilter class. Before 
using the API, a key-pair must be generated using GenerateCertificate.py.

~~~~
python3 PrivacyFilterAPI
~~~~

After starting the API, a service is created at https://localhost:8000. The documentation for this 
service is available at https://localhost:8000/docs.

Enjoy!