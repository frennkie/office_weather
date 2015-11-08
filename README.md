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


python-pygame

python-pip


1) [Librato](https://www.librato.com) account for posting the data to.

2) download [Raspbian](https://www.raspberrypi.org/downloads/) and [install it on the microSD](https://www.raspberrypi.org/documentation/installation/installing-images/README.md). We used [this version](https://github.com/wooga/office_weather/blob/0da94b4255494ecbcf993ec592988503c6c72629/.gitignore#L2) of raspbian.

# installation on the raspberry

0) Boot the raspberry with the raspbian. You'll need a USB-keyboard, monitor and ethernet for this initial boot. After overcoming the initial configuration screen, you can login into the box using ssh.

1) install python libs
```
sudo apt-get install python-pip python-pygame
sudo pip install -U pip
sudo pip install -U -r requirements.txt
```

2) create copy of example config  `cp config.yaml.sample config.yaml`
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


3) fix socket permissions
```
sudo chmod a+rw /dev/hidraw0
```

4) run the script
```
./ow_monitor.py /dev/hidraw0
```

5) run on startup

To get everything working on startup, need to add 2 crontabs, one for root
and the other for the pi user:

Roots:

```
SHELL=/bin/bash
* * * * * if [ $(find /dev/hidraw0 -perm a=rw | wc -l) -eq 0 ] ; then chmod a+rw /dev/hidraw0 ; fi
```

Pi:

```
SHELL=/bin/bash
* * * * * /usr/bin/python /home/pi/ow_monitor.py /dev/hidraw0 [ **optional:** /home/pi/my_config.yaml ]  > /dev/null 2>&1
```

The script will default to using "config.yaml" (residing in the same directory as the
monitor.py script - /home/pi in the example) for the librato credentials.
You can optionally override this by passing a custom configuration file path as a second parameter.

# credits

based on code by [henryk ploetz](https://hackaday.io/project/5301-reverse-engineering-a-low-cost-usb-co-monitor/log/17909-all-your-base-are-belong-to-us)

# license

[MIT](http://opensource.org/licenses/MIT)
