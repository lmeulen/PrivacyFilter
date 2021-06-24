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
# TODO: REduce the number of dependencies (like pandas, geopandas, ...)

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
    # TODO Manual parsing still required from XLSX to CSV, but better source required
    url = "https://www.ema.europa.eu/sites/default/files/Medicines_output_referrals.xlsx"
    urllib.request.urlretrieve(url, "datasets\\RAW_medicijnen\\medicines.xlsx")
    # !!! Convert to csv in Excel
    medicines = pd.read_csv("datasets\\RAW_medicijnen\\medicines.csv", sep=';')
    lijst = []
    for m in medicines.iloc[:, 2]:
        if len(str(m)) > 3:
            for n in m.split(','):
                lijst.append(re.sub(r"\([^()]*\)", "", n).strip())
    medicines = pd.DataFrame(lijst, columns=['medicijn']).drop_duplicates()
    medicines.to_csv("datasets\\medicines.csv", index=False)

    #
    # Download nationalitites
    #
    total = pd.DataFrame(cbsodata.get_data('03743'))
    nationalities = pd.DataFrame(total.Nationaliteiten.unique()[1:-1], columns=['nationaliteit']).drop_duplicates()
    nationalities.to_csv("datasets\\nationalities.csv", index=False)