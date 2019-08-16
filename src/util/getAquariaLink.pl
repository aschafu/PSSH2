#!/usr/bin/perl -w
use strict;
use warnings;
use Getopt::Long;
use DBI;

# This script goes to the Aquaria database on AWS to check for matches in Aquaria and gives back links to Aquaria based on sequence MD5

our($dbg,$md5);
my $args_ok=GetOptions( 'md5=s'    =>  \$md5,
			'debug'       => \$dbg,
);

exit(255) unless (defined $md5);

my @accessions = getUniprotAccFromAquaria($md5);
if (defined $accessions[0]){
    foreach my $acc(@accessions){
	print "http://aquaria.ws/$acc?features=https%3A%2F%2Frostlab.org%2Fservices%2Faquaria%2Fsnap4aquaria%2Fjson.php%3FuniprotAcc%3D$acc \n";
    }
}
else {
    print "";
}

sub getUniprotAccFromAquaria{

    my ($sequenceMD5) = @_;

    my $dbname = 'aquaria';
    my $host='database.aquaria.ws';
    my $db_user='read_only';
    my $db_pass='Aquaria_4_the_win!';

    # if ($debug) {print "\nOpen connection to database\n\n"};
    my $dbh=DBI->connect("DBI:mysql:$dbname:$host;mysql_local_infile=1", $db_user, $db_pass, {'mysql_enable_utf8'=>1});
    my $sth=$dbh->prepare("select s.Primary_Accession from protein_sequence s where s.MD5_Hash = '$sequenceMD5' and exists (select * from PSSH2 p where p.Protein_sequence_hash=s.MD5_Hash);")  or die "SQL Error: $DBI::errstr\n";
    $sth->execute();
    my $acc_result_ref = $sth->fetchall_arrayref([0]);    # get array of results
    my @accessions=();
    foreach my $r (@{$acc_result_ref}){
	my $acc = $r->[0];
	if ($dbg){
	    print $acc, "\n";
	}
	push @accessions, $acc;
    }
    return @accessions;

}
