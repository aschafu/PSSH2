#!/usr/bin/perl -w

# generate_pssh2.pl
# Makes the two subsequent HHblits runs:
# 1) UniProt Sequence against the UniProt with HHM output (HMM-profile)
# 2) Starting with the HHM output from step 1 against the pdb_full database of profiles with HHR ouput
# and parses the HHR output from the second run using parse_hhr.pl
 
use strict;
use File::chdir;
use Getopt::Long;

# PARAMETERS
my $rootDir = "/mnt/project/pssh/pssh2_project/";
my $queries_dir = $rootDir."data/uniprot_derived/sprot_fastas";
my $time_log = $rootDir."work/pssh2_log/time";
my $localHhblitsDir = "/var/tmp/rost_db/data/hhblits/";
my $uniprot20 = $localHhblitsDir."uniprot20_current"; 
my $pdb_full = $localHhblitsDir."pdb_full";
#cluster: "/var/tmp/rost_db/data/hhblits/uniprot20_current"; #jobtest: "/mnt/project/rost_db/data/hhblits/uniprot20_current"; # database for first HHblits run (to build the profile)
my $hit_list = 10000; # used for -B (maximum number of alignments in alignment list) and -Z (maximum number of lines in summary hit list) parameters in the hhr output of the second HHblits run (against pdb_full)
my $hhblits_path = "/usr/bin/hhblits";
my $cache_path = "/usr/bin/ppc_store";
my $parser_path = $rootDir."src/pssh2/parse_hhr.pl";
my $md5script_path = $rootDir."src/pssh2/fasta_to_md5.rb";


# Parse command line parameter
my($m, $i, $t, $o, $h, $d);
my $args_ok = GetOptions(
    'i=s' => \$i, #file name of input sequence
    'm=s' => \$m, #md5sum of the input sequence
    'd=s' => \$d, #directory where the md5sum-named sequence files are stored
    't=s' => \$t, #path to temporary output (hhm and two hhr files)
    'o=s' => \$o, #path to final output (from parser)
    'h'   => \$h #print help
);
if($h){
    print_help();
    exit;
}
if(!($m || $i)){
    print_help();
    exit;	
}
if (defined $i && defined $m){
    print STDERR "WARNING: You gave -i $i and -m $m, will only use $i \n";
    undef $m;
}
if (defined $m){
    if (defined $d){
	$queries_dir = $d;
    }
    else {
	print STDERR "WARNING: You did not provide a directory for the md5sum sequence files. Will use default: $queries_dir \n";
    }
    $i = "$queries_dir/$m"; #input FASTA file named according to the sequence-md5sum 
    unless (-r $i){die "Input sequence file $i not readable! \n"};
}
if (defined $i){
    my $tmp_md5sum = "tmp_md5sum";
    system("cat $i | $md5script_path > $tmp_md5sum");

    open FILE, $tmp_md5sum or die "Generating md5sum, but couldn't open file $tmp_md5sum\n";
    $m = join("", <FILE>);
    close FILE;
    unlink $tmp_md5sum;
    chomp $m;
}
unless (defined $t && -d $t){
    die "temporary hhblits output path $t is not a directory! \n";
}
unless (defined $o && -d $o){
    die "output path for parsed files $o is not a directory! \n";
}

print ("\nRunning $m: $i \n");
my ($cmd_hhblits1, $cmd_hhblits2, $cmd_parse_hhr, $cmd_ppc, $cmd_ppc2) = init($i, $m, $t, $o);
my $exit_run_hhblits1 = run_hhblits1($cmd_hhblits1, $cmd_ppc);
my $exit_run_hhblits2 = run_hhblits2($exit_run_hhblits1, $cmd_hhblits2, $cmd_ppc2);
my $exit_parse_hhr = parse_hhr($exit_run_hhblits2, $cmd_parse_hhr);

print "\nFinished successfully $m.\n";


