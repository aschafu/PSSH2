#!/bin/bash
# script to carry out a one-time fix on the headers of a3m and hhm files
#set -x
# get config data
REGION=`wget -q 169.254.169.254/latest/meta-data/placement/availability-zone -O- | sed 's/.$//'`

if [ -z "$conf_file" ]; then
	conf_file='/etc/pssh2.conf'
fi

#### parameters (will be overwritten by anything read from conf file)
seqfile='query.fasta' 
hhblitsLog='hhblits.log' 
a3mfile='query.uniprot20.a3m' 
hmmfile='query.uniprot20.hhm'
pa3mfile='query.uniprot20.psipred.a3m' 
rootDir="/mnt/project/pssh/pssh2_project/" 
temp_work="/tmp/pssh2"
dbDate='current'
dbName='pdb_full'
a3mDir='/mnt/resultData/pdb_full_201909/a3m/'
hhmDir='/mnt/resultData/pdb_full_201909/hhm/'
n_cpu=1
build_fail_queue='build_hhblits_structure_profiles_failed'
debug=0

# get configurable options, e.g. local file paths
if [ -s $conf_file ]
then
	source $conf_file
fi


keepWorking=1
while [ $keepWorking -gt 0 ]
do
	MSG=`aws --region=$REGION sqs receive-message --queue-url https://sqs.$REGION.amazonaws.com/$ACCOUNT/$build_fail_queue --query 'Messages[*].[ReceiptHandle,Body]' --output text`
	HANDLE=`awk '{print $1}' <<< $MSG`
	md5=`awk '{print $2}' <<< $MSG`

	# if we really received something, we process, otherwise we poll again until we are killed
	if [ -z $md5 ]
	then
		CC='fake'
		skip_all=1
	else
		# here, we don't only set the path location, but also fetch the data from the cache
		CC=`$rootDir/src/util/aws_local_cache_handler -m $md5 -r | tail -1`
		skip_all=0
	fi

	if [ $skip_all -eq 0 ]
	then
		cd $CC
		sed -i "s/>[1-9][a-zA-Z0-9][a-zA-Z0-9][a-zA-Z0-9]_[a-zA-Z0-9]/>$md5/" $pa3mfile
		if grep "# $md5" $pa3mfile
		then 
			echo 'header ok'
		else
			sed -i "1s;^;# $md5 \n;" $pa3mfile
		fi
		sed -i "s/NAME  [1-9][a-zA-Z0-9][a-zA-Z0-9][a-zA-Z0-9]_[a-zA-Z0-9]/NAME  $md5/" $hmmfile
		$rootDir/src/util/copy_to_S3 -m $md5 -p $CC/$hmmfile -a $CC/$pa3mfile -d $dbDate -n $dbName
		$rootDir/src/util/aws_local_cache_handler -m $md5 -s
		cp $pa3mfile $a3mDir/$md5
		cp $pa3mfile $hhmDir/$md5
		cd $temp_work
		if [ $debug -eq 0 ]
		then
			rm -r $CC
		fi

		# send the queue a message that this sequence has been processed
		aws --region=$REGION sqs delete-message --queue-url https://sqs.$REGION.amazonaws.com/$ACCOUNT/$build_fail_queue --receipt-handle $HANDLE

	fi
	
done

