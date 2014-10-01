#!/bin/bash
# assembles jobs from given md5 list
# adjust this script to suit your individual submission needs (parameters to be passed)

set -x

md5List=$1
md5List_batches=$md5List.batches

#xargs -a $md5List -n 5 > $md5List_batches
IFS=$'\n'
#set -f 
#for md5String in `cat $md5List_batches`y
for md5String in `xargs -a $md5List -n 5`
do
	qsub -o /mnt/project/pssh/pssh2_project/work/pssh2_debug/ -e /mnt/project/pssh/pssh2_project/work/pssh2_debug/ /usr/bin/pssh2_multi_md5 -D -m "$md5String" 
done