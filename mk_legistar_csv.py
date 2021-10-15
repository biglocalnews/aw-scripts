import csv
import json

with open('data/legistar.json', 'r') as src:
    data = json.load(src)

headers = [
    'site_type',
    'endpoint',
    'name',
    'state',
    'country',
]
with open('data/legistar.csv', 'w') as out:
    writer = csv.writer(out)
    writer.writerow(headers)
    for row in data['Items']:
        to_write = [
            row['site_type']['S'],
            row['endpoint']['S'],
            row['name']['S'],
            row['state']['S'],
            row['country']['S'],
        ]
        writer.writerow(to_write)
