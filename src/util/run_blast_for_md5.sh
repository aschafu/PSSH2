#!/bin/bash
#$ -o /mnt/project/pssh/pssh2_project/work/blast_log/
#$ -e /mnt/project/pssh/pssh2_project/work/blast_log/


# take the md5 sum given on the input and run a blast for it -- taking advantage of PredictProtein files if possible

md5=$1

### full path to cachedir
pathPssh=`/mnt/project/pssh/pssh2_project/src/util/find_cache_path -m $md5`
echo $pathPssh
cd $pathPssh

# find check file
pathPPchk=`ppc_fetch --seqfile query.fasta | grep chk`
echo $pathPPchk

if [[ -z $pathPPchk ]];
then
    blastpgp -F F -j 3 -b 3000 -e 1 -h 1e-3 -d /mnt/project/rost_db/data/big/big_80 -i query.fasta -o query.big80.blastPsiOut -C query.chk 
else 
    ln -s $pathPPchk query.chk
fi
blastpgp -F F -b 100000 -e 10 -d /mnt/project/rost_db/data/big/big -i query.fasta -o query.big.blastPsiOut -R query.chk
#rm query.chk
gzip query.big.blastPsiOut


