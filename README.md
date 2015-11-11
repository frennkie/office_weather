# what & why?

Measuring Co2 and Temperature at [Woogas office](http://www.wooga.com/jobs/office-tour/).

People are sensitive to high levels of Co2 or uncomfortably hot work environments, so we want to
have some numbers. It turns out that our [office](https://metrics.librato.com/share/dashboards/l7pd2aia) does
vary in temperature and Co2 across the floors.

# requirements

## hardware

1) [TFA-Dostmann AirControl Mini CO2 Messgerät](http://www.amazon.de/dp/B00TH3OW4Q) -- 80 euro

2) [Raspberry PI 2 Model B](http://www.amazon.de/dp/B00T2U7R7I) -- 40 euro

3) case, 5v power supply, microSD card

## software


1) influxdb (I'm not using librato.. but you could if you want to:) [Librato](https://www.librato.com) account for posting the data to.

2) download [Raspbian](https://www.raspberrypi.org/downloads/) and [install it on the microSD](https://www.raspberrypi.org/documentation/installation/installing-images/README.md). We used [this version](https://github.com/wooga/office_weather/blob/0da94b4255494ecbcf993ec592988503c6c72629/.gitignore#L2) of raspbian.

# installation on the raspberry

0) Boot the raspberry with the raspbian. You'll need a USB-keyboard, monitor and ethernet for this initial boot. After overcoming the initial configuration screen, you can login into the box using ssh.

1) get this repo
```
git clone https://github.com/frennkie/office_weather.git
cd office_weather
```

2) install python libs
```
sudo apt-get install python-pip python-pygame
sudo pip install -U pip
sudo pip install -U -r requirements.txt
```

3) create copy of example config  `cp office_weather/config.yaml.sample office_weather/config.yaml`
```
# influxdb
host: influx.example.com
port: 8086
ssl: yes
verify_ssl: yes
username: username
password: password
# tags for sensor and office
sensor: raspberry
office: main-floor
```

4) get udev rules in place
```
sudo cp 90-co2mini.rules /etc/udev/rules.d/
```

5) setup sudo
```
sudo visudo
pi ALL=(ALL) NOPASSWD: /bin/chmod a+rw /dev/co2mini0
pi ALL=(ALL) NOPASSWD: /bin/chmod a+rw /dev/co2mini1
pi ALL=(ALL) NOPASSWD: /bin/chmod a+rw /dev/co2mini2
pi ALL=(ALL) NOPASSWD: /bin/chmod a+rw /dev/co2mini3
```

**TODO**: check whether `/dev/co2mini*` would work in sudo too


**optionally**: to also be able to change audio output to play to 3,5mm instead of HDMI:
```
pi ALL=(ALL) NOPASSWD: /usr/bin/amixer cset numid=3 1
```

6) run the script
```
python office_weather/ow_monitor.py
```

7) run on startup
To get everything working on startup you need to add a cronjob for the pi user:

pi user:
```
SHELL=/bin/bash
* * * * * /usr/bin/python /home/pi/office_weather/office_weather/ow_monitor.py [ **optional:** /home/pi/my_config.yaml ] > /dev/null 2>&1
```

The script will default to using "config.yaml" (residing in the same directory as the
ow_monitor.py script - /home/pi/office_weather/office_weather in the example) for the influxdb credentials.
You can optionally override this by passing a custom configuration file path as a second parameter.

# credits

based on code by [henryk ploetz](https://hackaday.io/project/5301-reverse-engineering-a-low-cost-usb-co-monitor/log/17909-all-your-base-are-belong-to-us)

# license

[MIT](http://opensource.org/licenses/MIT)
