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

otherFile=otherSequences.md5
submitted=lastSubmitted.list
pssh_normal_queue='pssh'
pssh_long_queue='pssh_bigJobs'
pssh_fail_queue='pssh_failed'

if [ -z $dbDate ]
then
	dbDate='active'
	echo 'Environment variable dbDate was undefined. Using \"$dbDate\".'
else
	echo 'dbDate is $dbDate'
fi

REGION=`wget -q 169.254.169.254/latest/meta-data/placement/availability-zone -O- | sed 's/.$//'`

swissFile=swissprot.uniq.$dbDate.md5
pdbFile=pdbChain.uniq.xlt50.clgt10.$dbDate.md5
allFile=allSequences.$dbDate.md5


aws  --region=$REGION  s3 cp s3://pssh3cache/hhblits_db_creation/pssh2/$dbDate/$allFile .
if [ -s $allFile ]
then
	aws  --region=$REGION  s3 cp s3://pssh3cache/hhblits_db_creation/pssh/$dbDate/$submitted .
	if [ -s $submitted ]
	then
		lastLine=`tail -1 $submitted`
		offset=`grep -n $lastLine | cut -d : -f 1`
		echo 'restarting with info from $allFile and $submitted on line $offset'
	else
		offset=1
	fi
else
	# get swissprot sequences
	~/git/PSSH2/src/util/DB.aquaria_local "select distinct md5_hash from protein_sequence where Source_Database='swissprot'" > $swissFile
	# resuse pdb list
	aws  --region=$REGION  s3 cp s3://pssh3cache/hhblits_db_creation/pdb_full/$dbDate/$pdbFile .
	# get any other list that might have been put there
	aws  --region=$REGION  s3 cp s3://pssh3cache/hhblits_db_creation/pssh2/$dbDate/$otherFile .

	sort $swissFile $pdbFile $otherFile | grep -i -v md5 | uniq > $allFile
	aws  --region=$REGION  s3 cp $allFile s3://pssh3cache/hhblits_db_creation/pssh2/$dbDate/
	offset=1
fi

count=0
for md5 in `tail -n +$offset $allFile` 
do 
	echo $md5
	aws --region=$REGION sqs send-message --queue-url https://sqs.$REGION.amazonaws.com/$ACCOUNT/$pssh_normal_queue --message-body $md5
	count=$((count+1))
	if [ $count -eq 1000 ]
	then
		echo $md5 >> $submitted 
		aws --region=$REGION  s3 cp $submitted s3://pssh3cache/hhblits_db_creation/pssh2/$dbDate/
		count=0
	fi
done
