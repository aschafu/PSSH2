#!/usr/bin/perl -w

# generate_pssh2.pl
# Makes the two subsequent HHblits runs:
# 1) UniProt Sequence against the UniProt with HHM output (HMM-profile)
# 2) Starting with the HHM output from step 1 against the pdb_full database of profiles with HHR ouput
# and parses the HHR output from the second run using parse_hhr.pl
 
use strict;
use File::chdir;
use Getopt::Long;

my $queries_dir = "/mnt/project/pssh/sprot_fastas";
my $uniprot20 = "/var/tmp/rost_db/data/hhblits/uniprot20_current"; 
#cluster: "/var/tmp/rost_db/data/hhblits/uniprot20_current"; #jobtest: "/mnt/project/rost_db/data/hhblits/uniprot20_current"; # database for first HHblits run (to build the profile)
my $pdb_full = "/var/tmp/rost_db/data/hhblits/pdb_full";

# Parse command line parameter
our($m, $t, $o, $h);

my $args_ok = GetOptions(
			 'm=s'	=> \$m, #md5sum of the input sequence
			't=s' => \$t, #path to temporary output (hhm and two hhr files)
			'o=s' => \$o, #path to final output (from parser)
			 'h'    => \$h #print help
);
if($h){
    print_help();
    exit;
}
if(!$m){
    print_help();
    exit;	
}

my $i = "$queries_dir/$m"; #input FASTA file named according to the sequence-md5sum 

print ("\nRunning $m.\n");
my ($cmd_hhblits1, $cmd_hhblits2, $cmd_parse_hhr) = init($i, $m, $t, $o);
my $exit_run_hhblits1 = run_hhblits1($cmd_hhblits1);
my $exit_run_hhblits2 = run_hhblits2($exit_run_hhblits1, $cmd_hhblits2);
my $exit_parse_hhr = parse_hhr($exit_run_hhblits2, $cmd_parse_hhr);

print "\nFinished successfully $m.\n";



#-------------------------------------------------------------------------------
=head 1 Subroutine print_help
Prints usage help message.
output: stdout
=cut
sub print_help {
  print "Usage: /mnt/project/pssh/scripts/generate_pssh2.pl
-m <md5sum>\tmd5sum of the input sequence
[-h\tprints this help]\n";
}

#-------------------------------------------------------------------------------
=head 2 Subroutine init
Initiates parameters and HHblits system calls
input: ($in, $out)
output: ($cmd_hhblits1, $cmd_hhblits2, $cmd_parse_hhr)
=cut
sub init {
  my ($i, $m, $t, $o) = @_;
  print "\nExecuting sub init...\n";

  my $ohhm = $t."/".$m."-uniprot20.hhm";
  my $ohhr1 = $t."/".$m."-uniprot20.hhr";
  my $ohhr = $t."/".$m."-uniprot20-pdb_full.hhr";
  my $hit_list = 10000; # used for -B (maximum number of alignments in alignment list) and -Z (maximum number of lines in summary hit list) parameters in the hhr output of the second HHblits run (against pdb_full)
  my $parsed_ohhrs = $o."/".$m."-pssh2_db_entry";
  my $time_log = "/mnt/project/pssh/pssh2_log/time";
  
  my $cmd_hhblits1 = "(/usr/bin/time /usr/bin/hhblits -i $i -d $uniprot20 -ohhm $ohhm -o $ohhr1) 2>> $time_log"."_hhblits1";
  my $cmd_hhblits2 = "(/usr/bin/time /usr/bin/hhblits -i $ohhm -d $pdb_full -n 1 -B $hit_list -Z $hit_list -o $ohhr) 2>> $time_log"."_hhblits2"; 
  my $cmd_parse_hhr = "(/usr/bin/time /mnt/project/pssh/scripts/parse_hhr.pl -i $ohhr -m $m -o $parsed_ohhrs) 2>> $time_log"."_parse_hhr";
  
  return ($cmd_hhblits1, $cmd_hhblits2, $cmd_parse_hhr); 
}

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
  return $?;
}

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
	return $?;
  }else{
    die "run_hhblits1 already exited with an error\n";
    return "-1";
  }
}

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
	  or die "Hoppla! Failed to execute $cmd_parse_hhr: $?\n";
	return $?;
      }else{
	die "run_hhblits2 already exited with an error\n";
	return "-2";
      }
}

