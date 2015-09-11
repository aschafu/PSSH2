#!/bin/bash

#$ -o /mnt/project/pssh/pssh2_project/work/copy_log/
#$ -e /mnt/project/pssh/pssh2_project/work/copy_log/

# fist make sure that /mnt/project/pssh/pssh2_project/data/pdb_full/pdb_full.tgz is up to date!

set -x

mkdir -p /var/tmp/rost_db/data/hhblits/ 2>/dev/null
chmod -R a+rwx /var/tmp/rost_db/data/hhblits/
cd /var/tmp/rost_db/data/hhblits/
time nice tar -xvzf /mnt/project/pssh/pssh2_project/data/pdb_full/pdb_full.tgz

DB.pssh2_local "insert into install_log set who=\"`whoami`\", node=\"`hostname -s`\", stamp=\"`date +%s`\" , package=\"clusterCopyPdbFull.sh\", notes=\"updating pdb_full in /var/tmp/rost_db/data/hhblits/ from /mnt/project/pssh/pssh2_project/data/pdb_full/pdb_full.tgz\" "
