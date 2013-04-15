#!/usr/bin/perl -w

# go over output files and check which md5 matches are duplicates 
# (check combi of sequence, structure, repeat)

use strict;
use warnings;
use Getopt::Long;
use IO::Uncompress::Gunzip qw($GunzipError);
use Cwd qw(abs_path);


my($d,$h);

my $args_ok = GetOptions(
    'd=s' => \$d, #directory to check
    'h'   => \$h #print help
    );
if($h){
    print_help();
    exit;
}

opendir DIR, $d;
my @pssh2_files = sort(map "$d/$_", grep /\.pssh2.gz$/, readdir DIR); 
closedir DIR;

my %seenBefore;

foreach my $file(@pssh2_files){

    if (-l $file){
	$file = abs_path($file);
    }

    my $z = IO::Uncompress::Gunzip->new( $file ) or die "IO::Uncompress::Gunzip failed: $GunzipError\n";
    while (<$z>){
	my $line = $_;
	my ($found_md5_seq,$found_md5_struc,$repeat,@data) = split /\,/, $line;
	my $found = $found_md5_seq.','.$found_md5_struc.','.$repeat;
	if (defined $seenBefore{$found}){
	     $seenBefore{$found} .= ':'.$file;
	     print STDOUT $seenBefore{$found}, "\n";
	}
	else {
	    $seenBefore{$found} = $found.':'.$file;
	}
    }
    close $z;     
    
}



sub print_help {

    print "Usage: find_duplicate_md5_pssh2_output.pl
<-d path>\t directory to check for duplicates
[-h]\t\t\t prints this help \n";


}
