#!/bin/bash

## 1. Creation of a non redundant FASTA file of PDB SEQRES records. Non redundant because 
## IDs of chains with identical SEQRES sequence are mentioned in header of one record 
## (ID of the structure with the highest resolution is first).

## First symbolic links to all PDB files in /mnt/project/rost_db/data/pdb/entries/*/ are remade, as the script needs all files in one directory.
rm -r /mnt/project/pssh/pdb_full/pdb_links/ 2>/dev/null
mkdir /mnt/project/pssh/pdb_full/pdb_links/ 2>/dev/null
for dir in $(ls /mnt/project/rost_db/data/pdb/entries); do ln -s /mnt/project/rost_db/data/pdb/entries/$dir/* /mnt/project/pssh/pdb_full/pdb_links/; done
## Then the non redundant file is created using the modified HH-suite script pdb2fasta.pl (pdb2fasta.non_redundant_chains_AS.pl).
export HHLIB=/mnt/project/pssh/hhsuite-2.0.13
mkdir /mnt/project/pssh/pdb_full/files/fasta 2>/dev/null
/mnt/project/pssh/hhsuite-2.0.13/scripts/pdb2fasta.non_redundant_chains_AS.pl '/mnt/project/pssh/pdb_full/pdb_links/*.ent' /mnt/project/pssh/pdb_full/files/fasta/pdb_non_redundant_chains.fas
## Check if the output file was created:
if [ ! -s /mnt/project/pssh/pdb_full/files/fasta/pdb_non_redundant_chains.fas ]
then
	echo the file pdb_non_redundant_chains.fas does not exist or is empty
	exit 1
fi
 

## 2. Splitting of the FASTA file to separate ".seq" files for each sequence using HH-suite script splitfasta.pl.
seq_dir="/mnt/project/pssh/pdb_full/files/seq/"
rm -r $seq_dir 2>/dev/null
mkdir $seq_dir 2>/dev/null
cd $seq_dir
/mnt/project/pssh/hhsuite-2.0.13/scripts/splitfasta.pl /mnt/project/pssh/pdb_full/files/fasta/pdb_non_redundant_chains.fas

## Remove all sequences only with 'X' and create a file which lists all sequences.
tmp="/mnt/project/pssh/pdb_full/files/tmp"
touch $tmp #create an empy temporary file
pdbseq_file="/mnt/project/pssh/pdb_full/files/pdbseq_file" #file with all PDB fasta input files to run
rm $pdbseq_file 2>/dev/null #delete the old file

# Do for each *.seq file:
cd $seq_dir
for file in $(ls); do 
   tail -n +2 $file | grep -v 'X' > $tmp #overwrite into tmp all AA from the sequence in the current file that are NOT 'X'
   if [ ! -s $tmp ] #tmp is empty -> the sequence in the current file has only 'X' 
   then
       rm $file # -> remove the file with only 'X' in the sequence
	echo "The sequence in $file has only 'X' - $file removed."
   else # file OK
       echo $file >> $pdbseq_file # add the file name to pdbseq_file
   fi
done
rm $tmp


## 3. Building profiles (a3m output) running HHblits against UniProt20 using the PDB sequences received in (2.) as input.
## The run are submitted in portions on the cluster using hhblits_submit.sh, which uses hhblits_sge.sh to distribute the 
## jobs on several nodes and makes sure that each job is finished succesfully (outputs an a3m file).
mkdir /mnt/project/pssh/pdb_full/files/a3m 2>/dev/null 
/mnt/project/pssh/pdb_full/scripts/hhblits_submit.sh
## wait until all jobs are ready
qstat_tmpfile="/mnt/project/pssh/pdb_full/scripts/qstat_final.out"
qstat > $qstat_tmpfile
while [ -s $qstat_tmpfile ] # if true a job is runing
do
    sleep 60
    qstat > $qstat_tmpfile
done
# if nothing is running - go to the next step

## 4. Adding PSIPRED secondary structure prediction to all MSAs received in (3.) with HH-suite script addss.pl. 
## Output of a3ms with PSIPRED prediction is written to another directory psipred_a3m. Using multithread.pl.
mkdir /mnt/project/pssh/pdb_full/files/psipred_a3m 2>/dev/null
mkdir /mnt/project/pssh/pdb_full/log/addss 2>/dev/null
/mnt/project/pssh/hhsuite-2.0.13/scripts/multithread.pl '/mnt/project/pssh/pdb_full/files/a3m/*.a3m' '/mnt/project/pssh/hhsuite-2.0.13/scripts/addss.pl $file /mnt/project/pssh/pdb_full/files/psipred_a3m/$base.a3m  1>/mnt/project/pssh/pdb_full/log/addss/$base.out 2>/mnt/project/pssh/pdb_full/log/addss/$base.err' -cpu 10

## 5. Generating pdb_full database files with HH-suite script hhblitsdb.pl and the MSAs with PSIPRED prediction received in (4.) as input 
## (runs on jobtest, as hhblitsdb.pl uses multithread.pl).
mkdir /mnt/project/pssh/pdb_full/db 2>/dev/null
mkdir /mnt/project/pssh/pdb_full/log/hhblitsdb 2>/dev/null
/mnt/project/pssh/hhsuite-2.0.13/scripts/hhblitsdb.pl -o '/mnt/project/pssh/pdb_full/db/pdb_full' -ia3m '/mnt/project/pssh/pdb_full/files/psipred_a3m/' -cpu 10 -log /mnt/project/pssh/pdb_full/log/hhblitsdb/hhblitsdb.log   
