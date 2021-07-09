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
import string
from bs4 import BeautifulSoup
from os.path import join

verbs = []


def remove_accents(text):
    text = unicodedata.normalize('NFD', str(text)).encode('ascii', 'ignore')
    return str(text.decode("utf-8"))


def filter_and_save(df, column, filename, min_length=1, filter_verbs=True):
    df = df[df[column].str.len() > min_length].drop_duplicates()
    df[column] = df.apply(lambda x: remove_accents(x[column]), axis=1)
    if filter_verbs:
        df = df[~df[column].isin(verbs)]
    df = df.sort_values(column)
    df.to_csv(join('datasets', filename), index=False)


def update_werkwoorden(download=True, min_length=3):
    global verbs
    if download:
        lst = []
        for ltr in list(string.ascii_uppercase):
            parse_next_page = True
            page = 1
            while parse_next_page:
                url = 'https://www.mijnwoordenboek.nl/werkwoorden/NL/' + ltr + '/' + str(page)
                print(url)
                reqs = requests.get(url)
                soup = BeautifulSoup(reqs.text, 'lxml')
                div = soup.find_all("div", {"style": "clear:both;"})[0]
                cnt = 0
                for u in div.find_all("a"):
                    cnt += 1
                    lst.append(u.text)
                print(cnt)
                parse_next_page = (cnt > 230)
                page += 1

        verbs = pd.DataFrame(lst, columns=['werkwoord'])
        verbs = verbs[verbs.werkwoord.str.len() >= min_length].drop_duplicates()
        verbs = verbs.sort_values('werkwoord')
        verbs = verbs.iloc[2:].reset_index()
        verbs = verbs[['werkwoord']]
        verbs.werkwoord = verbs.werkwoord.str.title()
        verbs.to_csv(join('datasets', 'werkwoorden.csv'), index=False)
    else:
        verbs = pd.read_csv(join('datasets', 'werkwoorden.csv'))
    verbs = verbs.werkwoord.values


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
    streetnames = pd.concat(lst, axis=0, ignore_index=True)
    streetnames.columns = ['straatnaam']
    filter_and_save(streetnames, 'straatnaam', 'streets_Nederland.csv', min_length=min_length, filter_verbs=True)


def update_places(min_length=4):
    #
    # Download places and regions from CBS
    #
    total = pd.DataFrame(cbsodata.get_data('84992NED'))
    places = np.append(
        np.append(np.append(total.Woonplaatsen.values, total.Naam_2.values), total.Naam_4.values), total.Naam_6.values)
    places = pd.DataFrame(places, columns=['plaatsnaam'])
    filter_and_save(places, 'plaatsnaam', filename='places.csv', min_length=min_length, filter_verbs=True)


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
    firstnames = pd.DataFrame(firstnames)
    filter_and_save(firstnames, 'voornaam', filename='firstnames.csv', min_length=1, filter_verbs=True)


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
    lastnames = pd.DataFrame(lastnames)
    filter_and_save(lastnames, 'achternaam', filename='lastnames.csv', min_length=1, filter_verbs=True)


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
    for d in ['Corona', 'Covid', 'Covid-19']:
        diseases.append(d)
    diseases = pd.DataFrame(diseases, columns=['aandoening'])
    filter_and_save(diseases, 'aandoening', filename='diseases.csv', min_length=1, filter_verbs=False)


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

    filter_and_save(medicines, 'medicijn', filename='medicines.csv', min_length=1, filter_verbs=False)


def update_nationalities():
    #
    # Download nationalitites
    #
    total = pd.DataFrame(cbsodata.get_data('03743'))
    nationalities = pd.DataFrame(total.Nationaliteiten.unique()[1:-1], columns=['nationaliteit'])
    filter_and_save(nationalities, 'nationaliteit', filename='nationalities.csv', min_length=1, filter_verbs=False)


def update_countries():
    #
    # Download countries
    #
    url = 'https://nl.wikipedia.org/wiki/Lijst_van_landen_in_2020'
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
    countries = pd.DataFrame(lst, columns=['land'])
    filter_and_save(countries, 'land', filename='countries.csv', min_length=1, filter_verbs=False)


def update_datasets():
    print('Verbs...')
    update_werkwoorden(download=False)
    print('Streets...')
    update_streetnames(download=False, min_length=6)
    print('Places...')
    update_places(min_length=4)
    print('First names...')
    update_firstnames()
    print('Last names...')
    update_lastnames()
    print('Diseases...')
    update_diseases()
    print('Medicines...')
    update_medicines()
    print('Nationalities...')
    update_nationalities()
    print('Countries...')
    update_countries()
    print('Done')


if __name__ == "__main__":
    update_datasets()
