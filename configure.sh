#!/usr/bin/env sh

export FLASK_CODE=cam2web
export USER_NAME=$USER

sudo touch /var/log/$FLASK_CODE.log
sudo chown $USER_NAME:$USER_NAME /var/log/$FLASK_CODE.log
