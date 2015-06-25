#!/bin/bash

counts=`zcat query.uniprot20.hhr.gz | $PSSH/src/util/countHHblitsHits.pl`
stamp=`stat -c%Y query.uniprot20.hhr.gz`
md5=`fasta_to_md5 query.fasta`
DB.aquaria_local "insert into hhblits_family_counts_201506 set md5=\"$md5\" , $counts hh_stamp=$stamp ON DUPLICATE KEY UPDATE $counts hh_stamp=$stamp" 
 