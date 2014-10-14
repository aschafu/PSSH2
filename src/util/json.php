<?php 
$seq=$_GET['seq'];
$cmd=escapeshellcmd("perl /mnt/project/pssh/pssh2_project/src/util/getSNAPjsonForPSSH.pl --seq $seq");
$r=shell_exec($cmd);
echo $r;
?>
