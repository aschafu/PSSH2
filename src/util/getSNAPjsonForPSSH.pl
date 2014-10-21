#!/usr/bin/perl -w
use strict;
use feature qw(say);
use Getopt::Long;
use lib glob("/mnt/project/snap2web/");
use Snap2Cache;
#use DBI;
#use Config::Simple;
use POSIX;

# now read the local config info
#my $cfg = new Config::Simple("Config.ini") || die Config::Simple->error();
#my $db_user= $cfg->param('mysql.db_user');
#my $db_pass= $cfg->param('mysql.db_pass');
#my $host= $cfg->param('mysql.host');
#my $seqHashQuery = $cfg->param('mysql.seqHashQuery');


our($seq,$dbg,$details);
$details = 0;

my $args_ok=GetOptions( 'seq=s'    =>  \$seq,
						'details'  =>  \$details,
                        'debug'       => \$dbg
);

exit(255) unless defined $seq;

my $cache=new Snap2Cache($seq,$dbg);
# array of mutations first pos to all, then 2 pos to all
my @mutants=$cache->allmuts();
# hash for each prediction key e.g. M38A, value 
my %predictions=$cache->predictions();

my @result = ();
my @score;

# cache complete: check whether all 19 non-native are defined
if ($cache->complete()){
    my $maxPos = 0;
	my $minPos;
	my %varFeature;
	my @avrgFeature = ();
	my @sensitivityFeature = ();
	
	# loop over all mutations and assemble the matrix
    foreach my $mut (@mutants) {
    	# read the mutations
        $mut=~/(\w)(\d+)(\w)/o;
        my ($wt,$pos,$var) = ($1,$2,$3);
        # remember the score for later usage (e.g. building averages)
        my $scoreVal =  $predictions{$mut};
        $score[$pos]{$var} = $scoreVal;
        # remember first and last postion in the sequences
		unless (defined $minPos){$minPos = $pos};
        if ($pos>$maxPos){$maxPos = $pos};
        # assemble the individual mutation feature for this variation and this position  
		$varFeature{$var}[$pos] = getFeature("$wt > $var", $pos, "SNAP score: ".$predictions{$mut}, getHexColForScore($scoreVal));
	}
	
    # now loop over all positions and work out the average and the number of significant mutations
    for (my $pos=$minPos; $pos<=$maxPos; $pos++){
    	$avrgFeature[$pos] = "";
#    	$sensitivityFeature[$pos] = "";
    	my $sum = 0;
    	my $nVal = 0;
		my $nNeutral = 0;
		my $nEffect = 0;
		
    	foreach my $var (keys %{$score[$pos]}){
    		my $testVal = $score[$pos]{$var};
			$sum += $testVal;
			$nVal++;
			# significant score:  effect > 40
			# significant neutral: <-40
			if ($testVal > 40) {$nEffect++}
			elsif ($testVal < -40) {$nNeutral++};
    	}
    	
    	# make sure we do not divide by 0
    	if ($nVal > 0){
    		my $avrgScore = $sum/$nVal;
 	   		my $ratioNeutral = $nNeutral/$nVal;
    		my $ratioEffect = $nEffect/$nVal;

    		my $description = "avrg. score: ";
    		$description .= sprintf("%.1f", $avrgScore);
			$avrgFeature[$pos] = getFeature("Average sensitivity", $pos, $description,getHexColForScore($avrgScore)); 

			if ($ratioNeutral > 0.5){
				$description = "$nNeutral\/$nVal amino acid substitutions do not change function";
				my $rbVal = getColVal($ratioNeutral);
				# color in green for neutral
				push @sensitivityFeature, getFeature("Insensitive", $pos, $description, "#".$rbVal."FF".$rbVal); 
			}
			elsif ($ratioEffect > 0.5){
				$description = "$nEffect\/$nVal amino acid substitutions change function";
				my $gbVal = getColVal($ratioNeutral);
				# color in red for effect
				push @sensitivityFeature, getFeature("Highly sensitive", $pos, $description,"#FF".$gbVal.$gbVal); 
			}
    	}
    	
    }
    
    # put together the annotations
    my $sensitivityAnnotation = getAnnotationStart("Mutational sensitivity (predicted)", "SNAP", "https://rostlab.org/services/snap/", "Prediction of sequence positions to be sensitive / insensitive to mutation");
    $sensitivityAnnotation .= join ",\n", @sensitivityFeature;
    $sensitivityAnnotation .= getAnnotationEnd();
    push @result, $sensitivityAnnotation;
    
    my $avrgScoreAnnotation =  getAnnotationStart("Average Mutation score (SNAP)", "SNAP", "https://rostlab.org/services/snap/", "Average SNAP score at sequence position");
    $avrgScoreAnnotation .= join ",\n", @avrgFeature[$minPos..$maxPos];
    $avrgScoreAnnotation .= getAnnotationEnd();
    push @result, $avrgScoreAnnotation;
   
   if ($details){
	#    my @individualScoreAnnotations = ();
   	 foreach my $var (sort keys %varFeature){
			my $annotation = getAnnotationStart("Mutation score (SNAP)", "SNAP", "https://rostlab.org/services/snap/", "SNAP score for ".$var." scan");
			my $featuresRef = $varFeature{$var};
			$annotation .= join ",\n", @$featuresRef[$minPos..$maxPos];
			$annotation .= getAnnotationEnd();
			push @result, $annotation;
    	}
    }

	my $result = join ",\n",@result;
	print "{\n".$result."\n"."}\n";
		   
}
else {
	print "SNAP scores not complete! \n";
}

