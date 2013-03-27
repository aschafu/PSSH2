#!/usr/bin/perl -w

# master_submit.pl
# Submits PSSH2 runs to the Rostlab cluster, to run parallelly in portions using arrayjobs.
# Calls scripts/pssh2/write_subjob.sh

use strict;
use warnings;
use POSIX;

my $seq = 10; #number of sequences to run in one subjob

my $pssh_dir = "/mnt/project/pssh";
 
my $tmp_file = "$pssh_dir/scripts/tmp.txt";
my $subjobs_file = "$pssh_dir/scripts/subjobs.sh";
my $arrayjob_file = "$pssh_dir/scripts/arrayjob.sh";

my $log_dir = "$pssh_dir/pssh2_log_debug";
system("mkdir $log_dir 2> /dev/null");
my $output_dir = "$pssh_dir/pssh2_files_debug";
system("mkdir $output_dir 2> /dev/null");

my $md5sums_uniq = "$pssh_dir/sprot_md5sums_uniq";
my $queries_dir = "$pssh_dir/sprot_fastas";

#write the arrayjob script:
open (WRITE, ">".$arrayjob_file) or die "could not open $arrayjob_file for writing";
print WRITE "#!/bin/bash
# Execute commands parallelly on the cluster:
#\$ -t 1-3
CMDFILE=$subjobs_file
PARAMS=\$(cat \$CMDFILE | head -n \$SGE_TASK_ID | tail -n 1)
echo \$PARAMS | xargs /mnt/project/pssh/scripts/write_subjob_debug.sh
";
close WRITE;

#first write the subjobs into the subjobs file:
system("cat $md5sums_uniq | head -n 3810 | tail -n 30 | xargs -n $seq > $tmp_file"); # divide the $n md5sums into blocks of $seq arguments, write to a temporary file
system("i=0; while read line; do let i=i+1; echo \"\$i \$line\"; done < $tmp_file > $subjobs_file");
#submit the arrayjob:
my $curr_log_dir = "$log_dir/redo_127";
system("mkdir $curr_log_dir");
system("qsub -e $curr_log_dir -o /dev/null $arrayjob_file");
