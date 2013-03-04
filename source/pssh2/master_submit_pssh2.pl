#!/usr/bin/perl -w

# master_submit.pl
# Submits PSSH2 runs to the Rostlab cluster, to run parallelly in portions using arrayjobs.
# Calls scripts/pssh2/batch_run_generate_pssh.sh (was write_subjob.sh)

use strict;
use warnings;
use POSIX;
use File::Path qw(remove_tree);

my $maxSubjobs = 5000; #number of subjobs in one arrayjob
my $maxSeqPerSubjob = 30; #number of sequences to run in one subjob
#my $n = $subjobs * $seq; #portion of sequences to run in one arrayjob (= 150000)
my $maxSeqPerArrayJob = $maxSubjobs * $maxSeqPerSubjob; #portion of sequences to run in one arrayjob (= 150000)

my $pssh_dir = "/mnt/project/pssh"; 
my $qstat_tmpfile = "$pssh_dir/scripts/qstat.out";
#my $size_file = "$pssh_dir/scripts/md5sums_uniq_size";
my $subjobs_file = "$pssh_dir/work/subjob_tasks.txt";
my $subjobs_script = "$pssh_dir/scripts/batch_run_generate_pssh2.sh";  # TODO!
my $arrayjob_file = "$pssh_dir/work/arrayjob.sh";

my $log_dir = "$pssh_dir/work/pssh2_log";
remove_tree($log_dir);
mkdir $log_dir;
my $output_dir = "$pssh_dir/pssh2_files";
if (-e $output_dir){
  my $time = (stat($output_dir))[9];
  rename $output_dir, $output_dir.".old.".$time;
}
mkdir $output_dir;

#Generate a new the swissprot md5sums file "/mnt/project/pssh/sprot_md5sums_uniq" (like "/mnt/project/mamut/app/sprot")
my $sprot_fasta = "/mnt/project/rost_db/data/swissprot/uniprot_sprot.fasta";
my $md5sums_all = "$pssh_dir/sprot_md5sums_all";
my $md5sums_uniq = "$pssh_dir/sprot_md5sums_uniq";
#system("cat $sprot_fasta | /mnt/project/mamut/bin/fasta_to_md5.rb > $md5sums_all"); 	#done already
#system("cat $md5sums_all | sort | uniq > $md5sums_uniq"); 				#done already

#Generate a new single FASTA files named by the md5sum of the sequence
my $queries_dir = "$pssh_dir/sprot_fastas";
system("mkdir $queries_dir 2>/dev/null");
#system("cd $queries_dir");
#system("cat $sprot_fasta | /mnt/project/mamut/bin/fasta_to_fastas.md5.rb");		#done already

my $totalSeqs_String = `wc -l $md5sums_uniq `; # size (line number) of $md5sums_uniq
my ($totalSeqs, $fileName) = split /\s/, $totalSeqs_String;

my $arrayJobTextBegin = "#!/bin/bash
# Execute commands parallelly on the cluster:
#\$ -t 1-";
my $arrayJobTextEnd = "TASKS=$subjobs_file
PARAMS=\$(cat \$TASKS | head -n \$SGE_TASK_ID | tail -n 1)
echo \$PARAMS | xargs $subjobs_script 
";

open SEQS, $md5sums_uniq; 

print STDOUT "starting job assembly \n";
my $nSequence = 1;
my @subjobsLines = ();
# $totalSeqs counts from 1, so $nSequence has to start at 1, too
COLLECT: while($nSequence <= $totalSeqs){ 
 
 #submit the next $maxSeqPerArrayJob sequences in one arrayjob in portions of $maxSeqPerSubjob sequences in one subjob -> $maxSeqPerArrayJob/$maxSeqPerSubjob = $maxSubjobs subjobs (5000 subjobs with 30 seq. in each; assume 1job = 4min -> 30jobs = 2h):
  
  my $nLast = $nSequence+$maxSeqPerSubjob-1;
  if ($nLast > $totalSeqs){$nLast = $totalSeqs};

#  print STDOUT "next chunk: $nSequence to $nLast \n";
  my $i = $nSequence;
  my @temp = ();
  READ: while ($i <= $nLast){
    my $nextSeq = <SEQS>;
    last READ unless $nextSeq;
    chomp $nextSeq;
    push @temp, $nextSeq;
    $i++;
  }
  if ($i < $nLast){
    print STDERR "Warning: found less sequences ($i) than expected ($nLast) \n";
    $nLast = $i;
  }

  my $subJobNumber = $#subjobsLines + 2; 
  my $subJobTasksLine =  $subJobNumber." ";
  $subJobTasksLine .= join " ", @temp;
  $subJobTasksLine .= "\n";
  push @subjobsLines, $subJobTasksLine;

  # if we have all the jobs for one array job (maximal number or every pdb file accounted for), then 
  if ( ($subJobNumber >= $maxSubjobs) || ($nLast == $totalSeqs) ){

    print STDOUT "$subJobNumber jobs in current array ", $nLast, " is last sequence in this list -> start submission process \n";
    print STDOUT $#subjobsLines+1, " subjob lines found \n";

    if (-e $subjobs_file){
      my $curTime = (stat($output_dir))[9];
      my $oldName = $subjobs_file.".".$curTime.".bkp";
      rename $subjobs_file, $oldName;
    };

    # print the tasks-file
    open SUB, ">$subjobs_file"  or die "could not open $subjobs_file for writing";
    print SUB @subjobsLines;
    close SUB;
    @subjobsLines = ();

    # print the array job file
    open (ARRAY, ">$arrayjob_file") or die "could not open $arrayjob_file for writing";
    print ARRAY $arrayJobTextBegin.$subJobNumber."\n".$arrayJobTextEnd;
    close ARRAY;
    
    print STDOUT "wrote subjobTasks to $subjobs_file and array job script to $subjobs_file, now submitting! \n ";

    # and submit
    my $curr_log_dir = "$log_dir/to$nLast";
    mkdir $curr_log_dir;
    system("qsub -e $curr_log_dir -o /dev/null $arrayjob_file");   #TODO: nice in right way for trembl runs!!!
    waitUntilReady(); # wait with the submission of the next arrayjob until this is finished

  };    
  $nSequence = $nLast+1; 
  
};


sub waitUntilReady {
	my $pssh_dir = "/mnt/project/pssh"; 
	my $qstat_tmpfile = "$pssh_dir/work/qstat.out";
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
