#!/bin/bash
## query database to find number of all possible matches based on CATH codes

if [ -z "$conf_file" ]; then
        conf_file='/etc/pssh2.conf'
fi

# get configurable options, e.g. local file paths
if [ -s $conf_file ]
then
        source $conf_file
fi

table='tmp_pdb_chain_clean_seqres_202002_filtered_list'

usage()
{
cat << EOT
NAME
  cathStatistics_allTrueMatches.sh - query database to find number of of all possible matches based on CATH codes
SYNOPSIS
  cathStatistics_allTrueMatches.sh -t table_name
DESCRIPTION
  gets the number possible matches for all structures in the non redundant data set of CATH (nr40);
  a possible match is any sequence (identified by md5) that has a CATH code that agrees in all 4 digits
  and has been processed when the pssh2 table was generated: 
  retrieves all distinct md5 from cath_non_redundant_40,
  for each: finds all distinct md5s sharing one of the CATH codes for that sequence (and bing in the considered set),
  sums up all matches
OPTIONS
  -t          table name containing pdb sequences used in building the pssh2 database being evaluated, default: $table
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

outfile="cathStatistics_allTrueMatches.csv"

# QUERY for all md5s
# select distinct md5 from cath_non_redundant_40 where md5 is not null;
query_cath_nr_40="select distinct md5 from cath_non_redundant_40 where md5 is not null"

# EXAMPLE query for ALL positives
#select count(distinct cd1.md5) from cath_domains_v420 cd1 where 
#cd1.CATH_key in 
#(select cd2.CATH_key from cath_domains_v420 cd2
#where cd2.md5 = '0005357e8c63860c9274031358fbdcaa')
#and cd1.md5 is not null
#and cd1.md5 in (select distinct MD5_hash from tmp_pdb_chain_clean_seqres_202002)
# for checking only against cath_nr_40, add further constraint:
#and cd1.md5 in (select distinct md5 from cath_non_redundant_40);

queryString1="select count(distinct cd1.md5) from cath_domains_v420 cd1 where cd1.CATH_key in (select cd2.CATH_key from cath_domains_v420 cd2
where cd2.md5 = '"
queryString2="') and cd1.md5 is not null and cd1.md5 in (select distinct MD5_hash from " 
queryString3=");"
queryString3b=") and cd1.md5 in (select distinct md5 from cath_non_redundant_40);"

md5s_cath_nr_40=`DB.pssh2_local $query_cath_nr_40`  

echo "md5,matchCount" > $outfile
count=0
sum=0
progress=0
for md5 in $md5s_cath_nr_40
do
#	count=`DB.pssh2_local "${queryString1}${md5}${queryString2} $table $queryString3" | tail -1 | tr -d '\n'`
	count=`DB.pssh2_local "${queryString1}${md5}${queryString2} $table $queryString3b" | tail -1 | tr -d '\n'`
	echo "$md5,$count">>$outfile
	sum=$(($sum+$count))
	progress=$((progress+1))
	if [ $progress -eq 10 ]
	then
		echo -n "."
		progress=0
	fi
	count=0
done
echo " "
echo "total possible matches: $sum"

