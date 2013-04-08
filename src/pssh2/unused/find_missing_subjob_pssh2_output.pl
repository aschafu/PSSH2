#!/usr/bin/perl -w

# collect subjob ids of failed subjobs

use strict;
use warnings;
use Getopt::Long;

my($a,$s,$l,$h);

my $args_ok = GetOptions(
    'a=s' => \$a, #number of array jobs
    's=s' => \$s, #number of sub jobs per array job
    'l=s' => \$l, #number of last subjob
    'h'   => \$h #print help
    );
if($h){
    print_help();
    exit;
}

my $ia;
my $is;
my $lastS;
for ($ia=1; $ia<=$a; $ia++){
    if ($ia == $a){
	$lastS = $l;
    }
    else {
	$lastS = $s;
    }
    my $prettyA = sprintf("%03d", $ia );
    
  FILE: for ($is=1; $is<=$lastS; $is++){
	
	my $prettyS =  sprintf("%04d", $is);
	my $fileName = $prettyA."_".$prettyS.".pssh2.gz";
	unless (-e $fileName){
	    print STDOUT "missing: ", $fileName, "\n";
	    next FILE;
	}
	unless (-s $fileName){
	    print STDOUT "empty: ", $fileName, "\n"; 
	}

    }
}





sub print_help {

    print "Usage: find_missing_subjob_pssh2_output.pl
<-a num>\t number of array jobs  
<-s num>\t number of sub jobs per array job
<-l num>\t number of last subjob  
[-h]\t\t\t prints this help \n";


}
