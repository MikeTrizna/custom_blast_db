# /bin/sh
module load ~/modulefiles/miniconda
source activate blast_tools
seqkit split data/macse_out.fasta -p 1000 -O data/fasta_split --quiet
