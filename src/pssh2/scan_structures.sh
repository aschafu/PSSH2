#!/bin/bash

# this script is used to sum up the parameters for a structure database (pdb_full) scanning hhblits in one place
# it is used by the PredictProtein make file and by the generate_pssh2 perl script

pdb_full='/var/tmp/rost_db/data/hhblits/pdb_full'
big=''
reportedHits=" -B 10000 -Z 10000"

usage() { 
	echo "Usage: $0 -f <fasta sequence file> -m <hmm file name> -a <a3m file name> -r <results file name>" 
	echo "                           [-b (for much memory)] [-u /path/to/uniprot_20 (without extensions)]" 1>&2
	exit 1; }


while getopts "m:a:r:bu:h" option;
do
 case $option in
  m)
   # name of input hmm profile (generated e.g. with bild_hhblits_profile.sh)
   hhm=$OPTARG;
   ;;
  r)
   # name of output file for hhblits results  
   hhr=$OPTARG;
   ;;
  p)
   # path for pdb_full for hhblits
   pdb_full=$OPTARG;
   ;;
  b)
	echo 'received -b, setting option -maxmem 5'
  	b='-maxmem 5 '
   ;;
  :)
   echo "option -$OPTARG needs an argument"
   usage
   ;;
  h)
   usage  	
   ;;
  *)
   echo "invalid option -$OPTARG" 
   usage
   ;;
 esac
done

if  [ -z "$hhm" -o -z "$hhr" ]; 
then
	usage
fi

echo "running hhblits -cpu 1 -i $fasta -d $u20 -ohhm $hhm -oa3m $a3m -o $hhr $b $reportedHits"
#hhblits -cpu 1 -i $fasta -d $u20 -ohhm $hhm -oa3m $a3m -o $hhr $b $reportedHits




