#!/bin/bash
log_dir=$1
redo_md5sums_file=$2
cd $log_dir
for e in $(ls);
do 
	if [ $(stat -c %s $e) -gt "49" ];
	then 
		grep 'cat:' $e | awk -F "/" '{print $6}' | sed 's/-pssh2_db_entry: No such file or directory//' >> $redo_md5sums_file;  
	fi; 
done
