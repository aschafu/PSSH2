#!/bin/bash

set -x 

REGION=`wget -q 169.254.169.254/latest/meta-data/placement/availability-zone -O- | sed 's/.$//'`
ACCOUNT=`wget -q 169.254.169.254/latest/dynamic/instance-identity/document -O- | grep accountId | awk -F'"' '{print $4}'`
instance_id=`wget 169.254.169.254/latest/meta-data/instance-id -qO-`
instance_type=`wget 169.254.169.254/latest/meta-data/instance-type -qO-`
availability_zone=`wget 169.254.169.254/latest/meta-data/placement/availability-zone -qO-`	
pid=$BASHPID

#seqlist=`ls /mnt/data/protein_sequence_201709_representativeSequences/0000002*.fasta`
seqlist=`ls /mnt/data/protein_sequence_201709_representativeSequences/*.fasta`
db_local='/mnt/data/hhblits/uniprot20_2016_02/uniprot20_2016_02'
db_EBS='/mnt/data2/hhblits/uniprot20_2016_02/uniprot20_2016_02'
HHLIB='/usr/share/hhsuite/'
db_path=($db_local $db_EBS)
reportedHits=" -B 10000 -Z 10000"

db_index=0
for storage in 'local' 'EBS' 
do 
	
	db=${db_path[$db_index]}

	for nCpu in '1' '2' 
	do
	
		for sequence in $seqlist 
		do

			hhblitsCommand="$HHLIB/bin/hhblits -i $sequence -o $sequence.hhr -d $db -cpu $nCpu $reportedHits"
			stderr=$((( command time -f ' MemTimeSUe_Stat %M %S %U %e' $hhblitsCommand; ) 1>/dev/null; ) 2>&1; )
			statistics=`echo $stderr | sed 's/.* MemTimeSUe_Stat \([ 0-9.]*\)$/\1/'`
			maxmem=`echo $statistics| awk '{print $1}'`
			sysTime=`echo $statistics| awk '{print $2}'`
			usrTime=`echo $statistics| awk '{print $3}'`
			wallTime=`echo $statistics| awk '{print $4}'`
	
			md5=`basename $sequence .fasta`
	
			jsonFile=$md5.$storage.nCpu_$nCpu.json
			cat << EOF > $jsonFile
{
	"sequence_md5": {"S": "$md5"},
	"conditionString": {"S": "$instance_type-$storage-$nCpu"},
	"architecture": {"S": "$instance_type"},
	"storage": {"S": "$storage"},
	"nCpu": {"N": "$nCpu"},
	"maxmem": {"N": "$maxmem"},
	"sysTime": {"N": "$sysTime"},
	"usrTime": {"N": "$usrTime"},
	"wallTime": {"N": "$wallTime"}
}
EOF
			aws dynamodb put-item --region=$REGION --table-name "runTimes" --item file://$jsonFile
			
		done

	done		
	
	db_index=1
	
done