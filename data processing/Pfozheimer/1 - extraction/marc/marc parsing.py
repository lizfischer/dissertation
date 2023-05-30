import pymarc
import json

with open("pforz_utcatalog.mrc", 'rb') as data:
    reader = pymarc.MARCReader(data)

    misses = []
    catalog_records = {}
    nRecords = 0
    for record in reader:
        if not record['510']:
            misses.append(record)
            continue
        catalog = record['510']['a']
        catalog_records[record['510']['c']] = record.as_dict()
        nRecords += 1
        # if "Pforzheimer" in catalog:
        #     number = record['510']['c']
        #     title = record.title()
        #     if number in catalog_records.keys():
        #         catalog_records[number]["title"] += f"; {title}"
        #     catalog_records[number] = {"title": title}
        # else:
        #     misses.append(record)

    print(len(misses), len(catalog_records), nRecords)
    with open('marc_records.json', 'w') as f:
        json.dump(catalog_records, f, indent=4)