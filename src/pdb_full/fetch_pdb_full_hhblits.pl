#!/usr/bin/perl -w
use strict;
use warnings;
use Carp qw| cluck :DEFAULT |;
use Getopt::Long qw(:config gnu_getopt auto_version auto_help);
use Pod::Usage;
our $opt;
BEGIN {
  our $VERSION = "1.0";

  my $Lok = GetOptions( $opt = { dataroot => '/mnt/project/rost_db/data/hhblits', prefix => '/var/tmp/rost_db/data/hhblits', scriptdir => '~rost_db/src' }, 'dataroot=s', 'debug!', 'man!', 'prefix=s', 'scriptdir=s' );
  if( !$Lok ){ die("Invalid arguments, please check man page.\n"); }
}
use lib glob($opt->{scriptdir});
use RG::I12Fetch;

my $dbg = $opt->{debug};

if( $opt->{man} ){ pod2usage(-verbose => 2); }

my $spr = RG::I12Fetch->new()->dbg($dbg);

my $ddir = "$opt->{prefix}";

$spr->do_mkdir( $ddir );

my @files = glob( "$opt->{dataroot}/pdb_full*" );

$spr->cp_files( files => \@files, ddir => $ddir );

exit(0);

=pod

=head1 NAME

fetchPdb_full_hhblits.pl - make a node-local copy of the `pdb_full' hhblits database

=head1 SYNOPSIS

~rost_db/src/fetchPdb_full_hhblits.pl

=head1 DESCRIPTION

fetchPdb_full_hhblits.pl makes a node-local copy of the `pdb_full' hhblits database.

=head1 OPTIONS

=over

=item --dataroot

Default: F</mnt/project/rost_db/data/hhblits>

=item --debug

=item --nodebug

=item --help

=item --man

=item --prefix

prefix for destination paths, default: '/var/tmp/rost_db/data/hhblits'

=item --scriptdir

Default: F<~rost_db/src>

=item --version

=back

=head1 AUTHOR

Laszlo Kajan <lkajan@rostlab.org>

=cut

# vim:et:ts=2:ai:

