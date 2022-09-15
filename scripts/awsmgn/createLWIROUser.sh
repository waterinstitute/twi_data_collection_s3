#!/bin/bash
USER=$1
aws iam create-user --user-name "$USER"
aws iam add-user-to-group --group-name OCDLWI-S3-lwi-common-ro --user-name "$USER"
aws iam create-access-key --user-name "$USER"
