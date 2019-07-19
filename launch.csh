#!/bin/csh

pushd "/home/iamOgunyinka/PycharmProjects/TragelPython/"
source venv/bin/activate.csh
export SECRET_KEY="as6234oeryertertertpsefjest9e6586ds9t056rturentretmnbvcxz4nv54taw"
export FLASK_CONFIG=production
exec gunicorn -w 1 -b 127.0.0.1:6000 run:app
