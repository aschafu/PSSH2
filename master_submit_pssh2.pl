#!/usr/bin/perl -w

# master_submit.pl
# Submits PSSH2 runs to the Rostlab cluster, to run parallelly in portions using arrayjobs.
# Calls scripts/pssh2/write_subjob.sh

use strict;
use warnings;
use POSIX;

my $subjobs = 5000; #number of subjobs in one arrayjob
my $seq = 30; #number of sequences to run in one subjob
my $n = $subjobs * $seq; #portion of sequences to run in one arrayjob (= 150000)

my $pssh_dir = "/mnt/project/pssh"; 
my $qstat_tmpfile = "$pssh_dir/scripts/qstat.out";
my $size_file = "$pssh_dir/scripts/md5sums_uniq_size";
my $tmp_file = "$pssh_dir/scripts/tmp.txt";
my $subjobs_file = "$pssh_dir/scripts/subjobs.sh";
my $arrayjob_file = "$pssh_dir/scripts/arrayjob.sh";

my $log_dir = "$pssh_dir/pssh2_log";
system("rm -r $log_dir 2>/dev/null");
system("mkdir $log_dir 2>/dev/null");
my $output_dir = "$pssh_dir/pssh2_files";
system("rm -r $output_dir 2>/dev/null"); 
system("mkdir $output_dir 2>/dev/null");

#Generate anew the swissprot md5sums file "/mnt/project/pssh/sprot_md5sums_uniq" (like "/mnt/project/mamut/app/sprot")
my $sprot_fasta = "/mnt/project/rost_db/data/swissprot/uniprot_sprot.fasta";
my $md5sums_all = "$pssh_dir/sprot_md5sums_all";
my $md5sums_uniq = "$pssh_dir/sprot_md5sums_uniq";
#system("cat $sprot_fasta | /mnt/project/mamut/bin/fasta_to_md5.rb > $md5sums_all"); 	#done already
#system("cat $md5sums_all | sort | uniq > $md5sums_uniq"); 				#done already

#Generate anew single FASTA files named by the md5sum of the sequence
my $queries_dir = "$pssh_dir/sprot_fastas";
system("mkdir $queries_dir 2>/dev/null");
#system("cd $queries_dir");
#system("cat $sprot_fasta | /mnt/project/mamut/bin/fasta_to_fastas.md5.rb");		#done already

my $size; #actual size of $md5sums_uniq
system("cat $md5sums_uniq | wc -l > $size_file");
open FILE, $size_file or die "Couldn't open file $size_file\n"; 
$size = join("", <FILE>);
chomp($size); 
close FILE;

#write the arrayjob script:
open (WRITE, ">".$arrayjob_file) or die "could not open $arrayjob_file for writing";
print WRITE "#!/bin/bash
# Execute commands parallelly on the cluster:
#\$ -t 1-$subjobs
CMDFILE=$subjobs_file
PARAMS=\$(cat \$CMDFILE | head -n \$SGE_TASK_ID | tail -n 1)
echo \$PARAMS | xargs /mnt/project/pssh/scripts/write_subjob.sh
";
close WRITE;

my $i = $n; #defines end line of $md5sums_uniq for the next portion of $n cmds
my $subjob_nr = 0; #counts the subjobs
while($i <= $size){ 
	#submit the next $n sequences in one arrayjob in portions of $seq sequences in one subjob -> $n/$seq = $subjobs subjobs (5000 subjobs with 30 seq. in each; assume 1job = 4min -> 30jobs = 2h):
	#first write the subjobs into the subjobs file:
	system("cat $md5sums_uniq | head -n $i | tail -n $n | xargs -n $seq > $tmp_file"); # divide the $n md5sums into blocks of $seq=30 arguments, write to a temporary file
	system("i=$subjob_nr; while read line; do let i=i+1; echo \"\$i \$line\"; done < $tmp_file > $subjobs_file");
	#submit the arrayjob:
	my $h = $i - $n + 1; #$h=first subjob, $i=last subjob in the block
	my $curr_log_dir = "$log_dir/$h-$i";
	system("mkdir $curr_log_dir");
	system("qsub -e $curr_log_dir -o /dev/null $arrayjob_file"); #TODO: nice in right way for trembl runs!!!
   
	$subjob_nr = $subjob_nr + $subjobs;
  	$i = $i + $n;
	waitUntilReady(); # wait with the submition of the next arrayjob until this is finished
}

# run the left sequences (less than $n)
my $h = $i - $n + 1; #first subjob in the block
my $last = $size - $h + 1; #number of sequences left to run
if ($last > 0){
	#run the remained sequences:
        system("cat $md5sums_uniq | tail -n $last | xargs -n $seq > $tmp_file");
	system("i=$subjob_nr; while read line; do let i=i+1; echo \"\$i \$line\"; done < $tmp_file > $subjobs_file");
	system("rm $tmp_file");
	$subjobs = ceil($last / $seq);
	
	#rewrite the arrayjob file because $subjobs_file number of lines ($subjobs) changed:	
	open (WRITE, ">".$arrayjob_file) or die "could not open $arrayjob_file for writing";
        print WRITE "#!/bin/bash
# Execute commands parallelly on the cluster:
#\$ -t 1-$subjobs
CMDFILE=$subjobs_file
PARAMS=\$(cat \$CMDFILE | head -n \$SGE_TASK_ID | tail -n 1)
echo \$PARAMS | xargs /mnt/project/pssh/scripts/write_subjob.sh
";
        close WRITE;
	#submit it:
	my $curr_log_dir = "$log_dir/$h-$size";
	system("mkdir $curr_log_dir");
        system("qsub -e $curr_log_dir -o /dev/null $arrayjob_file"); #TODO: nice in right way for trembl!!!
	system("rm $qstat_tmpfile");

	$subjob_nr = $subjob_nr + $subjobs;
	print "last subjob nr $subjob_nr submitted\n";
}

sub waitUntilReady {
	my $pssh_dir = "/mnt/project/pssh"; 
	my $qstat_tmpfile = "$pssh_dir/scripts/qstat.out";
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
