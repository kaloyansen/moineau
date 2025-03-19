#!/usr/bin/env sh

export FLASK_WORK_DIRECTORY="/yocto/moineau"
export FLASK_CODE="cam2web"
export FLASK_APP="$FLASK_CODE:server"
export FLASK_TITLE="vrabec.tv"
export IP_BAN_LIST_COUNT="3"
export IP_BAN_LIST_SECONDS="10000000"
export FLASK_SECRET_KEY="68c80c893465f24b2a2151cd9bf9b49c3b9889823bca1a26cabf350864705429"
export FLASK_LOG_FILE="/var/log/$FLASK_CODE.log"
export FLASK_PORT="8081"

echo initializing virtual envirenment
source $FLASK_WORK_DIRECTORY/venv/bin/activate

echo starting application on 0.0.0.0:$FLASK_PORT
# exec "python -m gevent.pywsgi -w 4 --bind 0.0.0.0:$FLASK_PORT $FLASK_WORK_DIRECTORY/$FLASK_CODE"
# exec python -m gevent.pywsgi --bind 0.0.0.0:$FLASK_PORT $FLASK_CODE:server
exec $FLASK_WORK_DIRECTORY/$FLASK_CODE.py

echo




