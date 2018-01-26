#!/bin/bash
set -x
exec > >(tee /var/log/user-data.log|logger -t user-data ) 2>&1

yum update -y
yum upgrade -y
yum groupinstall -y "Development Tools"
yum install -y python-pip lvm2 git ruby
yum install -y cmake mysql
# in case we want to run cstranslate on this node in parallel
yum install -y openmpi-devel
#yum install -y openmpi

mkdir /home/ec2-user/git
chmod a+tw /home/ec2-user/git
cd  /home/ec2-user/git
git clone https://github.com/aschafu/PSSH2.git

# get config data
REGION=`wget -q 169.254.169.254/latest/meta-data/placement/availability-zone -O- | sed 's/.$//'`
aws --region=$REGION s3 cp s3://pssh3cache/software/HHpaths.pm /usr/share/hhsuite/scripts/HHPaths.pm
aws --region=$REGION s3 cp s3://pssh3cache/private_config/pssh2.aws.conf /home/ec2-user/pssh2.aws.conf
conf_file=/home/ec2-user/pssh2.aws.conf
export conf_file
echo 'export conf_file="/home/ec2-user/pssh2.aws.conf"'>> /home/ec2-user/.bashrc 

echo "#!/bin/bash" > /home/ec2-user/startProcesses.sh
echo 'export conf_file=/home/ec2-user/pssh2.aws.conf' >> /home/ec2-user/startProcesses.sh
echo 'nohup /home/ec2-user/git/PSSH2/src/cloud/submitToQueue_aws_pssh2.sh > submitToQueue.log  2>&1 & '  >>  /home/ec2-user/startProcesses.sh

chmod a+x /home/ec2-user/startProcesses.sh
sudo -u ec2-user -H sh -c /home/ec2-user/startProcesses.sh