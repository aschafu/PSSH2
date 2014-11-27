<?php 
$option=""
if (isset($_GET['seq'])){
	$seq=$_GET['seq'];
	$option="--seq $seq";
}
elseif (isset($_GET['uniprotAcc'])){
	$uniprotAcc=$_GET['uniprotAcc'];
	$option="--uniprotAcc $uniprotAcc";
}
$details="";
if (isset($_GET['details'])){
	$details=" --details";
}
$cmd=escapeshellcmd("perl /mnt/project/pssh/pssh2_project/src/util/getSNAPjsonForAquaria.pl $option $details");
$r=shell_exec($cmd);
echo $r;
?>
