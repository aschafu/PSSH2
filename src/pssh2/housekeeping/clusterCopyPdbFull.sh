#!/bin/bash

set -x

mkdir -p /var/tmp/rost_db/data/hhblits/ 2>/dev/null
cd /var/tmp/rost_db/data/hhblits/
time nice tar -xvzf /mnt/project/pssh/pssh2_project/data/pdb_full/pdb_full.tgz

/mnt/home/roos/bin/DB.mamut "insert into install_log set who=\"`whoami`\", node=\"`hostname -s`\", stamp=\"`date +%s`\" , package=\"clusterCopyPdbFull.sh\", notes=\"updating pdb_full from /mnt/project/pssh/pssh2_project/data/pdb_full/pdb_full.tgz\"    "