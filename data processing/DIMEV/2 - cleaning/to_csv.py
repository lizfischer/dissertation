import json
import pandas as pd

with open('../1 - extraction/all_records.json', 'r') as infile:
    texts = json.load(infile)

texts_df = pd.DataFrame(texts).transpose()
texts_df = texts_df.drop('_witnesses', axis=1)
texts_df = texts_df.rename(columns={'_id': 'Id', '_header': 'Label'})
texts_df['Id'] = 'DIMEV ' + texts_df['Id'].astype(str)
texts_df['Type'] = 'Text'
texts_df.to_csv('text_info_file.tsv', sep='\t', encoding='utf-8', index=False)

# TODO: concat MSS & Texts node lists
# TODO: check relationships gephi format
# TODO: Handle author ? and 'attrib' 

relationships = []
for t in texts:
    for wit in texts[t]['_witnesses']:
        rel = {'text': f'DIMEV {t}',
               'witness': wit,
               **texts[t]['_witnesses'][wit]
               }
        relationships.append(rel)
relationships_df = pd.DataFrame(relationships)
relationships_df = relationships_df.replace(r'^\s*','', regex=True).replace(r'\n',r'\\n', regex=True)
relationships_df = relationships_df.rename(columns={'text': 'Source', 'witness': 'Target'})

relationships_df.to_csv('relationships.tsv',  sep='\t', index=False)


# MS Info
ms_df = pd.read_csv('mss_info.csv', sep='|', encoding='cp1252')
ms_df = ms_df.rename(columns={'ID': 'Id', 'Name': 'Label'})
ms_df['Type'] = 'MS'
ms_df.to_csv('mss_info_revised.tsv',  sep='\t', index=False)

    # record = {'_id': dimev_num,
    #           '_header': header,
    #           **_bold_headers_to_key_value_pairs(details_elements[1:], collapse_whitespace=True),
    #           '_description': _collapse_whitespace(details_elements[0].text),
    #           '_witnesses': {}}
