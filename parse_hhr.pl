#!/usr/bin/perl -w

# parse_hhr.pl
# Parses an HHblits HHR-output file for required informations for PSSH2:
# "uniprot_sequence_md5sum,pdb_seqres_md5sum,E-value,identity,alignment"

use strict;
use warnings;
use File::chdir;
use Getopt::Long;

# Parse command line parameter
our($i, $m, $o, $h, $v);

my $args_ok = GetOptions('i=s'  => \$i, #input hhr file
			 'm=s'	=> \$m, #md5sum of the query sequence used to produce the hhr file 
                         'o=s'  => \$o, #output file
			 'h'	=> \$h, #print help
			 'v'	=> \$v #verbosity mode
);
if($h){
    print_help();
    exit;
}
if(!$i || !$m|| !$o){
    print "Missing parameters!\n";
    print_help();
    exit;
}
#-----------------------------------------------------------------------------------------------------------------------------------
=head 1 Subroutine print_help
Prints help.
=cut
sub print_help{
    print "Usage: parse_hhr.pl 
	-i <input hhr file>\tstandard \".hhr\" HHblits/HHsearch output file
	-m <md5sum>\tmd5sum of the query sequence used to produce the hhr file
	-o <output file>\twhere the parsed output should be written
	-h\tprints this help screen\n";
}
#-----------------------------------------------------------------------------------------------------------------------------------
=head 2 Subroutine read_hhr.
Parses the hhr output file of hhblits/hhsearch. Uses mapping of pdb chains with identical SEQRES sequence, md5sum of the sequence 
and the sequence: /mnt/project/pssh/pdb_redundant_chains-md5-seq-mapping.
input: ($i, $v)
output: \@alis, @alis format: ($seqres_md5sum, $evalue, $identity/100.0, $gapless_blocks)
=cut
sub read_hhr{
  my ($i, $v) = @_;

  ## read the mapping and make a hash, which refers target PDB ID to its SEQRES md5sum:
  if ($v) {print "Creating a hash of PDB IDs and SEQRES MD5-sums ...\n";}
  my $mapping = "/mnt/project/pssh/pdb_redundant_chains-md5-seq-mapping"; 
  my %id_md5sum = ();
  open (READ, "$mapping") or die "could not open $mapping";
  for my $line (<READ>) {
	if ($line =~ /^(\S*).*\t(\S*)\t/){
		$id_md5sum{$1} = $2; # $1=target_id, $2=seqres_md5sum
	}
  } 
  close READ;
  if ($v) {print "\%id_md5sum size: ".scalar(keys(%id_md5sum))."\n";}

  ## parse the hhr file and write the output hash %alis
  if ($v) {print "Parsing the hhr file ...\n";}
  my $align_lines = 0;
  my $ali_start;

  my $query_id;
  my $substr_query_id;
  my $full_target_id;
  my $substr_target_id;

  my @alis;
  my $target_id; #e.g. 1bab_A
  my $seqres_md5sum;
  my $evalue;
  my $identity;

  my $query_ali_start;
  my $target_ali_start;
  my $query_ali = ""; 
  my $target_ali = "";
  my $gapless_blocks;

  open (READ, "$i") or die "could not open $i";
  for my $line (<READ>) {

    if ($line =~ /^Query\s*(\S*)/) { #query
	$query_id = $1;
	$substr_query_id = substr($query_id, 0, 14);
	$substr_query_id =~ s/\|/\\\|/g;
	if ($v) {print "Query: ".$query_id."\n\n";}
    }
    
    if ($align_lines) {   #alignments   
      if ($line =~ /^>(\S+)\s(.+)/) { #1st line of an alignment
        $full_target_id = $1;
	$substr_target_id = substr($full_target_id, 0, 14);
	$substr_target_id =~ s/\|/\\\|/g;
	$ali_start = 1; #so that new alignment start positions will be read
	$query_ali = ""; #set to empty to read the new alignment
	$target_ali = "";
 	if ($v) {print "Target: ".$full_target_id."\n";}
      }   

      if ($line =~ /^Probab/) { #2nd line of an alignment
        my @p = split(/\s+/, $line);
        $evalue = $p[1]; 
        $identity = $p[4];

        $evalue =~ /=(.+)/; 
        $evalue = $1; 
        $identity =~ /=(.+)\%/;
        $identity = $1; 
      }
      
      #alignment blocks
      #alignment start positions
      if ($ali_start) {
        if ($line =~ /^Q\s+$substr_query_id\s+(\S+)\s/){ 
          $query_ali_start = $1;	
        }
        if ($line =~ /^T\s+$substr_target_id\s+(\S+)\s/){
          $target_ali_start = $1;
          $ali_start = 0; #ready with alignment start positions
        }
      }
      #alignment sequences
      if ($line =~ /^Q\s+$substr_query_id\s+\S+\s(\S+)/){
        $query_ali .= $1;
      }
      if ($line =~ /^T\s+$substr_target_id\s+\S+\s(\S+)/){
        $target_ali .= $1;
      }

      if ($line =~ /^No/ || $line =~ /Done!/) { #when next alignment begins or end - save the last alignment

        if ($full_target_id =~ /(\w{4}_\w)/){
        	$target_id = $1;
        	if ($v) {print "target ID: ".$target_id."\n";}
        }else{
        	print "Error: full target ID in wrong format!\n";
        	exit(1);
        }

        if (defined $id_md5sum{$target_id}){
        	$seqres_md5sum = $id_md5sum{$target_id};
        	if ($v) {print "Target ".$target_id." SEQRES md5sum: ".$seqres_md5sum."\n";}
        }else{
        	print "Error: SEQRES md5sum of ".$target_id." not initialized!\n";
        	exit(1);
        }

        $gapless_blocks = parse_gapless_blocks($query_ali_start, $query_ali, $target_ali_start, $target_ali, $v);

        my @ali_values = ($seqres_md5sum, $evalue, $identity/100.0, $gapless_blocks);
        push (@alis, \@ali_values);      
      }
    }

    if ($line =~ /^No 1 /) { #first alignment begins
      $align_lines = 1;  
    }   

  }
  close READ;

  return \@alis;
}
#-----------------------------------------------------------------------------------------------------------------------------------
=head 3 Subroutine parse_gapless_blocks
Parses the aligned gapless blocks in format e.g: 1-5:2-7 7-9:8-10 ...
input: ($query_ali_start, $query_ali, $target_ali_start, $target_ali, $v)
output: $gapless_blocks (in the above format)
=cut
sub parse_gapless_blocks{
my ($query_ali_start, $query_ali, $target_ali_start, $target_ali, $v) = @_;
    if ($v) {
        print "Query alignment start: ".$query_ali_start."\n";
	print "Query alignment: ".$query_ali."\n";
        print "Target alignment start: ".$target_ali_start."\n";
	print "Target alignment: ".$target_ali."\n";
    }
#initialize:
my $query_ali_cur_pos = $query_ali_start - 1;
my $target_ali_cur_pos = $target_ali_start - 1;
my $query_ali_block_start = $query_ali_start;
my $target_ali_block_start = $target_ali_start;
my $query_ali_block_end;
my $target_ali_block_end;
my $gapless_blocks = "";
my $last_gapless_pos;
my @query_ali_arr = split(//, $query_ali);
my @target_ali_arr = split(//, $target_ali);

if (scalar @query_ali_arr != scalar @target_ali_arr) {
    print "Error: Query and target alignments not of same length!\n";
    exit;
}

my $ali_length = scalar @query_ali_arr;
for(my $i=0; $i<$ali_length; $i++){
    if($query_ali_arr[$i] eq "-" || $target_ali_arr[$i] eq "-") { #a gap
	if($query_ali_arr[$i-1] ne "-" && $target_ali_arr[$i-1] ne "-") { #leading gap -> write the previous gapless block
	    $query_ali_block_end = $query_ali_cur_pos;
	    $target_ali_block_end = $target_ali_cur_pos;
	    $gapless_blocks .= "$query_ali_block_start-$query_ali_block_end:$target_ali_block_start-$target_ali_block_end ";
	}
	#update the current position for the sequence without a gap: 
 	if($query_ali_arr[$i] ne "-") {
	    $query_ali_cur_pos++;
	}
	if($target_ali_arr[$i] ne "-") {
             $target_ali_cur_pos++;
        } 
    } else { #not a gap
	#update the current position for both sequences
	$query_ali_cur_pos++;
	$target_ali_cur_pos++;
	if($query_ali_arr[$i-1] eq "-" || $target_ali_arr[$i-1] eq "-") { #last position had a gap -> start a new block
	    $query_ali_block_start = $query_ali_cur_pos;
	    $target_ali_block_start = $target_ali_cur_pos;
	}
    }
}
#write the last gapless block:
$query_ali_block_end = $query_ali_cur_pos;
$target_ali_block_end = $target_ali_cur_pos;
$gapless_blocks .= "$query_ali_block_start-$query_ali_block_end:$target_ali_block_start-$target_ali_block_end";
if ($v) {print "Gapless blocks: ".$gapless_blocks."\n\n";}
return $gapless_blocks; 
}
#-----------------------------------------------------------------------------------------------------------------------------------
=head 4 Subroutine write_output
input: ($alis_ref, $m, $v) with $m the given query uniprot sequence md5sum
output: file $o
=cut
sub write_output{
my($alis_ref, $m, $v) = @_;
if ($v) {print "Writing output to $o ...\n";}

my @alis = @{$alis_ref};
if ($v) {print "Alignments number: ".(scalar @alis)."\n";}
open(WRITE, ">".$o) or die "could not open file $o for writing";
#output format: "uniprot_sequence_md5sum,pdb_seqres_md5sum,probability,E-value,identity,alignment"
my $seqres_md5sum;
my $probability;
my $evalue;
my $identity;
my $gapless_blocks;
my $ali_num = 0; #counter of the alignments
foreach my $ali_values_ref (@alis){ #@alis: ($seqres_md5sum, $evalue, $identity/100.0, $gapless_blocks)
    $ali_num++;
    my @ali_values = @{$ali_values_ref};
    $seqres_md5sum = $ali_values[0];
    $evalue = $ali_values[1];
    $identity = $ali_values[2];
    $gapless_blocks = $ali_values[3];
    if ($ali_num == 1 || $evalue <= 10e-10){ #leave only alignments with E-value below 10e-10 or at least the first one 
      print WRITE "$m,$seqres_md5sum,$evalue,$identity,$gapless_blocks\n";
    }
}
close WRITE;
}
#-----------------------------------------------------------------------------------------------------------------------------------
my ($alis_ref) = read_hhr($i, $v);
write_output($alis_ref, $m, $v);
