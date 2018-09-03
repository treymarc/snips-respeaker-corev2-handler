
exit

sudo apt-get install python-mraa libmraa1
pip install pixel-ring
pip install paho-mqtt
pip install requests

cp -r ./handler /usr/share/snips/
cp *.service /lib/systemd/system/

systemctl daemon-reload
systemctl enable snips-handler-weather.service
systemctl enable snips-handler-ww.service

systemctl start snips-handler-weather.service
systemctl start snips-handler-ww.service

#ref https://github.com/respeaker/respeaker_v2_eval
