#!/usr/bin/perl -w

# master_submit.pl
# Submits PSSH2 runs to the Rostlab cluster, to run parallelly in portions using arrayjobs.
# Calls scripts/pssh2/batch_run_generate_pssh.sh (was write_subjob.sh)

use strict;
use warnings;
use POSIX;
use File::Path qw(remove_tree);
use File::Basename;
use Getopt::Long;
#use Cwd 'abs_path';
#use Cwd;

# PARAMETERS!
my $maxSubjobs = 5000; #number of subjobs in one arrayjob
my $maxSeqPerSubjob = 20; #number of sequences to run in one subjob
#my $n = $subjobs * $seq; #portion of sequences to run in one arrayjob (= 150000)
my $maxSeqPerArrayJob = $maxSubjobs * $maxSeqPerSubjob; #portion of sequences to run in one arrayjob (= 150000)

my $pssh_dir = "/mnt/project/pssh/pssh2_project"; 
my $work_dir = $pssh_dir."/work";
my $src_dir =  $pssh_dir."/src/pssh2";
my $data_dir = $pssh_dir."/data";
my $output_dir = $data_dir."/pssh2/";
my $seq_dir = $data_dir."/uniprot_derived";
my $qstat_tmpfile = "$work_dir/qstat.out";
#my $size_file = "$pssh_dir/scripts/md5sums_uniq_size";
my $subjobs_file_path = "$work_dir/subjob_tasks";
my $arrayjob_file = "$work_dir/arrayjob.sh";
my $subjobs_script = "$src_dir/batch_run_generate_pssh2.sh";  # TODO!
my $fasta_to_md5_script = "$src_dir/fasta_to_md5.rb";
my $split_fasta_md5_script = "$src_dir/fasta_to_fastas.md5.rb";
my $big_option = " -q generic\@n37.rostclust";
#my $sprot_fasta = "/mnt/project/rost_db/data/swissprot/uniprot_sprot.fasta";

my($o,$s,$h,$r,$qb);
$r = "";
$qb = 0;
my $args_ok = GetOptions(
    'o=s' => \$o, #name of pssh2 output subdirectory
    's=s' => \$s, #path of sequence database to work with
    'r=s' => \$r, #resubmit
    'qb'  => \$qb, # use queue for big jobs only
    'h'   => \$h #print help
    );
if($h||!$s || !$o){
    print_help();
    exit;
}
if ($r){
    print STDOUT "resubmitting -> will not regenerate the fasta sequences \n";
    unless (-r $r){die "uniq md5 list $r not readable!"}
}
my $big_hhblits = " s ";
if ($qb){
    print STDOUT "will add '$big_option' to the queue submission -> less nodes, but hopefully more memory per job, fewer squences per job \n";
    print STDOUT "will pass on -b to generate_pssh.pl (via $subjobs_script ) \n";
    $big_hhblits = " b ";
    $maxSeqPerSubjob = 5;
}
unless (defined $o){
    my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime(time);
    $year += 1900;
    $mon += 1;
    $o = $year.$mon.$mday;
    print STDERR "WARNING: You did not give a name for the output subdir. Will use $o \n";
}
$output_dir .= $o;

my $fasta_input;
my $input_name;
if (defined $s && -r $s){
    $fasta_input = File::Spec->rel2abs($s);
    my ($path,$suffix);
    ($input_name,$path,$suffix) = fileparse($fasta_input,qr/\.[^.]*/);
    print STDOUT "Parsed name $fasta_input: ", join " ", ($input_name,$path,$suffix,"\n"); 
}
else {
    die "Sequence input $s not defined or not readable! \n";
};

my $log_dir = "$work_dir/pssh2_log";
unless ($r){
    remove_tree($log_dir);
    mkdir $log_dir;
};

print STDOUT "Will write output to $output_dir \n";
unless ($r){
    mkdir $output_dir;
}

#Generate a new the  md5sums file "$pssh_dir/sprot_md5sums_uniq" (like "/mnt/project/mamut/app/sprot")
my $md5sums_uniq;
if ($r){
    $md5sums_uniq = $r;
    print STDOUT "Working with md5sums files $md5sums_uniq; will assume that the single fasta sequences already exist! \n";
}
else {
    my $md5sums_all = $seq_dir."/".$input_name.".md5sums_all";
    $md5sums_uniq = $seq_dir."/".$input_name.".md5sums_uniq";
    print STDOUT "Making md5sums files $md5sums_all, $md5sums_uniq \n";
    system("cat $fasta_input | $fasta_to_md5_script > $md5sums_all"); 
    system("cat $md5sums_all | sort | uniq > $md5sums_uniq"); 	
}

