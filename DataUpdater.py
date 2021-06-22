import requests
import json
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

# TODO: Utrecht and Groningen downloads are city only, need bounded box
for name in ['Gelderland', 'Overijssel', 'Drenthe', 'Groningen', 'Friesland', 'Zeeland', 'Utrecht',
             'Limburg', 'Noord-Holland', 'Zuid-Holland', 'Flevoland', 'Noord-Brabant']:
    print(name)
    G = ox.graph_from_place(name + ", Netherlands", network_type="drive")
    gdf_nodes, gdf_edges = ox.graph_to_gdfs(G)
    names = gdf_edges[['name']].reset_index().drop(columns={'u', 'v', 'key'})
    names.name = names.name.astype('str')
    names = names.drop_duplicates()
    names.name = names.name.astype('str')
    names = names[~names.name.str.contains('\[')]
    print(len(names))
    names.to_csv('datasets\\RAW_streets\\streets_' + name + '.csv', index=False)

lst = []
for name in ['Gelderland', 'Overijssel', 'Drenthe', 'Groningen', 'Friesland', 'Zeeland', 'Utrecht',
             'Limburg', 'Noord-Holland', 'Zuid-Holland', 'Flevoland', 'Noord-Brabant']:
    lst.append(pd.read_csv('datasets\\RAW_streets\\streets_' + name + '.csv'))
self.straatnamen = pd.concat(lst, axis=0, ignore_index=True).drop_duplicates()
self.straatnamen.to_csv('datasets\\streets_Nederland.csv', index=False)

total = pd.DataFrame(cbsodata.get_data('84992NED'))
plaatsen = np.append(
    np.append(np.append(total.Woonplaatsen.values, total.Naam_2.values), total.Naam_4.values),
    total.Naam_6.values)
self.plaatsen = pd.DataFrame(plaatsen, columns=['plaatsnaam']).drop_duplicates()
self.plaatsen.to_csv("datasets\\places.csv", index=False)

url = "http://www.naamkunde.net/?page_id=293&vt_download_xml=true"
urllib.request.urlretrieve(url, "datasets\\RAW_names\\firstnames.xml")
xtree = ElementTree.parse("datasets\\RAW_names\\firstnames.xml")
xroot = xtree.getroot()
voornamen = []
for node in xroot:
    voornaam = node.find("voornaam")
    if voornaam is not None:
        voornamen.append({"voornaam": voornaam.text})
self.voornamen = pd.DataFrame(voornamen)
self.voornamen.to_csv("datasets\\firstnames.csv", index=False)

url = "http://www.naamkunde.net/wp-content/uploads/oudedocumenten/fn10k_versie1.zip"
urllib.request.urlretrieve(url, "datasets\\RAW_names\\lastnames.zip")
zf = zipfile.ZipFile("datasets\\RAW_names\\lastnames.zip", 'r')
f = zf.open("fn_10kw.xml")
xtree = ElementTree.parse(f)
xroot = xtree.getroot()
achternamen = []
for node in xroot:
    achternaam = node.find("naam")
    voorvoegsel = node.find("prefix")
    if achternaam is not None:
        if voorvoegsel.text is not None:
            achternamen.append({"achternaam": voorvoegsel.text + " " + achternaam.text})
        else:
            achternamen.append({"achternaam": achternaam.text})
self.achternamen = pd.DataFrame(achternamen)
self.achternamen.to_csv("datasets\\lastnames.csv", index=False)

url = 'https://nl.wikibooks.org/wiki/Geneeskunde/Lijst_van_aandoeningen'
reqs = requests.get(url)
soup = BeautifulSoup(reqs.text, 'lxml')
div = soup.find(id="mw-content-text")
aandoeningen = []
for tag in div.find_all("li"):
    aandoeningen.append(tag.text)
self.aandoeningen = pd.DataFrame(aandoeningen, columns=['aandoening'])
self.aandoeningen.to_csv("datasets\\aandoeningen.csv", index=False)

# TODO Manual parsing still required from XLSX to CSV, but better source required
url = "https://www.ema.europa.eu/sites/default/files/Medicines_output_referrals.xlsx"
urllib.request.urlretrieve(url, "datasets\\RAW_medicijnen\\medicines.xlsx")
# !!! Convert to csv in Excel
medicijnen = pd.read_csv("datasets\\RAW_medicijnen\\medicines.csv", sep=';')
lijst = []
for m in medicijnen.iloc[:, 2]:
    if len(str(m)) > 3:
        for n in m.split(','):
            lijst.append(re.sub(r"\([^()]*\)", "", n).strip())
self.medicijnen = pd.DataFrame(lijst, columns=['medicijn']).drop_duplicates()
self.medicijnen.to_csv("datasets\\medicijnen.csv", index=False)
