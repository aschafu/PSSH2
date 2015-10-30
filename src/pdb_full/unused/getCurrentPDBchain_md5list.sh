#!/bin/tcsh

# This is more meant to be a HOWTO than a real script! --> use as prototype for running your stuff

# After pdb at rostlab has been updated:
# Update PDB database in mysql:
cd $Aquaria/fromSparkleshare/Aquaria/work/PDB/
rsync -rlt -v -z --delete --port=33444 rsync.wwpdb.org::ftp_data/biounit/coordinates/divided/ ./biounit/ >& rsync.log &
ln -s /mnt/project/rost_db/data/pdb/entries/ /var/tmp/Data/PDB/structures
ln -s $Aquaria/fromSparkleshare/Aquaria/work/PDB/biounit/ /var/tmp/Data/PDB/biounit
../../src/PDB/Update.pl -v -d 2 -s > & Update.20150811.log &

# create a temporary table in Aquaria MYSQL:
# create table tmp_pdb_chain_clean_seqres as select `MD5_Hash`, group_concat(pdb_id, `Chain` separator ', ') as pdb_ids, SEQRES, length,  Replace (SEQRES, "X", "") as clean_seqres, length(Replace (SEQRES, "X", "")) as c_length,  ((length - length(Replace (SEQRES, "X", ""))) / length) as x_ratio from PDB_chain where type='Protein' and length>10 group by `MD5_Hash`;
DB.aquaria_local "select MD5_Hash from tmp_pdb_chain_clean_seqres t where t.x_ratio < 0.5 and t.c_length > 10" > pdbChain.uniq.xlt50.clgt10.20150811.md5