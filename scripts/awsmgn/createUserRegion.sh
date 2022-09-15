#!/bin/bash
USER=$1
REGION=$2
aws iam create-user --user-name "$USER"
aws iam add-user-to-group --group-name OCDLWI-S3-lwi-common-ro --user-name "$USER"
aws iam add-user-to-group --group-name "OCDLWI-S3-lwi-region$REGION-rw" --user-name "$USER"
aws iam create-access-key --user-name "$USER"
