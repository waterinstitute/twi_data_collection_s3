#!/bin/bash
SCRIPTPATH=$(dirname "$(realpath -s "$0")")
ACTIVATE_VENV="$SCRIPTPATH/../.venv/bin/activate"
AGOL_CREDENTIALS_FILE="$SCRIPTPATH/.agol_setup.sh"
SRC_PATH="$SCRIPTPATH/../src"
# shellcheck source=../.venv/bin/activate
if [[ ! -f "$ACTIVATE_VENV" ]]
then
cat >&2 <<EOF
The virtual environment (.venv) doesn't exist at the expected location, please create it by running
at the project root folder:
virtualenv -p python3 .venv
source .venv/bin/activate
pip install -r requirements.txt
EOF
exit 1
fi
# shellcheck source=../.venv/bin/activate
source "$ACTIVATE_VENV"
AGOL=false
# shellcheck source=.agol_setup.sh
if [[ -f "$AGOL_CREDENTIALS_FILE" ]]
then
source "$SCRIPTPATH/.agol_setup.sh"
AGOL=true
fi
export PYTHONPATH="$SRC_PATH:$PYTHONPATH"
if [[ $AGOL == true ]]
then
python -m metadata_collector collect --agol_credentials '{"username":"'$AGOL_USERNAME'", "password":"'$AGOL_PASSWORD'", "endpoint":"'$AGOL_ENDPOINT'", "folder":"'${AGOL_FOLDER:-GLO}'"}' "$@"
else
python -m metadata_collector collect "$@"
fi
