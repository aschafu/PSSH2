#!/usr/bin/perl -w

# generate_pssh2_from_seq.pl
# Makes the two subsequent HHblits runs:
# 1) UniProt Sequence against the UniProt with HHM output (HMM-profile)
# 2) Starting with the HHM output from step 1 against the pdb_full database of profiles with HHR ouput
# and parses the HHR output from the second run using parse_hhr.pl
 
use strict;
use File::chdir;
use Getopt::Long;

# Parse command line parameter
our($i, $t, $o, $h);

my $args_ok = GetOptions(
			'i=s' => \$i, #file with the input sequence
			't=s' => \$t, #path to temporary output (hhm and two hhr files)
			'o=s' => \$o, #path to final output (from parser)
			'h'   => \$h #print help
);
#-------------------------------------------------------------------------------
=head 1 Subroutine print_help
Prints usage help message.
output: stdout
=cut
sub print_help {
print "Usage: /mnt/project/pssh/scripts/generate_pssh2_from_seq.pl
-i <file>\tfile with the input sequence
-t <path>\tpath to temporary output (hhm and two hhr files)
-o <path>\tpath to final output (from parser)
[-h\tprints this help]\n";
}

if($h){
    print_help();
    exit;
}
if(!$i || !$o || !$t){
    print_help();
    exit;	
}
#calculate md5sum of the input sequence and save it in variable $m
my $tmp_md5sum = "tmp_md5sum";
system("cat $i | /mnt/project/mamut/bin/fasta_to_md5.rb > $tmp_md5sum");

open FILE, $tmp_md5sum or die "Couldn't open file $tmp_md5sum\n";
my $m = join("", <FILE>);
close FILE;
system("rm $tmp_md5sum");
chomp $m;
#print $m."\n";
#-------------------------------------------------------------------------------
=head 2 Subroutine init
Initiates parameters and HHblits system calls
input: ($in, $out)
output: ($cmd_hhblits1, $cmd_hhblits2, $cmd_parse_hhr)
=cut
sub init {
my ($i, $m, $t, $o) = @_;
print "\nExecuting sub init...\n";

my $uniprot20 = "/var/tmp/rost_db/data/hhblits/uniprot20_current"; #cluster: "/var/tmp/rost_db/data/hhblits/uniprot20_current"; #jobtest: "/mnt/project/rost_db/data/hhblits/uniprot20_current"; # datam for first HHblits run (to build the profile)
my $pdb_full = "/mnt/project/pssh/pdb_full/db/pdb_full"; #<- up-to-date (local: "/var/tmp/rost_db/data/hhblits/pdb_full")
my $ohhm = $t."/".$m."-uniprot20.hhm";
my $ohhr1 = $t."/".$m."-uniprot20.hhr";
my $ohhr = $t."/".$m."-uniprot20-pdb_full.hhr";
my $hit_list = 10000; # used for -B (maximum number of alignments in alignment list) and -Z (maximum number of lines in summary hit list) parameters in the hhr output of the second HHblits run (against pdb_full)
my $parsed_ohhrs = $o."/".$m."-pssh2_db_entry";

my $cmd_hhblits1 = "if [ ! -f $ohhm ] 
then 
	/usr/bin/time /usr/bin/hhblits -i $i -d $uniprot20 -ohhm $ohhm -o $ohhr1 
fi";
my $cmd_hhblits2 = "if [ ! -f $ohhr ] 
then 
	/usr/bin/time /usr/bin/hhblits -i $ohhm -d $pdb_full -n 1 -B $hit_list -Z $hit_list -o $ohhr
fi";

my $cmd_parse_hhr = "/usr/bin/time /mnt/project/pssh/scripts/parse_hhr.pl -i $ohhr -m $m -o $parsed_ohhrs -v";

return ($cmd_hhblits1, $cmd_hhblits2, $cmd_parse_hhr); 
}

print ("\nRunning $i.\n");
my ($cmd_hhblits1, $cmd_hhblits2, $cmd_parse_hhr) = init($i, $m, $t, $o);
#-------------------------------------------------------------------------------
=head 3 Subroutine run_hhblits1
Runs HHblits with the query input sequence and default parameters against uniprot20 with HMM (hhm) output.
input: $cmd_hhblits1
output: HMM (hhm) output and exit status.
=cut
sub run_hhblits1 {
my ($cmd_hhblits1) = @_;
print "\nExecuting sub run_hhblits1...\n";
system($cmd_hhblits1) == 0
	or die "Failed to execute $cmd_hhblits1: $?\n";
#print "Exit run_hhblits1 value= ".$?."\n"; #only to test
return $?;
}

my $exit_run_hhblits1 = run_hhblits1($cmd_hhblits1);
#-------------------------------------------------------------------------------
=head 4 Subroutine run_hhblits2
Runs HHblits with the HMM output as input and default parameters against pdb_full with default (hhr) output. 
input: ($exit_run_hhblits1, $cmd_hhblits2)
output: normal output file (hhr) and exit status.
=cut
sub run_hhblits2 {
my ($exit_run_hhblits1, $cmd_hhblits2) = @_;
print "\nExecuting sub run_hhblits2...\n";
if ($exit_run_hhblits1 == 0){
	system($cmd_hhblits2) == 0
		or die "Failed to execute $cmd_hhblits2: $?\n";
	#print "Exit run_hhblits2 value= ".$?."\n"; #only to test
	return $?;
}else{
	die "run_hhblits1 already exited with an error\n";
	return "-1";
}
}

my $exit_run_hhblits2 = run_hhblits2($exit_run_hhblits1, $cmd_hhblits2);
#------------------------------------------------------------------------------
=head 5 Subroutine parse_hhr
Parses the hhr output of the final HHblits run against pdb_full with parse_hhr.pl to retrieve for each target alignment:
-md5sum of the PDB sequence
-probability
-E-value
-identity
-alignments gapless blocks
input: ($exit_run_hhblits2, $cmd_parse_hhr)
output: output file "pssh2" in $o and exit status
=cut
sub parse_hhr {
my ($exit_run_hhblits2, $cmd_parse_hhr) = @_;
print "\nExecuting parse_hhr.pl...\n";
if ($exit_run_hhblits2 == 0){
	system($cmd_parse_hhr) == 0
		or die "Failed to execute $cmd_parse_hhr: $?\n";
	#print "Exit parse_hhr value= ".$?."\n"; #only to test
	return $?;
}else{
	die "run_hhblits2 already exited with an error\n";
	return "-2";
}
}

my $exit_parse_hhr = parse_hhr($exit_run_hhblits2, $cmd_parse_hhr);

##Remove hhblits output files:
#system("rm ".$t."/".$m."*");

print "\nFinished successfully $m.\n";
