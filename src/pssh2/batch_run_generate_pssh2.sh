#!/bin/bash
## to be executed by SGE on cluster-nodes as a single arrayjob unit
## this just needs the md5sums 

subjob_nr=$1
shift
tmp_hhblits="/tmp/pssh/hhblits_files/$subjob_nr"
mkdir -p $tmp_hhblits 2>/dev/null
tmp_pssh2="/tmp/pssh/pssh2_files/$subjob_nr"
mkdir -p $tmp_pssh2 2>/dev/null
out_pssh2="/mnt/project/pssh/pssh2_files"

/mnt/project/pssh/pdb_full/scripts/fetch_pdb_full_hhblits_pssh.pl 
#(for pssh/pdb_full/db copy) 
thisdate=`date +%s`
out_file="$tmp_pssh2/$subjob_nr.$thisdate"
# we do not need to check for the subjob_nr, since we shifted that away
time (
for md5sum in $* ; do
    echo $md5sum
    /mnt/project/pssh/scripts/generate_pssh2.pl -m $md5sum -t $tmp_hhblits -o $tmp_pssh2
# concatenate the parsed output files into one file with the subjob number
    cat "$tmp_pssh2/$md5sum-pssh2_db_entry" >> $out_file 
done
)
# gzip the subjob otput file and copy it to $out_pssh2
zip_file="$out_file.gz" 
gzip -c $out_file > $zip_file
cp "$zip_file" $out_pssh2
