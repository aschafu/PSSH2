<?php 
$seq=$_GET['seq'];
$details="";
if (isset $_GET['details']){
	$details=" --details";
}
$cmd=escapeshellcmd("perl /mnt/project/pssh/pssh2_project/src/util/getSNAPjsonForPSSH.pl --seq $seq $details");
$r=shell_exec($cmd);
echo $r;
?>
