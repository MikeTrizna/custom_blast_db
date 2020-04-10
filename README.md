# Custom BLAST database

Utilities for making a versioned custom blast database

This is the documentation of creating a custom BLAST database of non-environmental COI sequences, and then querying a large environmental sample against it to find taxonomic composition.

This overall pipeline is split into the following components, which correspond to the directories in this repo. You can read more about each step in the individual directory README files.

## Getting sequences

To create a custom BLAST database, you need 2 components:

* A FASTA-formatted file of DNA sequences
* (optional) A tsv file of sequence IDs and NCBI taxonomy IDs

## Creating local database

The `makeblastdb` function from BLAST is used to create a local database. However, we ran into virtual memory issues on Hydra, and ironically had to run this step on a laptop and then transfer back to Hydra.

## Splitting and running BLAST jobs

The file of environmental sequences contains 278,775 sequences. Since BLAST is only able to run serially, we can achieve parallelism by splitting up this file into many files and submitting them as part of a job array on Hydra.

## Gather results and annotate

The job array submission leaves us with several result files that need to be combined back together. This combined file only contains the NCBI taxonomy ID of matching sequences, so it needs to be joined with a file from the NCBI taxonomy database to provide all taxonomic levels.