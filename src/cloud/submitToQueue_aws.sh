#!/bin/bash
echo 'start this with nohup to make sure that it continues if the ssh dies!'
# get the md5 sums to submit
~/git/PSSH2/src/util/DB.pssh2_local "select MD5_Hash from tmp_pdb_chain_clean_seqres_201709 t where t.x_ratio < 0.5 and t.c_length > 10" > pdbChain.uniq.xlt50.clgt10.201709.md5
for md5 in `tail -n +1 pdbChain.uniq.xlt50.clgt10.201709.md5` ; do echo $md5; aws --region=$REGION sqs send-message --queue-url https://sqs.$REGION.amazonaws.com/$ACCOUNT/build_hhblits_structure_profiles --message-body $md5; done
