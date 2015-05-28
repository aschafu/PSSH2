#!/bin/bash
#$ -o /mnt/project/pssh/pssh2_project/work/copy_log/
#$ -e /mnt/project/pssh/pssh2_project/work/copy_log/

set -x

hostname -s
ls -lt /var/tmp/rost_db/data/hhblits/
