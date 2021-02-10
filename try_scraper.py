"""
TITLE: try_scraper.py

Tests the functionality of civic-scraper and reports results into a csv.

USAGE: From the command line,

    python3 try_scraper.py \ 
    "~/.temp/civic_plus_sites.csv" \ # csv of urls to test
    "~/.temp/try_scraper.csv" \ # name of csv file to export
    "~/.temp/metadata/" # directory to store csvs created by to_csv function
"""

# Check if websites work

from civic_scraper.platforms import CivicPlusSite
from collections import defaultdict
import requests
import csv
import os
import bs4
import re

def try_scraper(file_in, file_out, metadata_path):
    raw_list = read_file(file_in)
    test_urls(raw_list, metadata_path, file_out)

def read_file(file_in):
    # Read in each line of the .csv, reformat them and add them to a list

    columns = defaultdict(list) # each value in each column is appended to a list

    with open(file_in) as f:
        reader = csv.DictReader(f) # read rows into a dictionary format
        for row in reader: # read a row as {column1: value1, column2: value2,...}
            for (k,v) in row.items(): # go over each column name and value 
                columns[k].append(v) # append the value into the appropriate list
                                    # based on column name k

    return columns['url']

def write_file(file_out, checked):
    # Write out the dict to a csv
    with open(file_out, 'a', newline='') as f:
        dict_writer = csv.DictWriter(f, checked.keys())
        if os.stat(file_out).st_size == 0:
            dict_writer.writeheader()
        dict_writer.writerow(checked)

def test_urls(raw_list, metadata_path, file_out):
    for url in raw_list:
        try:
            response = requests.get(url, allow_redirects=True)
            status_code = response.status_code

            years = check_years(response)
            (history, alias) = check_redirect(response)
            
            # Test the scraper
            site = CivicPlusSite(url)
            assets = site.scrape()
            assets.to_csv(metadata_path)
            
            checked = {
                "status_code": status_code, 
                "history": history, 
                "alias": alias, 
                "site": url, 
                "error": None,
                "years": len(years) > 0
            }
            write_file(file_out, checked)
        except (requests.exceptions.RequestException, requests.exceptions.HTTPError, AttributeError) as e:
            checked = {
                "status_code": None, 
                "history": None, 
                "alias": None, 
                "site": url, 
                "error": e,
                "years": None
            }
            write_file(file_out, checked)

def check_redirect(response):
    # Check if site redirects
    if len(response.history) > 0:
        history = response.history
        alias = response.url
    else:
        history = None
        alias = None
    
    return (history, alias)

def check_years(response):
    # Check to see if there are any documents posted on the site
    soup = bs4.BeautifulSoup(response.text, 'html.parser')
    return soup.find_all(href=re.compile("changeYear"))
    
if __name__ == '__main__':

    """
    Call generate_site_csv from the command line.
    """

    import argparse


    # Set up parser
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'file_in',
        type=str
    )
    parser.add_argument(
        'file_out',
        type=str,
    )
    parser.add_argument(
        'metadata_path',
        type=str,
    )

    args = parser.parse_args()

    # Call function
    site_civicplus = try_scraper(
        file_in=args.file_in,
        file_out=args.file_out,
        metadata_path=args.metadata_path
    )