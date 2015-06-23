#!/bin/bash

#$ -o /mnt/project/pssh/pssh2_project/work/copy_log/
#$ -e /mnt/project/pssh/pssh2_project/work/copy_log/

set -x

mkdir -p /var/tmp/rost_db/data/hhblits/ 2>/dev/null
cd /var/tmp/rost_db/data/hhblits/
time nice tar -xvzf /mnt/project/pssh/pssh2_project/data/pdb_full/pdb_full.tgz

DB.pssh2_local "insert into install_log set who=\"`whoami`\", node=\"`hostname -s`\", stamp=\"`date +%s`\" , package=\"clusterCopyPdbFull.sh\", notes=\"updating pdb_full in /var/tmp/rost_db/data/hhblits/ from /mnt/project/pssh/pssh2_project/data/pdb_full/pdb_full.tgz\" "
