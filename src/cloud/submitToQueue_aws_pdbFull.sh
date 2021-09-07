#!/bin/bash
echo 'start this with nohup to make sure that it continues if the ssh dies!'

if [ -z "$conf_file" ]; then
        conf_file='/etc/pssh2.conf'
fi

# get configurable options, e.g. local file paths
if [ -s $conf_file ]
then
        source $conf_file
fi

# get the md5 sums to submit
if [ -z $dbDate ]
then
	dbDate='current'
	echo 'Environment variable dbDate was undefined. Using "current".'
fi

if [ -z $aquaria_name ]
then
	echo "Missing parameters: 'aquaria_name' is undefined. > Source conf_file? "
	exit 1
fi

while getopts :siD opt
do
	case $opt in
	s) silent=1; debug=0;; 
	i) incremental=1;;
	D) debug=1;; 
	:)  echo "Error: -$OPTARG requires an argument"; usage; exit 1;;
	esac
done

if [ $debug -eq 1 ]
then
	set -x
	echo "conf_file: $conf_file"
fi

# set the additional query string we need in case we only want to do an incremental update of pdb_full
incremental_options=''
if [ $incremental -eq 1 ]
then
    incremental_options="and exists (select p.Published from $aquaria_name.PDB p where (p.Published > '$lastFullUpdate' or p.Revision_Date > '$lastFullUpdate') and p.PDB_ID=c.PDB_ID)"
#    Should have been set in the conf_file: Should have been set in the conf_file: build_normal_queue, dbDate
fi


REGION=`wget -q 169.254.169.254/latest/meta-data/placement/availability-zone -O- | sed 's/.$//'`

# CAVE: here we are selecting from database $aquaria_name
# check that the database specified in the conf file really contains the newest update of PDBchain!
~/git/PSSH2/src/util/DB.pssh2_local "create table tmp_pdb_chain_clean_seqres_$dbDate as select MD5_Hash, group_concat(pdb_id, Chain separator ', ') as pdb_ids, SEQRES, length,  Replace (SEQRES, 'X', '') as clean_seqres, length(Replace (SEQRES, 'X', '')) as c_length,  ((length - length(Replace (SEQRES, 'X', ''))) / length) as x_ratio from $aquaria_name.PDB_chain c where type='Protein' and length>10 $incremental_options group by MD5_Hash;"

~/git/PSSH2/src/util/DB.pssh2_local "select MD5_Hash from tmp_pdb_chain_clean_seqres_$dbDate t where t.x_ratio < 0.5 and t.c_length > 10" > pdbChain.uniq.xlt50.clgt10.$dbDate.md5
aws  --region=$REGION  s3 cp pdbChain.uniq.xlt50.clgt10.$dbDate.md5 s3://pssh3cache/hhblits_db_creation/pdb_full/$dbDate/
count=0
for md5 in `tail -n +1 pdbChain.uniq.xlt50.clgt10.$dbDate.md5`
do
	echo $md5
	aws --region=$REGION sqs send-message --queue-url https://sqs.$REGION.amazonaws.com/$ACCOUNT/$build_normal_queue --message-body $md5
	count=$((count+1))
	if [ $count -eq 1000 ]
	then
		echo $md5 >> /tmp/lastSubmitted.list 
		aws --region=$REGION  s3 cp /tmp/pssh2/lastSubmitted.list s3://pssh3cache/hhblits_db_creation/pdb_full/$dbDate/
		count=0
	fi
done
