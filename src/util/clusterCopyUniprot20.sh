#!/bin/bash

#$ -o /mnt/project/pssh/pssh2_project/work/copy_log/
#$ -e /mnt/project/pssh/pssh2_project/work/copy_log/

set -x

mkdir -p /var/tmp/rost_db/data/hhblits/ 2>/dev/null
cd /var/tmp/rost_db/data/hhblits/
time nice cp -p /mnt/project/rost_db/data/hhblits/uniprot20_current* /var/tmp/rost_db/data/hhblits/
chmod -R a+rwx /var/tmp/rost_db/data/hhblits/

DB.pssh2_local "insert into install_log set who=\"`whoami`\", node=\"`hostname -s`\", stamp=\"`date +%s`\" , package=\"clusterCopyUniprot20.sh\", notes=\"updating uniprot20 in /var/tmp/rost_db/data/hhblits/ from /mnt/project/rost_db/data/hhblits/\" "
