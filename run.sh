#!/usr/bin/env sh

export FLASK_WORK_DIRECTORY="/yocto/moineau"
export FLASK_TITLE="vrabec.tv"
export IP_BAN_LIST_COUNT="3"
export IP_BAN_LIST_SECONDS="10000000"
export FLASK_SECRET_KEY="68c80c893465f24b2a2151cd9bf9b49c3b9889823bca1a26cabf350864705429"
export FLASK_LOG_FILE="$FLASK_WORK_DIRECTORY/log/log"

echo initializing virtual envirenment
source $FLASK_WORK_DIRECTORY/venv/bin/activate

echo starting application
echo logging file $FLASK_LOG_FILE

exec $FLASK_WORK_DIRECTORY/cam2web

echo



