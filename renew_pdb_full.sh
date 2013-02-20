#!/bin/bash

## renew_pdb_full.sh
## Process for making a completely new pdb_full. Removes all old files and creates the database again. This ensures that alignments for not anymore existing PDB chains are removed and new uniprot20 sequences are included in all alignments.
## This process should be run every 6 month at least.

## 1. Creation of a non redundant FASTA file of PDB SEQRES records. Non redundant because IDs of chains with identical SEQRES sequence are mentioned in header of one record 
## (ID of the structure with the highest resolution is first).

## First symbolic links to all PDB files in /mnt/project/rost_db/data/pdb/entries/*/ are remade, as the script needs all files in one directory.
pdb_entries_dir="/mnt/project/rost_db/data/pdb/entries/"
pdb_links_dir="/mnt/project/pssh/pdb_full/pdb_links/"
rm -r $pdb_links_dir 2>/dev/null #remove all old links
mkdir $pdb_links_dir 2>/dev/null
for subdir in $(ls $pdb_entries_dir); do ln -s $pdb_entries_dir$subdir/* $pdb_links_dir; done
## Then the non redundant file is created using the modified HH-suite script pdb2fasta.pl (pdb2fasta.non_redundant_chains_AS.pl).
export HHLIB=/mnt/project/pssh/hhsuite-2.0.13
fasta_dir="/mnt/project/pssh/pdb_full/files/fasta/"
mkdir $fasta_dir 2>/dev/null
pdb_chains="pdb_non_redundant_chains.fas"
/mnt/project/pssh/hhsuite-2.0.13/scripts/pdb2fasta.non_redundant_chains_AS.pl '/mnt/project/pssh/pdb_full/pdb_links/*.ent' $fasta_dir$pdb_chains
## Check if the output file was created:
if [ ! -s $fasta_dir$pdb_chains ]
then
	echo the file $pdb_chains does not exist or is empty
	exit 1
fi
## Update the mapping of PDB IDs to md5sums:
/mnt/project/pssh/pdb_full/scripts/pdb_redundant_chains-md5-seq-mapping.pl > /mnt/project/pssh/pdb_redundant_chains-md5-seq-mapping
 

## 2. Splitting of the FASTA file to separate ".seq" files for each sequence using HH-suite script splitfasta.pl.
seq_dir="/mnt/project/pssh/pdb_full/files/seq/"
rm -r $seq_dir 2>/dev/null #remove all old ".seq" files
mkdir $seq_dir 2>/dev/null
cd $seq_dir #change to this directory because splitfasta.pl writes output to the current directory
/mnt/project/pssh/hhsuite-2.0.13/scripts/splitfasta.pl $fasta_dir$pdb_chains

## Remove all sequences only with 'X' and create a file which lists all sequences.
tmp="/mnt/project/pssh/pdb_full/files/tmp"
touch $tmp #create an empy temporary file
pdbseq_file="/mnt/project/pssh/pdb_full/files/pdbseq_file" #file with all PDB fasta input files to run
rm $pdbseq_file 2>/dev/null #delete the old file

# Do for each ".seq" file:
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


## 3. Building profiles (a3m output) running HHblits against uniprot20 using the PDB sequences received in (2.) as input.
## The runs are submitted in portions on the cluster using hhblits_submit.sh, which uses hhblits_sge.sh to distribute the 
## jobs on several nodes and makes sure that each job is finished succesfully (outputs an a3m file).
a3m_dir=/mnt/project/pssh/pdb_full/files/a3m/
rm -r $a3m_dir 2>/dev/null #remove old a3m files
mkdir $a3m_dir 2>/dev/null 
#/mnt/project/pssh/pdb_full/scripts/hhblits_submit.sh
flagfile="/mnt/project/pssh/pdb_full/work/master_submit_hhblits.DO_NOT_REMOVE.flag"
touch $flagfile
/mnt/project/pssh/pdb_full/scripts/master_submit_hhblits.pl 
## wait until all jobs are ready (flag file is gone)
while [ -s $flagfile ] # if true a job is running
do
    sleep 600
done
# if nothing is running - go to the next step

## 4. Adding PSIPRED secondary structure prediction to all MSAs received in (3.) with HH-suite script addss.pl. 
## Output of a3ms with PSIPRED prediction is written to another directory psipred_a3m. Using multithread.pl.
psipred_a3m_dir="/mnt/project/pssh/pdb_full/files/psipred_a3m/"
rm -r $psipred_a3m_dir 2>/dev/null #remove all old a3m files with PSIPRED prediction
mkdir $psipred_a3m_dir 2>/dev/null
addss_log_dir="/mnt/project/pssh/pdb_full/log/addss/"
mkdir $addss_log_dir 2>/dev/null
/mnt/project/pssh/hhsuite-2.0.13/scripts/multithread.pl '/mnt/project/pssh/pdb_full/files/a3m/*.a3m' '/mnt/project/pssh/hhsuite-2.0.13/scripts/addss.pl $file /mnt/project/pssh/pdb_full/files/psipred_a3m/$base.a3m 1>/mnt/project/pssh/pdb_full/log/addss/$base.out 2>/mnt/project/pssh/pdb_full/log/addss/$base.err' -cpu 10

## 5. Generating pdb_full database files with HH-suite script hhblitsdb.pl and the MSAs with PSIPRED prediction received in (4.) as input 
## (runs on jobtest, as hhblitsdb.pl uses multithread.pl).
db="/mnt/project/pssh/pdb_full/db/"
rm -r $db 2>/dev/null #delete old db files
mkdir $db 2>/dev/null

hhblitsdb_log_dir="/mnt/project/pssh/pdb_full/log/hhblitsdb/"
mkdir $hhblitsdb_log_dir 2>/dev/null
/mnt/project/pssh/hhsuite-2.0.13/scripts/hhblitsdb.pl -o '/mnt/project/pssh/pdb_full/db/pdb_full' -ia3m '/mnt/project/pssh/pdb_full/files/psipred_a3m/' -cpu 10 -log "${hhblitsdb_log_dir}hhblitsdb.log"   
