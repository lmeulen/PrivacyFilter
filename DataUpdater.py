import requests
import urllib
import zipfile
import re
import cbsodata
import osmnx as ox
import pandas as pd
import geopandas as gpd
import numpy as np
import xml.etree.ElementTree as ElementTree
from bs4 import BeautifulSoup

if __name__ == "__main__":

    #
    # Download streetnames per province, and combine to the total set of streetnames
    #
    # TODO: Utrecht and Groningen downloads are city only, need bounded box
    for name in ['Gelderland', 'Overijssel', 'Drenthe', 'Groningen', 'Friesland', 'Zeeland', 'Utrecht',
                 'Limburg', 'Noord-Holland', 'Zuid-Holland', 'Flevoland', 'Noord-Brabant']:
        print(name)
        G = ox.graph_from_place(name + ", Netherlands", network_type="drive")
        gdf_nodes, gdf_edges = ox.graph_to_gdfs(G)
        names = gdf_edges[['name']].reset_index().drop(columns={'u', 'v', 'key'})
        names.name = names.name.astype('str')
        names = names.drop_duplicates()
        names = names[~names.name.str.contains('\[')]
        names.to_csv('datasets\\RAW_streets\\streets_' + name + '.csv', index=False)

    lst = []
    for name in ['Gelderland', 'Overijssel', 'Drenthe', 'Groningen', 'Friesland', 'Zeeland', 'Utrecht',
                 'Limburg', 'Noord-Holland', 'Zuid-Holland', 'Flevoland', 'Noord-Brabant']:
        lst.append(pd.read_csv('datasets\\RAW_streets\\streets_' + name + '.csv'))
    streetnames = pd.concat(lst, axis=0, ignore_index=True).drop_duplicates()
    streetnames = streetnames[streetnames.name.str.len() > 5]
    streetnames.to_csv('datasets\\streets_Nederland.csv', index=False)

    #
    # Download places and regions from CBS
    #
    total = pd.DataFrame(cbsodata.get_data('84992NED'))
    places = np.append(
        np.append(np.append(total.Woonplaatsen.values, total.Naam_2.values), total.Naam_4.values), total.Naam_6.values)
    places = pd.DataFrame(places, columns=['plaatsnaam']).drop_duplicates()
    places.to_csv("datasets\\places.csv", index=False)

    #
    # Download first names
    #
    url = "http://www.naamkunde.net/?page_id=293&vt_download_xml=true"
    urllib.request.urlretrieve(url, "datasets\\RAW_names\\firstnames.xml")
    xtree = ElementTree.parse("datasets\\RAW_names\\firstnames.xml")
    xroot = xtree.getroot()
    firstnames = []
    for node in xroot:
        voornaam = node.find("voornaam")
        if voornaam is not None:
            firstnames.append({"voornaam": voornaam.text})
    firstnames = pd.DataFrame(firstnames).drop_duplicates()
    firstnames.to_csv("datasets\\firstnames.csv", index=False)

    #
    # Download last names
    #
    url = "http://www.naamkunde.net/wp-content/uploads/oudedocumenten/fn10k_versie1.zip"
    urllib.request.urlretrieve(url, "datasets\\RAW_names\\lastnames.zip")
    zf = zipfile.ZipFile("datasets\\RAW_names\\lastnames.zip", 'r')
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
    lastnames.to_csv("datasets\\lastnames.csv", index=False)

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
    diseases.to_csv("datasets\\diseases.csv", index=False)

    #
    # Download medicines
    #
    lst = []
    for ltr in ['u', 'e', 'o', 'a']:
        url = 'https://www.apotheek.nl/zoeken?q=' + ltr + '&filter=medicijnen'
        print(url)
        reqs = requests.get(url)
        soup = BeautifulSoup(reqs.text, 'lxml')
        div = soup.find_all("p", {"class": "searchIndication_text__2l4pd"})

        results = int(div[0].find('span').text)
        print(results)
        count = 0
        while count < results:
            for med in soup.find_all("div", {"class": "searchItem_resultTitle__2TXzJ"}):
                lst.append(med.text)
            url = 'https://www.apotheek.nl/zoeken?q=u&filter=medicijnen&start=' + str(count + 10)
            reqs = requests.get(url)
            soup = BeautifulSoup(reqs.text, 'lxml')
            count += 10
    df = pd.DataFrame(lst, columns=['original'])
    df['lengte'] = df['original'].str.len()
    df = df.sort_values('lengte')
    new = df["original"].str.replace('De Tuinen ', '').str.replace('/', ' ').str.replace(',', ' ') \
        .str.replace('(', ' ').str.split(" ", n=1, expand=True)
    df['medicijn'] = new[0].str.title()
    df = df[['medicijn']].sort_values('medicijn').drop_duplicates()
    df.to_csv("datasets\\medicines.csv", index=False)

    #
    # Download nationalitites
    #
    total = pd.DataFrame(cbsodata.get_data('03743'))
    nationalities = pd.DataFrame(total.Nationaliteiten.unique()[1:-1], columns=['nationaliteit']).drop_duplicates()
    nationalities.to_csv("datasets\\nationalities.csv", index=False)

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
    countries.to_csv("datasets\\countries.csv", index=False)