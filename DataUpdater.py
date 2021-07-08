import re
import urllib
import xml.etree.ElementTree as ElementTree
import zipfile
import cbsodata
import numpy as np
import osmnx as ox
import pandas as pd
import requests
import unicodedata
from bs4 import BeautifulSoup
from os.path import join


def remove_accents(text):
    text = unicodedata.normalize('NFD', str(text)).encode('ascii', 'ignore')
    return str(text.decode("utf-8"))


def update_streetnames(download=True, min_length=6):
    #
    # Download streetnames per province, and combine to the total set of streetnames
    #
    # TODO: Utrecht and Groningen downloads are city only, need bounded box
    if download:
        for name in ['Gelderland', 'Overijssel', 'Drenthe', 'Groningen', 'Friesland', 'Zeeland', 'Utrecht',
                     'Limburg', 'Noord-Holland', 'Zuid-Holland', 'Flevoland', 'Noord-Brabant']:
            print(name)
            graph = ox.graph_from_place(name + ", Netherlands", network_type="drive")
            gdf_nodes, gdf_edges = ox.graph_to_gdfs(graph)
            names = gdf_edges[['name']].reset_index().drop(columns={'u', 'v', 'key'})
            names.name = names.name.astype('str')
            names = names.drop_duplicates()
            names = names[~names.name.str.contains('\[')]
            names.to_csv(join('datasets', 'RAW_streets', 'streets_' + name + '.csv'), index=False)
    lst = []
    for name in ['Gelderland', 'Overijssel', 'Drenthe', 'Groningen', 'Friesland', 'Zeeland', 'Utrecht',
                 'Limburg', 'Noord-Holland', 'Zuid-Holland', 'Flevoland', 'Noord-Brabant']:
        lst.append(pd.read_csv(join('datasets', 'RAW_streets', 'streets_' + name + '.csv')))
    streetnames = pd.concat(lst, axis=0, ignore_index=True).drop_duplicates()
    streetnames = streetnames[streetnames.name.str.len() >= min_length]
    streetnames.name = streetnames.apply(lambda x: remove_accents(x.name), axis=1)
    streetnames.to_csv(join('datasets', 'streets_Nederland.csv'), index=False)


def update_places(min_length=4):
    #
    # Download places and regions from CBS
    #
    total = pd.DataFrame(cbsodata.get_data('84992NED'))
    places = np.append(
        np.append(np.append(total.Woonplaatsen.values, total.Naam_2.values), total.Naam_4.values), total.Naam_6.values)
    places = pd.DataFrame(places, columns=['plaatsnaam']).drop_duplicates()
    places = places[places.plaatsnaam.str.len() >= min_length]
    places.plaatsnaam = places.apply(lambda x: remove_accents(x.plaatsnaam), axis=1)
    places.to_csv(join("datasets", "places.csv"), index=False)


def update_firstnames():
    #
    # Download first names
    #
    url = "http://www.naamkunde.net/?page_id=293&vt_download_xml=true"
    urllib.request.urlretrieve(url, join("datasets", "RAW_names", "firstnames.xml"))
    xtree = ElementTree.parse(join("datasets", "RAW_names", "firstnames.xml"))
    xroot = xtree.getroot()
    firstnames = []
    for node in xroot:
        voornaam = node.find("voornaam")
        if voornaam is not None:
            firstnames.append({"voornaam": voornaam.text})
    firstnames = pd.DataFrame(firstnames).drop_duplicates()
    firstnames.voornaam = firstnames.apply(lambda x: remove_accents(x.voornaam), axis=1)
    firstnames.to_csv(join("datasets", "firstnames.csv"), index=False)


def update_lastnames():
    #
    # Download last names
    #
    url = "http://www.naamkunde.net/wp-content/uploads/oudedocumenten/fn10k_versie1.zip"
    urllib.request.urlretrieve(url, join("datasets", "RAW_names", "lastnames.zip"))
    zf = zipfile.ZipFile(join("datasets", "RAW_names", "lastnames.zip"), 'r')
    f = zf.open("fn_10kw.xml")
    xtree = ElementTree.parse(f)
    xroot = xtree.getroot()
    lastnames = []
    for node in xroot:
        lastname = node.find("naam")
        prefix = node.find("prefix")
        if lastname is not None:
            if prefix.text is not None:
                lastnames.append({"achternaam": prefix.text + " " + lastname.text})
            else:
                lastnames.append({"achternaam": lastname.text})
    lastnames = pd.DataFrame(lastnames).drop_duplicates()
    lastnames.achternaam = lastnames.apply(lambda x: remove_accents(x.achternaam), axis=1)
    lastnames.to_csv(join("datasets", "lastnames.csv"), index=False)


