#!/bin/bash

counts=`zcat query.uniprot20.hhr.gz | $PSSH/src/util/countHHblitsHits.pl`
stamp=`stat -c%Y query.uniprot20.hhr.gz`
md5=`fasta_to_md5 query.fasta`
DB.pssh2_local "insert into hhblits_family_counts set md5=\"$md5\" , $counts hh_stamp=$stamp ON DUPLICATE KEY UPDATE $counts hh_stamp=$stamp" 

# to do this for many md5 sums, you can do this on the shell:
# foreach md5 ( ` tail -n +2 swissprot.20150610.uniq.md5 | head` )
# foreach? echo $md5
# foreach? cd `$PSSH/src/util/find_cache_path -m $md5`
# foreach? pwd
# foreach? $PSSH/src/util/DB_insert_countHHblitsHits.sh
# foreach? cd -
# foreach? end 