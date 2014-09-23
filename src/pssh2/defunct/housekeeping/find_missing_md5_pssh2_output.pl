#!/usr/bin/perl -w

# collect md5 sums that should have run (subjob_tasks file) but are not present in output
# ouput can be directly used for resubmission in master_submit... (e.g. with bigger memory option)

use strict;
use warnings;
use Getopt::Long;
use IO::Uncompress::Gunzip qw($GunzipError);



my($a,$t,$p,$h);

my $args_ok = GetOptions(
    'a=s' => \$a, #array job number we are testing
    't=s' => \$t, #task file with md5 sums to run
    'p=s' => \$p, #path to output files
    'h'   => \$h #print help
    );
if($h){
    print_help();
    exit;
}

my $prettyA = sprintf("%03d", $a );

open (TASKS, $t) or die "Can't read taks file: $t";

 TASK: while (<TASKS>){
     
     my @md5 = split " ";
     my $subjob = shift @md5;
#     print STDOUT "testing subjob $subjob md5 sums: ", join " ", @md5, "\n"; 
     my $task_output_file = $p."/".$prettyA."_".$subjob.".pssh2.gz";
     if (! ($subjob % 100) ){
	 print STDERR "read $task_output_file \n";
     }
     my %matched;
     foreach my $md(@md5){
	 $matched{$md} = 0;
     }

     unless (-r $task_output_file){
	 print STDERR "ERROR: $task_output_file is not readable \n";
	 next TASK;
     }
     my $z = IO::Uncompress::Gunzip->new( $task_output_file ) or die "IO::Uncompress::Gunzip failed: $GunzipError\n";
     while (<$z>){
	 my $line = $_;
	 my ($found_md5,@data) = split /\,/, $line;
	 $matched{$found_md5} = 1;
     }
     close $z;

     foreach my $md(sort keys %matched){
	 unless ($matched{$md}) {print STDOUT $md, "\n"};
     }

}
close TASKS;




sub print_help {

    print "Usage: find_missing_md5_pssh2_output.pl
<-a num>\t number of array job we are testing  
<-t num>\t task file with md5 sums to run     
<-p num>\t path to output files
[-h]\t\t\t prints this help \n";


}