def update_diseases():
    #
    # Download diseases
    #
    url = 'https://nl.wikibooks.org/wiki/Geneeskunde/Lijst_van_aandoeningen'
    reqs = requests.get(url)
    soup = BeautifulSoup(reqs.text, 'lxml')
    div = soup.find(id="mw-content-text")
    diseases = []
    for tag in div.find_all("li"):
        diseases.append(tag.text)
    diseases = pd.DataFrame(diseases, columns=['aandoening'])
    diseases.aandoening = diseases.apply(lambda x: remove_accents(x.aandoening), axis=1)
    diseases.to_csv(join("datasets", "diseases.csv"), index=False)


def update_medicines():
    #
    # Download medicines
    #
    lst = []
    for ltr in ['u', 'e', 'o', 'a']:
        url = 'https://www.apotheek.nl/zoeken?q=' + ltr + '&filter=medicijnen'
        reqs = requests.get(url)
        soup = BeautifulSoup(reqs.text, 'lxml')
        div = soup.find_all("p", {"class": "searchIndication_text__2l4pd"})

        results = int(div[0].find('span').text)
        count = 0
        while count < results:
            for med in soup.find_all("div", {"class": "searchItem_resultTitle__2TXzJ"}):
                lst.append(med.text)
            url = 'https://www.apotheek.nl/zoeken?q=u&filter=medicijnen&start=' + str(count + 10)
            reqs = requests.get(url)
            soup = BeautifulSoup(reqs.text, 'lxml')
            count += 10
    medicines = pd.DataFrame(lst, columns=['original'])
    medicines['lengte'] = medicines['original'].str.len()
    medicines = medicines.sort_values('lengte')
    new = medicines["original"].str.replace('De Tuinen ', '').str.replace('/', ' ').str.replace(',', ' ') \
        .str.replace('(', ' ').str.split(" ", n=1, expand=True)
    medicines['medicijn'] = new[0].str.title()
    medicines = medicines[['medicijn']].sort_values('medicijn').drop_duplicates()
    medicines.medicijn = medicines.apply(lambda x: remove_accents(x.medicijn), axis=1)
    medicines.to_csv(join("datasets", "medicines.csv"), index=False)


def update_nationalities():
    #
    # Download nationalitites
    #
    total = pd.DataFrame(cbsodata.get_data('03743'))
    nationalities = pd.DataFrame(total.Nationaliteiten.unique()[1:-1], columns=['nationaliteit']).drop_duplicates()
    nationalities.nationaliteit = nationalities.apply(lambda x: remove_accents(x.nationaliteit), axis=1)
    nationalities.to_csv(join("datasets", "nationalities.csv"), index=False)


def update_countries():
    #
    # Download countries
    #
    url = 'https://nl.wikipedia.org/wiki/Lijst_van_landen_in_2020'
    print(url)
    reqs = requests.get(url)
    soup = BeautifulSoup(reqs.text, 'lxml')
    tbls = soup.find_all("table", {"class": "wikitable"})
    lst = []
    for tbl in tbls:
        rows = tbl.find_all("tr")
        for row in rows:
            cells = row.find_all("td")
            if len(cells) == 4:
                naam = cells[0].text.strip()
                naam = re.sub("\[.*", "", naam)
                lst.append(naam)
                naam = cells[1].text.strip()
                naam = re.sub("\(.*", "", naam)
                lst.append(naam)
                lst.append(cells[3].text.strip().split(":")[1].split('/')[0].strip())
    countries = pd.DataFrame(lst, columns=['land']).drop_duplicates()
    countries.land = countries.apply(lambda x: remove_accents(x.land), axis=1)
    countries.to_csv(join("datasets", "countries.csv"), index=False)


def update_datasets():
    update_streetnames(download=False, min_length=6)
    update_places(min_length=4)
    update_firstnames()
    update_lastnames()
    update_diseases()
    update_medicines()
    update_nationalities()
    update_countries()


if __name__ == "__main__":
    update_datasets()
