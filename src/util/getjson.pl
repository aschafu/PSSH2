#!/usr/bin/perl -w
use strict;
use feature qw(say);
use Getopt::Long;
use lib glob("/mnt/project/snap2web/");
use Snap2Cache;
use DBI;
use Config::Simple;

# now read the local config info
my $cfg = new Config::Simple("Config.ini") || die Config::Simple->error();
my $db_user= $cfg->param('mysql.db_user');
my $db_pass= $cfg->param('mysql.db_pass');
my $host= $cfg->param('mysql.host');
my $seqHashQuery = $cfg->param('mysql.seqHashQuery');


our($seq,$dbg);

my $args_ok=GetOptions( 'seq=s'    =>  \$seq,
                        'debug'       => \$dbg
);

exit(255) unless defined $seq;

my $cache=new Snap2Cache($seq,$dbg);
# array of mutations first pos to all, then 2 pos to all
my @mutants=$cache->allmuts();
# hash for each prediction key e.g. M38A, value 
my %predictions=$cache->predictions();

# significant score:  effect > 40
# significant neutral: <-40

my @result;

# cache complete: check whether all 19 non-native are defined
if ($cache->complete()){
    my $c=0;
    my $r=0;
    foreach my $mut (@mutants) {
        $mut=~/(\w)(\d+)(\w)/o;
        my ($wt,$pos,$var)=($1,$2,$3);
        push @result,'{"col":'.$c.',"row":'.$r.',"label":"'.$wt.'","score":'.$predictions{$mut}.',"mut":"'.$var.'"}';
        if($r==19){
            $c++;
            $r=-1;
        }
        $r++;
    }
}
my $result=join ",",@result;

print "[$result]";
