#!/bin/bash

# hhblits_submit.sh
# Submits HHblits runs to the Rostlab cluster, to run paralelly in portions.
# Calls /mnt/project/pssh/pdb_full/scripts/hhblits_sge.sh

n=3000 #portion of sequences to run
i=$n #defines end line of cmds.txt for the next portion of $n cmds

qstat_tmpfile="/mnt/project/pssh/pdb_full/scripts/qstat.out"
pdbseq_file="/mnt/project/pssh/pdb_full/files/pdbseq_file" #file with list of all query sequences
len=$(cat $pdbseq_file | wc -l) #number of query sequences

while [ $i -le $len ]; do 

    qstat > $qstat_tmpfile
    if [ -s $qstat_tmpfile ] #not empty -> a job is still running
    then
	sleep 60
    else #qstat had no output = all jobs ready!(or this script just started)
	 #submit the next $n cmds in portions of 60 (assumed max 4 min per query sequence: 60 * 4min = 240 min = 4 h) -> $n/60 jobs with 60 script calls in each, run parallelly on the cluster:
	cat $pdbseq_file | head -n $i | tail -n $n | xargs -n 60 qsub /mnt/project/pssh/pdb_full/scripts/hhblits_sge.sh
    fi
    let i=i+$n

done
# run the left sequences (less than $n; without waiting)
if [ $i -gt $len ]
then
    let i=i-$n #restore last done sequence
    let last=$len-$i #number of sequences left to run
    if [ $last -gt 0 ]
    then
	cat $pdbseq_file | tail -n $last | xargs -n 60 qsub /mnt/project/pssh/pdb_full/scripts/hhblits_sge.sh
    fi
fi
