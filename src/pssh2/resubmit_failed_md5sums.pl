#!/usr/bin/perl -w

# resubmit_failed_md5sums.pl
# Resubmits failed PSSH2 runs to the Rostlab cluster, to run parallelly using arrayjob.
# Calls scripts/pssh2/write_subjob.sh

use strict;
use warnings;
use POSIX;

my $pssh_dir = "/mnt/project/pssh"; 
my $qstat_tmpfile = "$pssh_dir/scripts/qstat.out";
my $tmp_file = "$pssh_dir/scripts/tmp.txt";
my $subjobs_file = "$pssh_dir/scripts/subjobs.sh";
my $arrayjob_file = "$pssh_dir/scripts/arrayjob.sh";

my $log_dir = "$pssh_dir/pssh2_log";
my $output_dir = "$pssh_dir/pssh2_files";
my $redo_md5sums_file = "$pssh_dir/scripts/redo_md5sums";

my $size; #actual size of $ redo_md5sums
my $size_file = "$pssh_dir/scripts/redo_md5sums_size";
system("cat $redo_md5sums_file | wc -l > $size_file");
open FILE, $size_file or die "Couldn't open file $size_file\n"; 
$size = join("", <FILE>);
chomp($size); 
close FILE;

my $seq = 30; #run 30 md5sums in one subjob
my $subjobs_size = ceil($size / $seq); #number of subjobs
#write the arrayjob script:
open (WRITE, ">".$arrayjob_file) or die "could not open $arrayjob_file for writing";
print WRITE "#!/bin/bash
# Execute commands parallelly on the cluster:
#\$ -t 1-$subjobs_size
CMDFILE=$subjobs_file
PARAMS=\$(cat \$CMDFILE | head -n \$SGE_TASK_ID | tail -n 1)
echo \$PARAMS | xargs /mnt/project/pssh/scripts/write_subjob.sh
";
close WRITE;

my $subjob_nr = 15112; #first 30-block, because the last one was 15111
#submit the failed sequences in one arrayjob in portions of $seq sequences in one subjob -> $size/$seq subjobs:
#first write the subjobs into the subjobs file:
system("cat $redo_md5sums_file | xargs -n $seq > $tmp_file"); # divide the $size md5sums into blocks of $seq arguments, write to a temporary file
system("i=$subjob_nr; while read line; do let i=i+1; echo \"\$i \$line\"; done < $tmp_file > $subjobs_file");
system("rm $tmp_file");
#submit the arrayjob:
my $curr_log_dir = "$log_dir/redone";
system("mkdir $curr_log_dir");
system("qsub -e $curr_log_dir -o /dev/null $arrayjob_file"); 
   
