#!/bin/bash

if [ -s $conf_file ]
then
	source $conf_file
fi

# we should get the dbDate as an argument
dbDate=$1

if [ -z $dbDate ]
then
	dbDate='current'
fi

# process downloaded data on AWS node
/usr/share/hhsuite/bin/ffindex_build pdb_full_a3m.ffdata pdb_full_a3m.ffindex a3m/
/usr/share/hhsuite/bin/ffindex_build pdb_full_hhm.ffdata pdb_full_hhm.ffindex hhm/
LC_ALL=C sort pdb_full_hhm.ffindex > pdb_full_hhm.ffindex.simpleSort
LC_ALL=C sort pdb_full_a3m.ffindex > pdb_full_a3m.ffindex.simpleSort
mv pdb_full_a3m.ffindex pdb_full_a3m.ffindex.orig
mv pdb_full_hhm.ffindex pdb_full_hhm.ffindex.orig
ln -s pdb_full_a3m.ffindex.simpleSort pdb_full_a3m.ffindex
ln -s pdb_full_hhm.ffindex.simpleSort pdb_full_hhm.ffindex
export OMP_NUM_THREADS=$(nproc)
/usr/share/hhsuite/bin/cstranslate  -A /usr/share/hhsuite/data/cs219.lib -D /usr/share/hhsuite/data/context_data.lib -x 0.3 -c 4 -f -i pdb_full_a3m -o pdb_full_cs219 -I a3m -b
tar -h --transform 's,^,pdb_full_$dbDate/,' --show-transformed-names - -cvzf pdb_full.tgz pdb_full_a3m.ffdata  pdb_full_a3m.ffindex pdb_full_hhm.ffdata  pdb_full_hhm.ffindex pdb_full_cs219.ffdata  pdb_full_cs219.ffindex
