"""
Merge CivicPlus and Legistar site metadata CSVs into
a single, standardized file that contains a single row
for every "meeting body" associated with a site.

Output file enables automated and/or manual oaddition of metadata
(e.g. state, county, agency type fields).

Requires:
    * git
    * SSH pubkey uploaded to GitHub
    * Access to the private civic-scraper repo on GitHub
"""
import csv
import json
import os
import sys
from pathlib import Path

import us



def main():
    # FIPS lookup
    global CORRECTIONS, FIPS
    FIPS = CensusFips('data/all-geocodes-v2019.csv')
    CORRECTIONS = get_corrections()

    data_dir = Path('data')
    data_dir.mkdir(exist_ok=True)

    merged = []
    print("Processing Legistar...")
    merged.extend(get_legistar_data())
    print("Processing CivicPlus...")
    merged.extend(get_civicplus_data(data_dir))
    write_civic_sites(merged)
    write_county_fips_annotated_csv(merged)

def write_county_fips_annotated_csv(merged):
    """
    Generate basic CSV showing all county FIPs
    and whether they have at last one corresponding site
    """
    county_fips = FIPS.county_fips_dict
    for row in merged:
        if row['gov_level'] in ['county', 'borough'] and row['country'] == 'USA':
            for fips in row['county_fips']:
                county_fips[fips] = 1
    outfile = 'data/county_fips_annotated.json'
    print(f"Writing {outfile}")
    with open(outfile, 'w') as out:
        json.dump(county_fips, out, indent=4)

def write_civic_sites(merged):
    outfile = 'data/civic_sites.json'
    print(f"Writing {outfile}")
    with open(outfile, 'w') as out:
        json.dump(merged, out, indent=4)

def get_legistar_data():
    source = 'data/legistar.json'
    payload = []
    with open(source, 'r') as infile:
        data = json.load(infile)
        for row in data['Items']:
            raw_country = row['country']['S'].upper().strip()
            country = 'USA' if raw_country == 'UNITED STATES' else raw_country
            outrow = {
                'name': row['name']['S'],
                'state': row['state']['S'],
                'country': country,
                'gov_level': row['site_type']['S'].lower(),
                'county_fips': None,
                'state_fips': None,
                'site_type': 'legistar',
                'site': row['endpoint']['S'],
            }
            add_fips_legistar(outrow)
            payload.append(outrow)
    return payload


def get_civicplus_data(data_dir):
    civdir = data_dir.joinpath('civic-scraper')
    if not civdir.exists():
        print("Cloning CivicPlus repo...")
        os.system(f"cd {data_dir} && git clone git@github.com:biglocalnews/civic-scraper.git")
    else:
        print("Pulling latest from CivicPlus repo...")
        os.system(f"cd {civdir} && git pull")
    sites_file = civdir.joinpath('docs/civicplus_sites.csv')
    with open(sites_file, 'r') as infile:
        reader = csv.DictReader(infile)
        data = []
        for row in reader:
            outrow = {
                'name': row['name'],
                'state': row['state'],
                'country': row['country'].upper(),
                'gov_level': row['govt_level'].lower(),
                'county_fips': None,
                'state_fips': None,
                'site_type': 'civicplus',
                'site': row['end_point'],
            }
            add_fips_civplus(outrow)
            data.append(outrow)
            """
            # Un-nest meeting bodies collapsed into a single "meeting_bodies" list in each row
            # (i.e. create a separate row for each "meeting body" that shares row metadata)
            bodies_raw = row.pop('meeting_bodies')
            bodies = eval(bodies_raw)
            for body in bodies:
                # Because Dicts are annoying...
                outrow.update({
                    'gov_level': gov_level,
                    'meeting_body': body
                })
            """
        return data


def add_fips_legistar(row):
    if row['country'] == 'USA':
        state = row['state']
        name = row['name']
        if row['gov_level'] in ['borough', 'county']:
            try:
                county_fips = FIPS.lookup(state, name)
            except KeyError:
                try:
                    fixed_name = row['name'] + ' County'
                    county_fips = FIPS.lookup(state, fixed_name)
                except KeyError:
                    print(row)
                    sys.exit(f"ERROR on FIPS lookup {state} and {name}")
            row['county_fips'] = county_fips
            row['state_fips'] = county_fips[0][:2]


def add_fips_civplus(row):
    if row['country'] == 'USA':
        state = row['state']
        name = row['name']
        if row['gov_level'] == 'county':
            try:
                county_fips = FIPS.lookup(state, name)
            except KeyError:
                print(row)
                sys.exit(f"ERROR on FIPS lookup {state} and {name}")
            row['county_fips'] = county_fips
            row['state_fips'] = county_fips[0][:2]

class CensusFips:

    def __init__(self, csv_path):
        self._init_lookup(csv_path)

    @property
    def county_fips_dict(self):
        fips = {}
        for state, counties in self._lookup.items():
            for county, code in counties.items():
                fips[code] = 0
        return fips

    def _init_lookup(self, csv_path):
        with open(csv_path, 'r') as infile:
            # Toss preamble rows and header
            for _ in range(5):
                infile.__next__()
            first_row = infile.__next__()
            self._lookup = {}
            reader = csv.reader(infile)
            for row in reader:
                data = dict(zip(self._header, row))
                # if it's a county row, insert into
                # state, then county dict with value equal to full FIPS
                # Insert by state abbreviation. Data is ordered by state
                # first, then counties, so we can be naive about presence
                # of state postal in dictionary.
                if data['sum_level'] == '040':
                    # Initialize the state dictionary
                    state_abbr = us.states.lookup(data['area_name']).abbr
                    self._lookup[state_abbr] = {}
                if data['sum_level'] == '050':
                    # Insert county and its fips
                    county = data['area_name']
                    county_fips = data['state_fips'] + data['county_fips']
                    self._lookup[state_abbr][county] = county_fips

    @property
    def _header(header):
        return [
            'sum_level',
            'state_fips',
            'county_fips',
            'county_subdiv_fips',
            'place_fips',
            'consolidate_city_fips',
            'area_name',
        ]

    def lookup(self, state_abbr, name):
        lkup_name = CORRECTIONS.get(name, name)
        if lkup_name.startswith('['):
            counties = eval(lkup_name)
        else:
            counties = [lkup_name]
        return [
            self._lookup[state_abbr][county]
            for county in counties
        ]

def get_corrections():
    with open('data/corrections.csv') as infile:
        data = {}
        for row in csv.DictReader(infile):
            orig = row['original']
            corrected = row['corrected']
            data[orig] = corrected
        return data

if __name__ == '__main__':
    main()
