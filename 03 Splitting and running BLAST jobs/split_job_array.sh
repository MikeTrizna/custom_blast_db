# /bin/sh
qsub -t 1-1000 -tc 100 blast_job_array_template.job
