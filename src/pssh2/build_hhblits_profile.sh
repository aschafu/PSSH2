#!/bin/bash

# this script is used to sum up the parameters for a profile building hhblits in one place
# it is used by the PredictProtein make file and by the generate_pssh2 perl script

u20='/var/tmp/rost_db/data/hhblits/uniprot20_current'
big=''
reportedHits=" -B 10000 -Z 10000"

usage() { 
	echo "Usage: $0 -f <fasta sequence file> -m <hmm file name> -a <a3m file name> -r <results file name>" 
	echo "             [-b (for much memory)] [-u /path/to/uniprot_20 (without extensions)]" 1>&2
	exit 1; }


while getopts "f:m:a:r:bu:h" option;
do
 case $option in
  f)
   # expects fasta formatted input file
   fasta=$OPTARG;
   ;;
  m)
   # name of output file for hmm 
   hhm=$OPTARG;
   ;;
  a)
   # name of output file for a3m 
   a3m=$OPTARG;
   ;;
  r)
   # name of output file for hhblits results  
   hhr=$OPTARG;
   ;;
  u)
   # path for uniprot_20 for hhblits
   u20=$OPTARG;
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

if  [!$fasta || !$hhm ||!$a3m || !$hhr] usage

echo "running hhblits -cpu 1 -i $fasta -d $u20 -ohhm $hhm -oa3m $a3m -o $hhr $b $reportedHits"
hhblits -cpu 1 -i $fasta -d $u20 -ohhm $hhm -oa3m $a3m -o $hhr $b $reportedHits




