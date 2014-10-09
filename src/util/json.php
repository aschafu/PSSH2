<?php 
$seq=$_GET['seq'];
$cmd=escapeshellcmd("perl /mnt/project/snap2web/getjson.pl --seq $seq");
$r=shell_exec($cmd);
echo $r;
?>
