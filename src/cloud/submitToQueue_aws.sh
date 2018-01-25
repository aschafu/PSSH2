#!/bin/bash
echo 'start this with nohup to make sure that it continues if the ssh dies!'
# get the md5 sums to submit
if [ -z $dbDate ]
then
	dbDate='current'
	echo 'Environment variable dbDate was undefined. Using "current".'
fi
~/git/PSSH2/src/util/DB.pssh2_local "select MD5_Hash from tmp_pdb_chain_clean_seqres_$dbDate t where t.x_ratio < 0.5 and t.c_length > 10" > pdbChain.uniq.xlt50.clgt10.$dbDate.md5
aws  --region=$REGION  s3 cp pdbChain.uniq.xlt50.clgt10.$dbDate.md5 s3://pssh3cache/hhblits_db_creation/pdb_full/$dbDate/
for md5 in `tail -n +1 pdbChain.uniq.xlt50.clgt10.$dbDate.md5` ; do echo $md5; aws --region=$REGION sqs send-message --queue-url https://sqs.$REGION.amazonaws.com/$ACCOUNT/build_hhblits_structure_profiles --message-body $md5; done
