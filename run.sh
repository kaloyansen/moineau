#!/usr/bin/env sh

export FLASK_PORT="8081"
export FLASK_TITLE="vrabec.tv"
export FLASK_WORK_DIRECTORY="/yocto/moineau"
export FLASK_SECRET_KEY="68c80c893465f24b2a2151cd9bf9b49c3b9889823bca1a26cabf350864705429"
export FLASK_CODE="cam2web"
export FLASK_LOG_FILE="/var/log/$FLASK_CODE.log"
export IP_BAN_LIST_COUNT="3"
export IP_BAN_LIST_SECONDS="10000000"

echo initializing python virtual envirenment
source $FLASK_WORK_DIRECTORY/venv/bin/activate

echo starting web application on 0.0.0.0:$FLASK_PORT
exec $FLASK_WORK_DIRECTORY/$FLASK_CODE.py

echo




