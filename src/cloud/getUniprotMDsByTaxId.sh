#!/bin/bash
echo 'start this with nohup to make sure that it continues if the ssh dies!'
# get the md5 sums to submit

if [ -z "$conf_file" ]; then
	conf_file='/etc/pssh2.conf'
fi

# get configurable options, e.g. local file paths
if [ -s $conf_file ]
then
	source $conf_file
fi

# by default we want to use the system installation
# but if local_paths is set we have the option to change the path and instead use the local variants
if [ $local_paths ]
then
	PATH=$local_paths:$PATH
	export PATH
	echo "Using path: $PATH"
fi

if [ -z $dbDate ]
then
	dbDate='active'
	echo "Environment variable dbDate was undefined. Using \"$dbDate\"."
else
	echo "dbDate is $dbDate"
fi

inputFile=$1
outputFile=taxID_selection_$dbDate.md5

REGION=`wget -q 169.254.169.254/latest/meta-data/placement/availability-zone -O- | sed 's/.$//'`

for taxID in `cat $1`
do
	echo $taxID
	DB.aquaria_local "select distinct md5_hash from protein_sequence where Organism_ID=$taxID" >> $outputFile
done
aws  --region=$REGION  s3 cp $outputFile s3://pssh3cache/hhblits_db_creation/pssh2/$dbDate/