sub getAnnotationStart {
	
	my ($annotationName, $source, $URL, $annotationDescription) = @_;
	return "     "."\"".$annotationName."\": {\"Source\": \"".$source."\", \"URL\": \"".$URL."\", \"Description\": \"".$annotationDescription."\", \"Features\": [ \n"

}

sub getAnnotationEnd {
	
	return "\n     ]}"

}

sub getFeature {
	
	my ($featureName, $residue, $featureDescription, $color) = @_;
	my $colString = "";
	if ($color){
		$colString = "\", \"Color\": \"".$color;
	}
	return "         {\"Name\": \"".$featureName."\", \"Residue\": \"".$residue.$colString."\", \"Description\": \"".$featureDescription."\"}";
	
}

sub getColVal {
	
	# a high ratio should give a value close to 0, 
	# a low ration should give a value close to FF
	# This means for low ratios we will have almost white color,
	# for high ratios it will be red/green dependign on where our value gets stuck
	my ($ratio) = @_; 
	$ration = 1-$ratio; # inverting the ratio to make it scale to white (see above)!
	my $colInt = floor($ratio*256);
	if ($colInt>255){$colInt = 255};
	my $val = sprintf("%02X", $colInt);
	return $val;

}

sub getHexColForScore {
		
	my ($scoreVal) = @_;
	my $color = "";

	if ($scoreVal >= 0){
		# red color -> red on 255; rest according to ratio
		my $gbVal = getColVal($scoreVal/100); 
		$color = "#FF".$gbVal.$gbVal;
    }
    else {
        # green color -> green on 255; rest according to ratio
        my $rbVal = getColVal($scoreVal/-100); 
		$color = "#".$rbVal."FF".$rbVal;
    }
	return $color;
	
}


# {
#      "Sequence variation (natural variant site)": {"Source": "UniProt", "URL": "http://uniprot.org/uniprot/P04637", "Features": [
#          {"Name": "G > C", "Residue": 245, "Description": "Germline mutation."},
#          {"Name": "RP > SA", "Residues": [249, 250], "Description": "Somatic mutation. See <a href=\"http://pubmed.org/1394745\">PubMed evidence</a>."},
#          {"Name": "F > T", "Residue": 282}
#      ]},
#      "Mutational Sensitivity": {"Source": "SNAP", "URL": "https://rostlab.org/services/snap/", "Description": "Predicts mutation effects",  "Features": [
#          {"Name": "Highly sensitive", "Residue": 245, "Color": "#FF0000", "Description": "12/20 amino acid substitutions disrupt function."},
#          {"Name": "Insensitive", "Residue": 249, "Color": "#FF00FF", "Description": "2/20 amino acid substitutions disrupt function."}
#      ]}
# }