#-------------------------------------------------------------------------------
=head 1 Subroutine print_help
Prints usage help message.
output: stdout
=cut
sub print_help {
    print "Usage: /mnt/project/pssh/scripts/generate_pssh2.pl
< [ <-m md5sum>  \t md5sum of the input sequence AND
    <-d md5dir> ]\t directory where the md5sum-named sequence files are stored
OR
  [-i fileName] >\t file name containing input sequence
[-t path]\t\t path to temporary output (hhm and two hhr files) 
[-o path]\t\t path to final output (from parser)
[-h]\t\t\t prints this help \n";
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
    my $oa3m1 = $t."/".$m."-uniprot20.a3m";
    my $ohhr = $t."/".$m."-uniprot20-pdb_full.hhr";
    my $oa3m = $t."/".$m."-uniprot20-pdb_full.a3m";
    my $parsed_ohhrs = $o."/".$m.".pssh2";
    my $cmd_hhblits1 = "(/usr/bin/time ".$hhblits_path." -i $i -d $uniprot20 -ohhm $ohhm -oa3m $oa3m1 -o $ohhr1) 2>> $time_log"."_hhblits1";
    my $cmd_hhblits2 = "(/usr/bin/time ".$hhblits_path." -i $ohhm -d $pdb_full -n 1 -B $hit_list -Z $hit_list -o $ohhr) 2>> $time_log"."_hhblits2"; 
    my $cmd_parse_hhr = "(/usr/bin/time ".$parser_path." -i $ohhr -m $m -o $parsed_ohhrs) 2>> $time_log"."_parse_hhr";
    my $cmd_ppc = $cache_path." --seqfile $i --method=hhblits,db=uniprot20,res_hhblits_hhm=$ohhm,res_hhblits_hhr=$ohhr1,res_hhblits_a3m=$oa3m1";
    my $cmd_ppc2 = $cache_path." --seqfile $i --method=hhblits,db=pdb_full,res_hhblits_hhr=$ohhr";
    
    return ($cmd_hhblits1, $cmd_hhblits2, $cmd_parse_hhr, $cmd_ppc, $cmd_ppc2); 

}

#-------------------------------------------------------------------------------
=head 3 Subroutine run_hhblits1
Runs HHblits with the query input sequence and default parameters against uniprot20 with HMM (hhm) output.
input: $cmd_hhblits1
output: HMM (hhm) output and exit status.
=cut
sub run_hhblits1 {
    my ($cmd_hhblits1,$cmd_ppc) = @_;
    print "\nExecuting sub run_hhblits1...\n";
    system($cmd_hhblits1) == 0
	or die "Failed to execute $cmd_hhblits1: $?\n";
# store the output hmm in ppcache
    my $exitVal = $?;
    print STDOUT $cmd_ppc, "\n";
    system($cmd_ppc) == 0 
	or  print STDERR "WARNING: caching failed: $cmd_ppc";
    return $exitVal;
}

#-------------------------------------------------------------------------------
=head 4 Subroutine run_hhblits2
Runs HHblits with the HMM output as input and default parameters against pdb_full with default (hhr) output. 
input: ($exit_run_hhblits1, $cmd_hhblits2)
output: normal output file (hhr) and exit status.
=cut
sub run_hhblits2 {
    my ($exit_run_hhblits1, $cmd_hhblits2,$cmd_ppc2) = @_;
    my $exitVal;
    print "\nExecuting sub run_hhblits2...\n";
    if ($exit_run_hhblits1 == 0){
	system($cmd_hhblits2) == 0
	    or die "Failed to execute $cmd_hhblits2: $?\n";
	$exitVal = $?;
	print STDOUT $cmd_ppc2, "\n";
	system($cmd_ppc2) == 0
	    or  print STDERR "WARNING: caching failed: $cmd_ppc2";
    }else{
	die "run_hhblits1 already exited with an error\n";
	return "-1";
    }
    return $exitVal;
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

