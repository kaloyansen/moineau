#!/usr/bin/env sh


export FLASK_WORK="/yocto/moineau"

export IP_BAN_LIST_COUNT="3"
export IP_BAN_LIST_SECONDS="10000"

export FLASK_SECRET_KEY="68c80c893465f24b2a2151cd9bf9b49c3b9889823bca1a26cabf350864705429"
export FLASK_LOG_FILE="$FLASK_WORK/log/log"

echo initializing virtual envirenment
source $FLASK_WORK/venv/bin/activate
echo starting application
echo logging file $FLASK_LOG_FILE
exec $FLASK_WORK/cam2web
echo have a nice day

