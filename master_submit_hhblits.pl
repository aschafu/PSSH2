#!/usr/bin/perl -w

# master_submit.pl
# Submits HHblits runs for pdb_full to the Rostlab cluster, to run parallelly in portions using arrayjobs.
# Calls scripts/pssh2/write_subjob.sh

use strict;
use warnings;
use POSIX;
use File::Path qw(remove_tree);

my $maxSubjobs = 5000; #number of subjobs in one arrayjob
my $maxSeqPerSubjob = 30; #number of sequences to run in one subjob
my $maxSeqPerArrayJob = $maxSubjobs * $maxSeqPerSubjob; #portion of sequences to run in one arrayjob (= 150000)

my $pdb_full_dir = "/mnt/project/pssh/pdb_full"; 
my $qstat_tmpfile = "$pdb_full_dir/work/qstat.out";
my $subjobs_script = "$pdb_full_dir/scripts/hhblits_sge.sh";
my $subjobs_file = "$pdb_full_dir/work/subjob_tasks.txt";
my $arrayjob_file = "$pdb_full_dir/work/arrayjob.sh";
my $pdbseq_file = "$pdb_full_dir/files/pdbseq_file"; #file with list of all query sequences (pdb sequences)

my $log_dir = "$pdb_full_dir/work/hhblits_log";
remove_tree($log_dir);
mkdir $log_dir;
my $output_dir = "$pdb_full_dir/db";

# PDB list is not toooo long, so we read in everything. Will not work for Swissprot or Trembl!
open SEQS, $pdbseq_file;
my @seqs = <SEQS>;
close SEQS;

#my $size= `wc -l $pdbseq_file`; # size (line number) of $pdbseq_file
my $totalSeqs = $#seqs; # always dealing with array indices here anyway, so don't add one! 

my $arrayJobTextBegin = "#!/bin/bash
# Execute commands parallelly on the cluster:
#\$ -t 1-";
my $arrayJobTextEnd = "TASKS=$subjobs_file
PARAMS=\$(cat \$TASKS | head -n \$SGE_TASK_ID | tail -n 1)
echo \$PARAMS | xargs $subjobs_script 
";

my $nSequence = 0;
my @subjobsLines = ();
COLLECT: while($nSequence <= $totalSeqs){ 
  #submit the next $maxSeqPerArrayJob sequences in one arrayjob in portions of $maxSeqPerSubjob sequences in one subjob -> $maxSeqPerArrayJob/$maxSeqPerSubjob = $maxSubjobs subjobs (5000 subjobs with 30 seq. in each; assume 1job = 4min -> 30jobs = 2h):
  
  my $nLast = $nSequence+$maxSeqPerSubjob;
  if ($nLast > $totalSeqs){$nLast = $totalSeqs};
  my $subJobTasksLine = join " ", chomp(@seqs[$nSequence .. $nLast]);
  $subJobTasksLine .= "\n";
  push @subjobsLines, $subjobTasksLine;
  my $nJobsInCurrentArray = $#subjobsLines + 1;
  
  # if we have all the jobs for one array job (maximal number or every pdb file accounted for), then 
  if ( ($nJobsInCurrentArray >= $maxSubjobs) || ($nLast == $totalSeqs) ){
    # print the tasks-file
    open SUB, ">$subjobs_file"  or die "could not open $subjobs_file for writing";
    print SUB join @subjobsLines;
    close SUB;
    @subjobsLines = ();

    # print the array job file
    open (ARRAY, ">$arrayjob_file") or die "could not open $arrayjob_file for writing";
    print ARRAY $arrayJobTextBegin.$nJobsInCurrentArray."\n".$arrayJobTextEnd;
    close ARRAY;

    # and submit
    my $curr_log_dir = "$log_dir/to$nLast";
    mkdir $curr_log_dir;
    system("qsub -e $curr_log_dir -o /dev/null $arrayjob_file");
    waitUntilReady(); # wait with the submission of the next arrayjob until this is finished

  };    
  $nSequence = $nLast+1; 
  
};


sub waitUntilReady {
	my $qstat_tmpfile = "$pdb_full_dir/work/qstat.out";
	my $qstat_outstring = "";
	do{
        	sleep(3600); #wait 1h
		system("qstat > $qstat_tmpfile");
		open FILE, $qstat_tmpfile or die "Couldn't open file $qstat_tmpfile\n";
		$qstat_outstring = join("", <FILE>);
		chomp($qstat_outstring);
		close FILE;
	}
   	while($qstat_outstring ne "");
}
