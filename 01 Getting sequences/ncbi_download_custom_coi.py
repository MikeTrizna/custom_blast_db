import pandas as pd
import requests
from lxml import objectify

from datetime import date
from datetime import datetime
import time
import argparse
from tenacity import retry
from tenacity.stop import stop_after_attempt
from tenacity.wait import wait_fixed

SEARCH_TERM = "coi[Gene] OR cox1[Gene] OR co1[Gene]"

NAME_EXCLUDE = ['uncultured', 'environmental', 
                'Protostomia', 'metagenome']

esearch = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi'

search_params = {'term': SEARCH_TERM,
                 'db': 'nuccore',
                 'retmode': 'json',
                 'retmax': 10,
                 'idtype':'acc',
                 'usehistory': 'y'}

r = requests.post(esearch, data=search_params)
search_results = r.json()

result_count = int(search_results['esearchresult']['count'])
query_key = search_results['esearchresult']['querykey']
web_env = search_results['esearchresult']['webenv']

print('Search for {} had {} results.'.format(SEARCH_TERM, result_count))

@retry(stop=stop_after_attempt(7), wait=wait_fixed(2))
def parse_fasta_xml(query_key, web_env, retstart, batch_size):
    fetch_url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi'
    params = {'db': 'nuccore',
              'rettype': 'fasta',
              'retmode': 'xml',
              'query_key': query_key,
              'WebEnv': web_env,
              'retstart': retstart,
              'retmax':batch_size}
    r = requests.post(fetch_url, data=params)
    try:
        results = []
        xml_results = objectify.fromstring(r.content)
        for record in xml_results.TSeq:
            result = {}
            result['accession'] = record['TSeq_accver'].text.split('.')[0]
            result['taxid'] = record['TSeq_taxid'].text
            result['sci_name'] = record['TSeq_orgname'].text
            result['sequence'] = record['TSeq_sequence'].text
            results.append(result)
        return results
    except:
        print('Error at {}. Trying again...'.format(retstart))
        raise Exception

all_seqs = []
batch_size = 1000
for retstart in range(0, result_count, batch_size):
    if retstart % 100_000 == 0:
        print('{} at {}'.format(retstart,
                                datetime.now().strftime('%H:%M:%S')))
    seq_list = parse_fasta_xml(query_key, web_env, retstart, batch_size)
    all_seqs += seq_list
    time.sleep(1)

print("{} sequences downloaded from NCBI".format(len(all_seqs)))

current_date = date.today().strftime("%Y_%m_%d")
fasta_file = 'results/coi_custom_{}.fasta'.format(current_date)
accession_tsv = "results/coi_custom_accesssions_{}.tsv".format(current_date)

fasta_counter = 0
with open(fasta_file, 'w') as fasta_out:
    for seq in all_seqs:
        bad_name = any(name in seq['sci_name'] for name in NAME_EXCLUDE)
        if bad_name is False:
            fasta_counter += 1
            fasta_string = '>{}\n{}\n'.format(seq['accession'],
                                            seq['sequence'])
            fasta_out.write(fasta_string)

print("{} sequences in FASTA after filtering ".format(fasta_counter))

coi_df = pd.DataFrame(all_seqs)
coi_df = coi_df[['accession','taxid','sci_name']]

for bad_name in NAME_EXCLUDE:
    coi_df = coi_df[~coi_df['sci_name'].str.contains(bad_name)]

print("{} sequences in TSV after filtering".format(len(coi_df)))

coi_df.to_csv(accession_tsv, sep='\t', index=False)
