#!/bin/bash
set -x
exec > >(tee /var/log/user-data.log|logger -t user-data ) 2>&1

apt-get update
apt-get upgrade -y
apt-get install -y python-pip lvm2
pip install awscli

head -1 /etc/fstab > /tmp/fstab
mkdir /mnt/data
if test -b /dev/xvdc
then
	pvcreate /dev/xvdb /dev/xvdc
	vgcreate volgrp /dev/xvdb /dev/xvdc
	lvcreate -l 100%FREE  -n data volgrp
	mkfs -t ext4 /dev/volgrp/data
	echo "/dev/volgrp/data /mnt/data ext4 defaults 0 2" >> /tmp/fstab
else
	mkfs -t ext4 /dev/xvdb
	echo "/dev/xvdb /mnt/data ext4 defaults 0 2" >> /tmp/fstab
fi
chmod a+tw /mnt/data/
mv /tmp/fstab /etc/fstab

reboot

pssh2_init_universal.sh

cat > /usr/bin/DB.pssh2_local <<EOF
#!/bin/bash
echo "\$* ;"|mysql -u update_d --password=aquaria4ever! -hpssh2.c3snzk5nzczn.eu-west-1.rds.amazonaws.com -Dpssh2_aws --local-infile=1
EOF

#-----------------------------------------------------------------------

# The following should be run as user to pull the 20GB input data:
aws --region=eu-west-1 s3 cp s3://aquaria-020528756185-eu-west-1/data - | tar -xI pbzip2 -C /


#-----------------------------------------------------------------------

# The following should be called on reboot:
for i in `seq 1 $(nproc)`; do pss2_aws & done
