#!/bin/tcsh
## go over cache and get rid of files that take too much space (rm a3m, log, gzip hhr)

# loop over subdirs, so there are not too many files in a find
foreach dir ( `ls $CACHE/result_cache_2014/` )
	# find a3m files that have not been removed and are not currently used (older than 2 days)
	foreach file ( `find $CACHE/result_cache_2014/$dir/ -name "*.a3m" -mtime +2`)
 		set foundDir=`dirname $file`
 		echo $foundDir
 		ls -lh $foundDir
 		ls $foundDir/*.a3m
		rm $foundDir/*.a3m
 		ls $foundDir/*.log
 		rm $foundDir/*.log
 		ls $foundDir/*.hhr
 		gzip $foundDir/*.hhr
 		ls -lh $foundDir
 	end
end