#Generate a new single FASTA file named by the md5sum of the sequence
my $queries_dir = $seq_dir."/".$input_name."_single_fastas";
my $current_dir = getcwd;
if ($r){
    print STDOUT "Working with split md5sum files in $queries_dir, staying in $current_dir \n";
}
else {
    print STDOUT "Currently in $current_dir, changing to $queries_dir \n";
    mkdir $queries_dir;
    chdir $queries_dir;
    system("cat $fasta_input | $split_fasta_md5_script ");	
    chdir $current_dir;
    print STDOUT "Made split md5sum files in $queries_dir, changing back to $current_dir \n";
};

my $totalSeqs_String = `wc -l $md5sums_uniq `; # size (line number) of $md5sums_uniq
my ($totalSeqs, $fileName) = split /\s/, $totalSeqs_String;
print STDOUT "Found $totalSeqs sequences to work with \n";

my $arrayJobTextBegin = "#!/bin/bash
# Execute commands parallelly on the cluster:
#\$ -t 1-";
my $arrayJobTextMiddle = "TASKS=";
#my $arrayJobTextEnd = "TASKS=$subjobs_file
my $arrayJobTextEnd = "PARAMS=\$(cat \$TASKS | head -n \$SGE_TASK_ID | tail -n 1)
echo \$PARAMS | xargs $subjobs_script $big_hhblits $queries_dir $output_dir "; 

open SEQS, $md5sums_uniq; 

print STDOUT "starting job assembly \n";
my $nSequence = 1;
my $nArray = 0;
#my $previous_lastSubjobNumber = 0;
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
  my $pretty_subJobNumber = sprintf("%04d", $subJobNumber);
  my $subJobTasksLine =  $pretty_subJobNumber." ";
  $subJobTasksLine .= join " ", @temp;
  $subJobTasksLine .= "\n";
  push @subjobsLines, $subJobTasksLine;

  # if we have all the jobs for one array job (maximal number or every pdb file accounted for), then 
  if ( ($subJobNumber >= $maxSubjobs) || ($nLast == $totalSeqs) ){

      $nArray++;
      my $pretty_nArray = sprintf("%03d", $nArray );
      print STDOUT "$subJobNumber jobs in current array (number $pretty_nArray); $nLast is last sequence in this list -> start submission process \n";
      print STDOUT $#subjobsLines+1, " subjob lines found \n";

      my $subjobs_file = $subjobs_file_path.".".$pretty_nArray.".txt";

      # print the tasks-file
      open SUB, ">$subjobs_file"  or die "could not open $subjobs_file for writing";
      print SUB @subjobsLines;
      close SUB;
      @subjobsLines = ();
      
      # print the array job file
      open (ARRAY, ">$arrayjob_file") or die "could not open $arrayjob_file for writing";
      print ARRAY $arrayJobTextBegin.$subJobNumber."\n".$arrayJobTextMiddle.$subjobs_file."\n".$arrayJobTextEnd.$pretty_nArray."\n";
      close ARRAY;
      
      print STDOUT "wrote subjobTasks to $subjobs_file and array job script to $arrayjob_file, now submitting! \n ";

      # and submit
      my $curr_log_dir = "$log_dir/$pretty_nArray-subjobs_to$nLast";
      mkdir $curr_log_dir;
      my $qsub_cmd = "qsub -e $curr_log_dir -o /dev/null ";
      if ($qb){
	  $qsub_cmd .= $big_option;
      }
      $qsub_cmd .= " ".$arrayjob_file;
      system($qsub_cmd);   #TODO: nice in right way for trembl runs!!!
      waitUntilReady(); # wait with the submission of the next arrayjob until this is finished
      
  };    
  $nSequence = $nLast+1; 
  
};
print STDOUT "finished: all sequences submitted \n";


sub waitUntilReady {
	my $qstat_tmpfile = "$work_dir/pssh2_qstat.out";
	my $qstat_outstring = "";
	do{
        	sleep(600); #wait 10 min
		system("qstat > $qstat_tmpfile");
		open FILE, $qstat_tmpfile or die "Couldn't open file $qstat_tmpfile\n";
		$qstat_outstring = join("", <FILE>);
		chomp($qstat_outstring);
		close FILE;
	}
   	while($qstat_outstring =~ / qw /);
}

sub print_help {

    print "Usage: master_submit_pssh2.pl
<-o outdir>  \t name of pssh2 output subdirectory
<-s inputdir> ]\t path of sequence database to work with
[-r md5sumsUniq]\t path of file containing uniq md5sums to resubmit
[-qb]\t use only 'big' nodes, so the jobs can have lots of memory
[-h]\t\t\t prints this help \n";


}
