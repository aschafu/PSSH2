#!/bin/bash
# assembles jobs from given md5 list
# adjust this script to suit your individual submission needs (parameters to be passed)

# set -x
md5List=$1
IFS=$'\n'
for md5String in `xargs -a $md5List -n 10`
do
#   useful for degugging:
#	qsub -o /mnt/project/pssh/pssh2_project/work/pssh2_debug/ -e /mnt/project/pssh/pssh2_project/work/pssh2_debug/ /usr/bin/pssh2_multi_md5 -D -m "$md5String" 
#   normal run
	qsub /usr/bin/pssh2_multi_md5 -m "$md5String" 
done