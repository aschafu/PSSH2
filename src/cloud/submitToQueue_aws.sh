#!/bin/bash
for md5 in `tail -n +1 pdbChain.uniq.xlt50.clgt10.201709.md5` ; do echo $md5; aws --region=$REGION sqs send-message --queue-url https://sqs.$REGION.amazonaws.com/$ACCOUNT/build_hhblits_structure_profiles --message-body $md5; done
