#!/bin/bash
## query database to find number of False positives for different evalue cutoffs

if [ -z "$conf_file" ]; then
        conf_file='/etc/pssh2.conf'
fi

# get configurable options, e.g. local file paths
if [ -s $conf_file ]
then
        source $conf_file
fi

usage()
{
cat << EOT
NAME
  cathStatistics.sh - query database to find number of False positives for different evalue cutoffs
SYNOPSIS
  cathStatistics.sh table_name
DESCRIPTION
  gets the number of false positives based on CAT and CATH codes for different e-value cutoffs
  for the indicated table;
  a false positive is a match with an e-value lower than the cutoff 
  (and higher than cutoff/10 for non-cumulative values)
  where the CATH database (imported to table cath_domains_v420) does not list the same CAT or CATH codes:
  looks for all entries in indicated table with appropriate E-value 
  for which a pair of entries in the CATH table with respective md5 values and identical code cannot be found,
  (also checks that entries occur in CATH table at all)
OPTIONS
  -t          table name to evaluate
  -h          The option -h displays help and exits.
  -D 		  sets -x so the commands are echoed to STDOUT
AUTHOR
  Andrea Schafferhans <andrea.schafferhans@rostlab.org>
EOT
exit 1
}

while getopts "hDt:" option;
do
	case $option in
		h)
		  usage
	  	  exit
	      ;;
	    D)
	      set -x
	      ;;
	    t) table=$OPTARG;;
		:)  echo "Error: -$OPTARG requires an argument"; usage; exit 1;;
	esac
done

if  [ -z "${table}" ] 
then
	usage
	exit 1
fi

outfile="cathStatistics.csv"

# EXAMPLE query for False positives
#select count(distinct Protein_sequence_hash,PDB_chain_hash)
#from pssh2_202002_subset_cath_nr40xnr40 s where
# s.E_value< 1e-12 and s.E_value>1e-13 and
# s.Protein_sequence_hash in (select distinct md5 from cath_domains_v420) and
# s.PDB_chain_hash in (select distinct md5 from cath_domains_v420) and
#not exists 
#(select ca2.CATH_key, cb2.CATH_key from cath_domains_v420 ca2, cath_domains_v420 cb2 where
#s.Protein_sequence_hash = ca2.md5 and
#s.PDB_chain_hash = cb2.md5 and 
#ca2.CAT_key = cb2.CAT_key ); # 1187 / 2032

# EXAMPLE query for ALL positives
# select count(distinct Protein_sequence_hash,PDB_chain_hash) 
# from pssh2_202002_subset_cath_nr40xnr40 s where
# s.E_value< #threshold# and s.E_value>#threshold#/10 and
# s.Protein_sequence_hash in (select distinct md5 from cath_domains_v420) and
# s.PDB_chain_hash in (select distinct md5 from cath_domains_v420)


eValues=('1e-10' '1e-12' '1e-15' '1e-17' '1e-20' '1e-22' '1e-25' '1e-27' '1e-30' '1e-32' '1e-35' '1e-37' '1e-40' '1e-45' '1e-50' '1e-55' '1e-60' '1e-70' '1e-80')
eValues2=('1e-11' '1e-13' '1e-16' '1e-18' '1e-21' '1e-23' '1e-26' '1e-28' '1e-31' '1e-33' '1e-36' '1e-38' '1e-41' '1e-46' '1e-51' '1e-56' '1e-61' '1e-71' '1e-81')

cath_keys=('CAT_key' 'CATH_key')

queryString1="select count(distinct Protein_sequence_hash,PDB_chain_hash) from "
queryString2=" s where s.E_value < "
queryStringBin=" and s.E_value > "
queryString3=" and s.Protein_sequence_hash in (select distinct md5 from cath_domains_v420) and s.PDB_chain_hash in (select distinct md5 from cath_domains_v420) "
queryString3b="and not exists (select ca2.CATH_key, cb2.CATH_key from cath_domains_v420 ca2, cath_domains_v420 cb2 where s.Protein_sequence_hash = ca2.md5 and s.PDB_chain_hash = cb2.md5 and ca2."
queryString4=" = cb2."
queryString5=");"

echo -n "E-value" > $outfile
for je in ${!eValues[@]} 
do
	echo  -n  ", ${eValues[$je]}" >> $outfile
done
echo " " >> $outfile


# cumulative
# ALL hits
echo "ALL cumulative .. " 
echo  -n "ALL cumulative " >> $outfile
for je in ${!eValues[@]} 
do
  echo  -n "," >> $outfile
#	  echo "$queryString1 $table $queryString2 ${eValues[$je]} ${queryString3}${cath_keys[ic]} ${queryString4}${cath_keys[ic]} $queryString5"
  DB.pssh2_local "$queryString1 $table $queryString2 ${eValues[$je]} ${queryString3}"  | tail -1 | tr -d '\n' >> $outfile
done
echo " " >> $outfile
# false positives
for ic in ${!cath_keys[@]}
do
	echo "FP cumulative ${cath_keys[ic]} .. " 
	echo  -n "FP cumulative ${cath_keys[ic]}" >> $outfile
	for je in ${!eValues[@]} 
	do
	  echo  -n "," >> $outfile
#	  echo "$queryString1 $table $queryString2 ${eValues[$je]} ${queryString3}${cath_keys[ic]} ${queryString4}${cath_keys[ic]} $queryString5"
	  DB.pssh2_local "$queryString1 $table $queryString2 ${eValues[$je]} ${queryString3} ${queryString3b}${cath_keys[ic]} ${queryString4}${cath_keys[ic]} $queryString5"  | tail -1 | tr -d '\n' >> $outfile
	done
	echo " " >> $outfile
done

# bins
echo "ALL binned .. " 
echo  -n "ALL binned " >> $outfile
for je in ${!eValues[@]} 
do
  echo  -n "," >> $outfile
#	  echo "$queryString1 $table $queryString2 ${eValues[$je]} ${queryString3}${cath_keys[ic]} ${queryString4}${cath_keys[ic]} $queryString5"
  DB.pssh2_local "$queryString1 $table $queryString2 ${eValues[$je]} $queryStringBin ${eValues2[$je]} ${queryString3}"  | tail -1 | tr -d '\n' >> $outfile
done
echo " " >> $outfile
for ic in ${!cath_keys[@]} 
do
	echo "FP binned ${cath_keys[ic]} .. "
	echo -n "FP binned ${cath_keys[ic]}" >> $outfile
	for je in ${!eValues[@]} 
	do
	  echo -n "," >> $outfile
#	  echo "$queryString1 $table $queryString2 ${eValues[$je]} $queryStringBin ${eValues2[$je]} ${queryString3}${cath_keys[ic]} ${queryString4}${cath_keys[ic]} $queryString5"
	  DB.pssh2_local "$queryString1 $table $queryString2 ${eValues[$je]} $queryStringBin ${eValues2[$je]} ${queryString3} ${queryString3b}${cath_keys[ic]} ${queryString4}${cath_keys[ic]} $queryString5"  | tail -1 | tr -d '\n' >> $outfile
	done
	echo " " >> $outfile
done

