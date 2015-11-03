#!/bin/bash

set -x
exec > >(tee /var/log/user-data.log|logger -t user-data ) 2>&1

mkdir /mnt/local-storage/pssh2_data
mkdir /mnt/data
mount --bind /mnt/local-storage/pssh2_data /mnt/data

./pssh2_init_universal.sh
./pssh2_init_data.sh

# we currently don't have a database connection
cat > /usr/bin/DB.pssh2_local <<EOF
#!/bin/bash
echo ""
EOF
