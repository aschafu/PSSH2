#!/bin/bash
# assembles jobs from given md5 list
# adjust this script to suit your individual submission needs (parameters to be passed)

set -x

md5List=$1
md5List_batches={$md5List}.batches

xargs -a $md5List -n 5 | awk '{printf("\"%s\"\n", $0);}' > $md5List_batches
IFS=$'\n'
#set -f 
for md5String in `cat $md5List_batches`
do
	qsub -o /dev/null -e /dev/null pssh2_multi_md5 -m $md5String 
done