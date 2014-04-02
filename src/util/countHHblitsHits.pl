#!/usr/bin/perl -w   

# countHHblitsHits.pl 
# Counts the number of sequence hits better than a set of E-values in hhblits output


my %colNames = ('1e-100' => 'hh_100', '1e-33' => 'hh_33', '1e-10' => 'hh_10', '1e-3' => 'hh_3', '1e10' => 'hh_p10');
my @evalCutoffs = keys %colNames; 
my %evalues = ();

my $align_lines = 0;
my $cluster_id = "";
my $id = ""; 
my @id_list;
#my $probability;
my $evalue; 
#my $identity;
#my $similarity;
#my $length;
#my $score;
  
for my $line (<STDIN>) {
	if ($line =~ /No 1 /) {
		$align_lines = 1; 
    }
    
    if ($align_lines) {   #parsing alignments 
  
  		if ($line =~ /^>(\S+)\s(.+)/) { #1st line
        	$cluster_id = $1;
        	my $sp = $2; #contains all ids of the cluster
        	@id_list = ();

		    while ($sp =~ /\|(sp:)*(\w+)/g) {
				my $uniprot_id = $2;
		        push(@id_list, $uniprot_id);
		    }
		}

    }
	
	if ($line =~ /^Probab/) { #2nd line
        my @p = split(/\s+/, $line);
#		$probability = $p[0];
        $evalue = $p[1]; 
#        $score = $p[2];
#        $length = $p[3];
#		 $identity = $p[4];
#        $similarity = $p[5];

        $evalue =~ /=(.+)/; 
        $evalue = $1;
#       $identity =~ /=(.+)\%/;
#       $identity = $1;
#       $similarity =~ /=(.+)/;
#       $similarity = $1;
#       $length =~ /=(.+)/;
#       $length = $1;
#       $score =~ /=(.+)/;
#       $score = $1;
#		$probability =~ /=(.+)/; 
#		$probability = $1;

		my @id_list_loc = @id_list; # list of all the cluster ids

		for my $id (@id_list_loc){ # save all the cluster hits in the hash
			if (exists $evalues{$id}) {
		  	  	if ($evalue < $evalues{$id}) { # save only the HSP with the lowest evalue
		  	  		$evalues{$id} = $evalue;
			  	}    
			}
			else {
		  	  	$evalues{$id} = $evalue;
			}
  		}
		
    } # end of Probab line

} # end of input

foreach $id(keys %evalues){
	my $eVal = $evalues{$id};
	foreach $cut(@evalCutoffs){
		if ($eVal <= 1.0*$cut){
			$count{$cut} ++;
		}
	}
}

foreach $cut(@evalCutoffs){
	print STDOUT $colNames{$cut}."=".$count{$cut}, ",";
}
print STDOUT "\n";


  


