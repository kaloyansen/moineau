#!/usr/bin/env sh

echo loading flask configuration

export PAGE_TITLE=vrabec.tv
export FLASK_WORK_DIRECTORY=/yocto/moineau
export FLASK_SECRET_KEY="68c80c893465f24b2a2151cd9bf9b49c3b9889823bca1a26cabf350864705429"
export VIDEO_DEVICE=/dev/video0

export FLASK_CODE=cam2web
export FLASK_PORT=8081
export FPS_LIMIT=10
export JPEG_QUALITY=100
export GEVENT_WORKERS=8
export LOG_FILE=no
export LOG_FILE=/var/log/$FLASK_CODE.log
export IP_BAN_LIST_COUNT=3
export IP_BAN_LIST_SECONDS=10000000

echo static rute in $FLASK_WORK_DIRECTORY/nginx/conf.d/$FLASK_CODE.conf
echo initializing python virtual envirenment
source $FLASK_WORK_DIRECTORY/venv/bin/activate

echo starting web application on 0.0.0.0:$FLASK_PORT
echo log file $LOG_FILE
exec $FLASK_WORK_DIRECTORY/$FLASK_CODE.py

echo




