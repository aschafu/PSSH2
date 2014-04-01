#!/bin/bash

$u20 = '/path/to/uniprot_20';
$big = '';

while getopts ":f:h:a:rb" option;
do
 case $option in
  f)
   $fasta = $OPTARG;
   ;;
  h)
   $hhm = $OPTARG;
   ;;
  a)
   $a3m = $OPTARG;
   ;;
  r)
   $hhr = $OPTARG;
   ;;
  b)
	echo 'received -b, setting option -maxmem 5'
  	$b = '-maxmem 5 '
   ;;
  :)
   echo "option -$OPTARG needs an argument"
   ;;
  *)
   echo "invalid option -$OPTARG" 
   ;;
 esac
done

hhblits -cpu 1 -i $fasta -d $u20 -ohhm $hhm -oa3m $a3m -o $hhr $b;



