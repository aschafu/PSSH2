#!/bin/bash

# assumes that 
# * you have a set up the system to have a '/mnt/data' with storage space available

set -x
exec > >(tee /var/log/user-data-pssh2.log|logger -t user-data ) 2>&1

cd /mnt/data
mkdir /mnt/data/hhblits/
chmod a+tw /mnt/data/hhblits/
curl -o uniprot20_2015_06.tgz http://wwwuser.gwdg.de/~compbiol/data/hhsuite/databases/hhsuite_dbs/uniprot20_2015_06.tgz
tar -xvf uniprot20_2015_06.tgz  -C /mnt/data/hhblits/
rm uniprot20_2015_06.tgz
curl -o pdb_full.current.tgz ftp://rostlab.org/pssh2/pdb_full/pdb_full.current.tgz
tar -xvf pdb_full.current.tgz   -C /mnt/data/hhblits/
rm pdb_full.current.tgz
