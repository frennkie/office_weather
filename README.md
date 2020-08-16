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
sudo apt-get install python-pip python-pygame libyaml-dev libpython2.7-dev
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
sudo reboot
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
MAILTO="you@example.com"

# run script every minute. This will use config: /home/pi/office_weather/office_weather/config.yaml
* * * * * /usr/bin/python /home/pi/office_weather/office_weather/ow_monitor.py > /dev/null 2>&1
```

The script will default to using "config.yaml" (residing in the same directory as the
ow_monitor.py script - /home/pi/office_weather/office_weather in the example) for the influxdb credentials.
You can optionally override this by passing a custom configuration file path as a second parameter.


# Dashboarding

In order to save on storage and have a much faster UI experience the following setup makes sure that data is stored at different 
aggregation levels over time. The full amount of data (points) is kept only for a limited time - but the aggregation (which takes
a lot less data and is queried more quickly) can be kept for a very long timeframe.

See also: https://community.icinga.com/t/retention-policies-and-continuous-queries-made-simple/117 and https://github.com/grafana/grafana/issues/4262

This uses four different "datastores":

* autogen: All data is kept for ~3 month
* d: Data is aggregated over 1 minutes intervals and kept ~1 day
* m: Data is aggregated over 5 minutes intervals and kept ~1 month
* y: Data is aggregated over 1 hour intervals and kept ~4 years (1500 days)

## Influxdb


Change the default retention policy (RP) which is called **autogen**

```
ALTER RETENTION POLICY "autogen" ON "climate" DURATION 99d REPLICATION 1
```

Create additional retention policies (Day, Month, Years)

```
CREATE RETENTION POLICY "d" ON "climate" DURATION 24h1m REPLICATION 1
CREATE RETENTION POLICY "m" ON "climate" DURATION 32d REPLICATION 1
CREATE RETENTION POLICY "y" ON "climate" DURATION 1500d REPLICATION 1
```

Then create continuous queries (CQ) that will take the data from the `autogen` and insert an aggregate into the corresponding RP.

The follow CQ uses extra MIN and MAX fields to retain the original values.

```
CREATE CONTINUOUS QUERY cq_co2_1m_for_ag ON climate BEGIN SELECT last(value) AS value, max(value) AS max, min(value) AS min INTO climate.autogen.co2 FROM climate.autogen.co2 GROUP BY time(1m), * END
CREATE CONTINUOUS QUERY cq_tmp_1m_for_ag ON climate BEGIN SELECT last(value) AS value, max(value) AS max, min(value) AS min INTO climate.autogen.tmp FROM climate.autogen.tmp GROUP BY time(1m), * END
CREATE CONTINUOUS QUERY cq_co2_1m_for_1d ON climate BEGIN SELECT mean(value) AS value, max(value) AS max, min(value) AS min INTO climate.d.co2 FROM climate.autogen.co2 GROUP BY time(1m), * END
CREATE CONTINUOUS QUERY cq_tmp_1m_for_1d ON climate BEGIN SELECT mean(value) AS value, max(value) AS max, min(value) AS min INTO climate.d.tmp FROM climate.autogen.tmp GROUP BY time(1m), * END
CREATE CONTINUOUS QUERY cq_co2_5m_for_1m ON climate BEGIN SELECT mean(value) AS value, max(value) AS max, min(value) AS min INTO climate.m.co2 FROM climate.autogen.co2 GROUP BY time(5m), * END
CREATE CONTINUOUS QUERY cq_tmp_5m_for_1m ON climate BEGIN SELECT mean(value) AS value, max(value) AS max, min(value) AS min INTO climate.m.tmp FROM climate.autogen.tmp GROUP BY time(5m), * END
CREATE CONTINUOUS QUERY cq_co2_1h_for_1y ON climate BEGIN SELECT mean(value) AS value, max(value) AS max, min(value) AS min INTO climate.y.co2 FROM climate.autogen.co2 GROUP BY time(1h), * END
CREATE CONTINUOUS QUERY cq_tmp_1h_for_1y ON climate BEGIN SELECT mean(value) AS value, max(value) AS max, min(value) AS min INTO climate.y.tmp FROM climate.autogen.tmp GROUP BY time(1h), * END
```

In your Influxdb create a new measurement called "forever" and insert the retention policy configuration. This will be used for Grafana.

```
CREATE RETENTION POLICY "forever" ON testing DURATION INF REPLICATION 1
INSERT INTO forever rp_config,idx=1 rp="autogen",start=0i,end=3600000i -9223372036854775790
INSERT INTO forever rp_config,idx=2 rp="d",start=3600000i,end=86400000i -9223372036854775780
INSERT INTO forever rp_config,idx=3 rp="m",start=86400000i,end=2592000000i -9223372036854775770
INSERT INTO forever rp_config,idx=4 rp="y",start=2592000000i,end=3110400000000i -9223372036854775760

select * from "forever"."rp_config"
```


## Grafana

Dashboard Settings -> Variables -> New

Name: rp
Type: Query
Label: Retention Policy (auto)

Refresh: On Time Range Change
Query: `select rp from forever.rp_config where $__to - $__from > "start" and $__to - $__from <= "end"` 

Use **$rp** in the queries: `SELECT mean("value") FROM "$rp"."tmp" ...`


# credits

based on code by [henryk ploetz](https://hackaday.io/project/5301-reverse-engineering-a-low-cost-usb-co-monitor/log/17909-all-your-base-are-belong-to-us)

# license

[MIT](http://opensource.org/licenses/MIT)

# contribute
pylint --rcfile=../pylint.rc --init-hook='import sys; sys.path.append("/home/robbie/work/office_weather/office_weather")' ow_test.py
pylint --rcfile=pylint.rc --init-hook='import sys; sys.path.append("/home/robbie/work/office_weather/office_weather")' office_weather/ow_test.py
