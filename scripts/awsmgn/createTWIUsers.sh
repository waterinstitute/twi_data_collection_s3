#!/bin/bash
export AWS_PROFILE=GLO
while read username
do
aws iam create-user --user-name "$username"
aws iam add-user-to-group --group-name glo-data-rw --user-name "$username"
aws iam tag-user --tags '[{"Key":"GLO","Value":""},{"Key":"PROJECT_ID", "Value":"P-00649--DAN-2020-GLO-SB02-RC"}]' --user-name "$username"
aws iam create-access-key --user-name "$username"
done <GLO_usersToCreate.txt
