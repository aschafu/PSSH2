#!/usr/bin/perl -w

# master_submit.pl <flag_file> [pdbseq_file] [input_dir] [output_dir]
# Submits HHblits runs for pdb_full to the Rostlab cluster, to run parallelly in portions using arrayjobs.
# Calls scripts/pssh2/write_subjob.sh

use strict;
use warnings;
use POSIX;
use File::Path qw(remove_tree);

# PARAMETERS!
my $project_dir = "/mnt/project/pssh/pssh2_project"; 
my $maxSubjobs = 5000; #number of subjobs in one arrayjob
my $maxSeqPerSubjob = 30; #number of sequences to run in one subjob
my $maxSeqPerArrayJob = $maxSubjobs * $maxSeqPerSubjob; #portion of sequences to run in one arrayjob (= 150000)


my $flag_file = "";
$flag_file = $ARGV[0];
unless (-e $flag_file){die "ERROR: $flag_file does not exist! \n"};
unless (-w $flag_file){print STDERR "WARNING: $flag_file not writable! \n"};
my $pdbseq_file = $project_dir."/data/pdb_derived/pdbseq_file"; #file with list of all query sequences (pdb sequences)
if (defined $ARGV[1] && $ARGV[1]){
    $pdbseq_file = $ARGV[1];
}
my $seq_dir = $project_dir."/data/pdb_derived/seq";
if (defined $ARGV[2] && $ARGV[2]){
    $seq_dir = $ARGV[2];
}
unless (-d $seq_dir){print STDERR "WARNING: seq directory $seq_dir is not a directory! \n"}
my $a3m_dir = $project_dir."/data/pdb_derived/a3m";
if (defined $ARGV[3] && $ARGV[3]){
    $a3m_dir = $ARGV[3];
}
unless (-d $a3m_dir){print STDERR "WARNING: a3m directory $a3m_dir is not a directory! \n"}
#print STDOUT join " ", "settings: ", $pdbseq_file, $seq_dir, $a3m_dir, "\n";

# PARAMETERS!
my $src_dir = $project_dir."/src/pdb_full";
my $subjobs_script = $src_dir."/hhblits_sge.sh";
my $work_dir = $project_dir."/work";
my $qstat_tmpfile = $work_dir."/qstat.out";
my $subjobs_file = $work_dir."/subjob_tasks.txt";
my $arrayjob_file = $work_dir."/arrayjob.sh";
# flag_file is now passed as parameter
#my $flag_file = $work_dir."master_submit_hhblits.DO_NOT_REMOVE.flag";

my $log_dir = $work_dir."/hhblits_log";
remove_tree($log_dir);
mkdir $log_dir;

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
echo \$PARAMS | xargs $subjobs_script $seq_dir $a3m_dir $log_dir
";
# hhblits_sge.sh expects paths for input seq (I), ouput a3m files (O), temporary hhblits files (T) as input

print STDOUT "starting job assembly";
my $nSequence = 0;
my @subjobsLines = ();
COLLECT: while($nSequence <= $totalSeqs){ 
  #submit the next $maxSeqPerArrayJob sequences in one arrayjob in portions of $maxSeqPerSubjob sequences in one subjob -> $maxSeqPerArrayJob/$maxSeqPerSubjob = $maxSubjobs subjobs (5000 subjobs with 30 seq. in each; assume 1job = 4min -> 30jobs = 2h):
  
  my $nLast = $nSequence+$maxSeqPerSubjob;
  if ($nLast > $totalSeqs){$nLast = $totalSeqs};

#  print STDOUT "next chunk: $nSequence ",  $seqs[$nSequence], " to $nLast",  $seqs[$nLast], " \n";
  my @temp = (@seqs[$nSequence .. $nLast]);
  chomp  @temp;

  my $subJobTasksLine = join " ", @temp;
  $subJobTasksLine .= "\n";
  push @subjobsLines, $subJobTasksLine;
  my $nJobsInCurrentArray = $#subjobsLines + 1;
  
  # if we have all the jobs for one array job (maximal number or every pdb file accounted for), then 
  if ( ($nJobsInCurrentArray >= $maxSubjobs) || ($nLast == $totalSeqs) ){

    print STDOUT "$nJobsInCurrentArray jobs in current array, $nLast is last sequence in this list -> start submission process \n";
    print STDOUT "$#subjobsLines subjob lines found \n";

    # print the tasks-file
    open SUB, ">$subjobs_file"  or die "could not open $subjobs_file for writing";
    print SUB @subjobsLines;
    close SUB;
    @subjobsLines = ();

    # print the array job file
    open (ARRAY, ">$arrayjob_file") or die "could not open $arrayjob_file for writing";
    print ARRAY $arrayJobTextBegin.$nJobsInCurrentArray."\n".$arrayJobTextEnd;
    close ARRAY;
    
    print STDOUT "wrote subjobTasks to $subjobs_file and array job script to $subjobs_file, now submitting! \n ";

    # and submit
    my $curr_log_dir = "$log_dir/to$nLast";
    mkdir $curr_log_dir;
    system("qsub -e $curr_log_dir -o /dev/null $arrayjob_file");
    waitUntilReady($qstat_tmpfile); # wait with the submission of the next arrayjob until this is finished

  };    
  $nSequence = $nLast+1; 
  
};

unlink $flag_file;


sub waitUntilReady {

    my ($qstat_tmpfile) = $@;
    my $qstat_outstring = "";
    do{
	sleep(600); #wait 10 min
	system("qstat > $qstat_tmpfile");
	open FILE, $qstat_tmpfile or die "Couldn't open file $qstat_tmpfile\n";
	$qstat_outstring = join("", <FILE>);
	chomp($qstat_outstring);
	close FILE;
    }
    while($qstat_outstring ne "");
}
