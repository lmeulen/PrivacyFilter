# PrivacyFilter
Privacy Filter for free text

See also the following articles: 
- [Remove personal informaton from a text with Python](https://towardsdatascience.com/remove-personal-information-from-text-with-python-232cb69cf074)
- [Remove personal informaton from a text with Python - Part II](https://leo-vander-meulen.medium.com/remove-personal-information-from-a-text-with-python-part-ii-ner-2e6529d409a6)
- [Create a Privacy Filter Web Service with FastAPI and Heroku](https://towardsdatascience.com/create-a-privacy-filter-webservice-with-fastapi-and-heroku-4755ef1ccb25)


This repository implements a privacy filter for text. It removes dates, numbers, names, places, streets, medicines 
and diseases from text. The dataset files are all in Dutch but can be replaced by datasets for other languages.

A PrivacyFilter class is available with limited external dependencies (only FlashText). There is also a secure 
webservice implemented (FreeTextAPI).

There are two type of replacements; first regular expression based, then the forbidden word lists are removed using the
KeywordProcessor (Aho-Corasick algorithm based). The KeywordProcessor is based on 
[FlashText](https://github.com/vi3k6i5/flashtext). The creation of the datastructure is optimised since we are
adding words with a set of follow-up characters (spaces, dots, comma's, etc). In the orignal implementation
the tree is traversed for each addtion, in the optimised version the location of the word is found and from there
th additional characters are added. 

- Regular expression based replacements:
  - URL
  - Email addresses
  - Dates
  - Times
  - Postal codes (Dutch format)
  - Numbers

- Keywords to be replaced ('forbidden words'):
  - Street names
  - Places (cities, regions, etc)
  - First names
  - Last names
  - Medicines
  - Diseases
  - Nationalities
  - Countries

- Named Entity Recognition with Spacy (optional)

Verbs occur as names, streetnames and places. Keyword filters are therefore cleaned from verbs. 
They are removed from the text when the NER sees them as names/streets/places.

## Dependencies
For using the PrivacyFilter class:
- Spacy, including nl_core_news_lg

Make sure to run "python -m spacy download nl_core_news_lg" after installing Spacy if you want
to use the NLP filter. This is not needed when installing dependencies from the requirements.txt with pip.

For using the API:
- FastAPI
- Uvicorn

And for downloading and creating new datafiles
- Osmnx (if pip/conda install fails, download code from GitHub and put in project directory)
- Pandas
- GeoPandas
- Numpy
- BeautifulSoup
- cbsodata

The full dependency list is available in the requirements.txt

## Example usage
~~~~
pfilter = PrivacyFilter()
pfilter.initialize(clean_accents=True, nlp_filter=True, wordlist_filter=False,
                   regular_expressions = True)

pfilter.filter("Het is 12-12-2021.", set_numbers_zero=False, remove_accents=True)

OUTPUT:

Het is <FILTERED>. 
~~~~

The option set_number_zero determines whether numbers are replaced by the tag <NUMBER> or are 
replaced by zeros. Setting the option remove_accents assures all accents are removed before 
executing the filtering.  
The option clean_accents determines if all accents are removed from the text to filter before
filtering. The option nlp_filter determines whether to run the Spacy model. Using this
model increases accuracy but reduces performance.

There is also a set of example texts that can be filtered, both with the wordlist and with NER. It results 
in an HTML file (``results.html``) that compares the original text with the filtered text.
~~~~
python RunExamples.py
~~~~

## Filter Configuration
It is possible to configure the filter from code (see the example above). This way, it is poassible to enable/
disable the different filter parts. The default datasets will be used.

Another possibility is to use a yaml file for configration:
~~~~
pfilter = PrivacyFilter()
pfilter.initialize_from_file(filename='filter.yaml')
~~~~

An example configuration is:
~~~~
clean_accents: True
nlp_filter: True
wordlist_filter: False
regular_expressions: True

data_directory: 'datasets'
firstnames: 'firstnames.csv'
lastnames: 'lastnames.csv'
places: 'places.csv'
streets: 'streets_Nederland.csv'
diseases: 'diseases.csv'
medicines: 'medicines.csv'
nationalities: 'nationalities.csv'
countries: 'countries.csv'
~~~~
The first items specifiy the filters to apply, equal to the configuration from code. Both examples 
initialize the filter in the same way. The second part specifies the data directory and files that 
will be used to initialise the word lists. This example uses the same files as default.

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
without the NLP step and 5 ms with the NLP step. With NLP, initialisation time increases to 11 seconds.

## API

The class PrivacyFilterAPI implements an HTTPS REST service around the PrivacyFilter class. Before 
using the API, a key-pair must be generated using GenerateCertificate.py.

~~~~
python3 PrivacyFilterAPI.py
~~~~

After starting the API, a service is created at https://localhost:8000. The documentation for this 
service is available at https://localhost:8000/docs.

## Running on Heroku

It is possible to run the  filter on Heroku, al required specification files are in place. Do note 
that the free version of Heroku has an application limit of 500MB. To be able to run the filter
on Heroku for free some meausres must be taken to reduce the application size. This can be done
be reducing the file sizes in datasets and/or not loading the NLP part.  On a paid server there is 
sufficient capacity to run the complete server.

See 
[Create a Privacy Filter Web Service with FastAPI and Heroku](https://medium.com/4755ef1ccb25)
for more information.

Enjoy!