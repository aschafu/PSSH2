#!/bin/bash

set -x

mkdir -p /var/tmp/rost_db/data/hhblits/ 2>/dev/null
cd /var/tmp/rost_db/data/hhblits/
time nice tar -xvzf /mnt/project/pssh/pssh2_project/data/pdb_full/pdb_full.tgz
