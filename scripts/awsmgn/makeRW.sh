#!/bin/bash
while read -r username
do
aws iam add-user-to-group --group-name OCDLWI-S3-lwi-common-rw --user-name "$username"
aws iam remove-user-from-group --group-name OCDLWI-S3-lwi-common-ro --user-name "$username"
done<"$1"
