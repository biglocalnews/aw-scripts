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
from pathlib import Path


def main():
    data_dir = Path('data')
    data_dir.mkdir(exist_ok=True)
    civplus = get_civicplus_data(data_dir)
    outfile = 'data/gov_bodies_by_site.csv'
    print(f"Writing out {outfile}...")
    with open(outfile, 'w') as out:
        fieldnames = civplus[0].keys()
        writer = csv.DictWriter(out, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(civplus)

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
        # Un-nest meeting bodies collapsed into a single "meeting_bodies" list in each row
        # (i.e. create a separate row for each "meeting body" that shares row metadata)
        data = []
        for row in reader:
            bodies_raw = row.pop('meeting_bodies')
            bodies = eval(bodies_raw)
            for body in bodies:
                # Because Dicts are annoying...
                outrow = row.copy()
                outrow['meeting_body'] = body
                data.append(outrow)
        return data

def get_legistar_data():
    return []

if __name__ == '__main__':
    main()
