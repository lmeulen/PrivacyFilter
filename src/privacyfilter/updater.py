import re
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
from pathlib import Path
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DATA_DIRECTORY = Path(__file__).with_name("data")
DOWNLOAD_DIRECTORY = Path("data-cache")
HTTP_TIMEOUT = (5, 30)
HTTP_RETRY = Retry(
    total=3,
    backoff_factor=0.5,
    status_forcelist=(429, 500, 502, 503, 504),
    allowed_methods=("GET",),
)
HTTP_SESSION = requests.Session()
HTTP_SESSION.mount("https://", HTTPAdapter(max_retries=HTTP_RETRY))
HTTP_SESSION.headers.update({"User-Agent": "PrivacyFilter dataset updater"})

verbs = []


def get_response(url):
    try:
        response = HTTP_SESSION.get(url, timeout=HTTP_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as error:
        raise RuntimeError(f"Could not download {url}: {error}") from error
    return response


def get_soup(url):
    return BeautifulSoup(get_response(url).text, "lxml")


def download_file(url, destination):
    response = get_response(url)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(response.content)


def require_element(element, description, url):
    if element is None:
        raise ValueError(f"Could not parse {description} from {url}; source layout may have changed")
    return element


def remove_accents(text):
    text = unicodedata.normalize('NFD', str(text)).encode('ascii', 'ignore')
    return str(text.decode("utf-8"))


def filter_and_save(df, column, filename, min_length=1, filter_verbs=True):
    if column not in df.columns:
        raise ValueError(f"Cannot create {filename}: missing required column {column!r}")
    if df[column].dropna().empty:
        raise ValueError(f"Cannot create {filename}: column {column!r} has no values")

    df = df.dropna(subset=[column]).copy()
    df[column] = df[column].astype(str)
    df = df[df[column].str.len() > min_length].drop_duplicates().copy()
    df[column] = df[column].map(remove_accents)
    if filter_verbs:
        df = df[~df[column].isin(verbs)]
    df = df.sort_values(column)
    if df.empty:
        raise ValueError(f"Cannot create {filename}: no values remain after filtering")
    DATA_DIRECTORY.mkdir(exist_ok=True)
    df.to_csv(DATA_DIRECTORY / filename, index=False)


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
                soup = get_soup(url)
                div = require_element(
                    soup.find("div", {"style": "clear:both;"}), "verb results", url
                )
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
        DATA_DIRECTORY.mkdir(exist_ok=True)
        verbs.to_csv(DATA_DIRECTORY / 'werkwoorden.csv', index=False)
    else:
        verbs = pd.read_csv(DATA_DIRECTORY / 'werkwoorden.csv')
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
            gdf_edges = ox.graph_to_gdfs(graph, nodes=False)
            names = gdf_edges[['name']].reset_index().drop(columns={'u', 'v', 'key'})
            names.name = names.name.astype('str')
            names = names.drop_duplicates()
            names = names[~names.name.str.contains(r'\[')]
            raw_streets_directory = DOWNLOAD_DIRECTORY / 'RAW_streets'
            raw_streets_directory.mkdir(parents=True, exist_ok=True)
            names.to_csv(raw_streets_directory / ('streets_' + name + '.csv'), index=False)
    lst = []
    for name in ['Gelderland', 'Overijssel', 'Drenthe', 'Groningen', 'Friesland', 'Zeeland', 'Utrecht',
                 'Limburg', 'Noord-Holland', 'Zuid-Holland', 'Flevoland', 'Noord-Brabant']:
        lst.append(pd.read_csv(DOWNLOAD_DIRECTORY / 'RAW_streets' / ('streets_' + name + '.csv')))
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
    url = "https://www.naamkunde.net/?page_id=293&vt_download_xml=true"
    firstnames_file = DOWNLOAD_DIRECTORY / "RAW_names" / "firstnames.xml"
    download_file(url, firstnames_file)
    try:
        xtree = ElementTree.parse(firstnames_file)
    except ElementTree.ParseError as error:
        raise ValueError(f"Could not parse first-name XML from {url}") from error
    xroot = xtree.getroot()
    firstnames = []
    for node in xroot:
        voornaam = node.find("voornaam")
        if voornaam is not None and voornaam.text:
            firstnames.append({"voornaam": voornaam.text})
    if not firstnames:
        raise ValueError(f"Could not parse first names from {url}; no <voornaam> values found")
    firstnames = pd.DataFrame(firstnames)
    filter_and_save(firstnames, 'voornaam', filename='firstnames.csv', min_length=1, filter_verbs=True)


def update_lastnames():
    #
    # Download last names
    #
    url = "https://www.naamkunde.net/wp-content/uploads/oudedocumenten/fn10k_versie1.zip"
    lastnames_file = DOWNLOAD_DIRECTORY / "RAW_names" / "lastnames.zip"
    download_file(url, lastnames_file)
    try:
        with zipfile.ZipFile(lastnames_file, "r") as archive:
            with archive.open("fn_10kw.xml") as xml_file:
                xtree = ElementTree.parse(xml_file)
    except (KeyError, zipfile.BadZipFile, ElementTree.ParseError) as error:
        raise ValueError(f"Could not parse last-name archive from {url}") from error
    xroot = xtree.getroot()
    lastnames = []
    for node in xroot:
        lastname = node.find("naam")
        prefix = node.find("prefix")
        if lastname is not None and lastname.text:
            if prefix is not None and prefix.text:
                lastnames.append({"achternaam": prefix.text + " " + lastname.text})
            else:
                lastnames.append({"achternaam": lastname.text})
    if not lastnames:
        raise ValueError(f"Could not parse last names from {url}; no <naam> values found")
    lastnames = pd.DataFrame(lastnames)
    filter_and_save(lastnames, 'achternaam', filename='lastnames.csv', min_length=1, filter_verbs=True)


def update_diseases():
    #
    # Download diseases
    #
    url = 'https://nl.wikibooks.org/wiki/Geneeskunde/Lijst_van_aandoeningen'
    soup = get_soup(url)
    div = require_element(soup.find(id="mw-content-text"), "disease list", url)
    diseases = [tag.text for tag in div.find_all("li") if tag.text.strip()]
    if not diseases:
        raise ValueError(f"Could not parse diseases from {url}; no list items found")
    diseases.extend(['Corona', 'Covid', 'Covid-19'])
    diseases = pd.DataFrame(diseases, columns=['aandoening'])
    filter_and_save(diseases, 'aandoening', filename='diseases.csv', min_length=1, filter_verbs=False)


def update_medicines():
    #
    # Download medicines
    #
    lst = []
    for ltr in ['u', 'e', 'o', 'a']:
        url = 'https://www.apotheek.nl/zoeken?q=' + ltr + '&filter=medicijnen'
        soup = get_soup(url)
        result_element = require_element(
            soup.find("p", {"class": "searchIndication_text__2l4pd"}), "medicine result count", url
        ).find("span")
        result_element = require_element(result_element, "medicine result count", url)
        try:
            results = int(result_element.text)
        except ValueError as error:
            raise ValueError(f"Could not parse medicine result count from {url}") from error
        count = 0
        while count < results:
            for med in soup.find_all("div", {"class": "searchItem_resultTitle__2TXzJ"}):
                lst.append(med.text)
            url = 'https://www.apotheek.nl/zoeken?q=u&filter=medicijnen&start=' + str(count + 10)
            soup = get_soup(url)
            count += 10
    if not lst:
        raise ValueError("Could not parse medicines; no result titles found")
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
    soup = get_soup(url)
    tbls = soup.find_all("table", {"class": "wikitable"})
    if not tbls:
        raise ValueError(f"Could not parse country tables from {url}; no wikitable elements found")
    lst = []
    for tbl in tbls:
        rows = tbl.find_all("tr")
        for row in rows:
            cells = row.find_all("td")
            if len(cells) == 4:
                naam = cells[0].text.strip()
                naam = re.sub(r"\[.*", "", naam)
                lst.append(naam)
                naam = cells[1].text.strip()
                naam = re.sub(r"\(.*", "", naam)
                lst.append(naam)
                language = cells[3].text.strip().split(":", maxsplit=1)
                if len(language) == 2:
                    lst.append(language[1].split('/')[0].strip())
    if not lst:
        raise ValueError(f"Could not parse countries from {url}; no country rows found")
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
