# -*- coding: utf-8 -*-
"""
Name        ow_test.py
Author      Robert Habermann <mail@rhab.de>
Created     2015-11-08

based on
https://github.com/wooga/office_weather

based on code by henryk ploetz
https://hackaday.io/project/5301-reverse-engineering-a-low-cost-usb-co-monitor/log/17909-all-your-base-are-belong-to-us
"""

from __future__ import print_function

import socket
import subprocess
import sys
import time

import os
import yaml
from acm import AirControlMini
from influxdb_proxies import InfluxDBClientProxies

DATABASE_NAME = "climate"


def get_config(config_file=None):
    """
    Args:
        config_file (str): name of config file, defaults to script dir + "config.yaml"

    Return:
        dict containing the config settings parsed from yaml

    """

    if config_file is None:
        script_base_dir = os.path.dirname(os.path.realpath(sys.argv[0])) + "/"
        config_file = script_base_dir + "config.yaml"

    with open(config_file, 'r') as stream:
        return yaml.load(stream)


def now():
    return int(time.time())


def main():
    """main"""

    # use lock on socket to indicate that script is already running
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        ## Create an abstract socket, by prefixing it with null.
        s.bind('\0ow_test_notify_lock')
    except socket.error:
        # if script is already running just exit silently
        sys.exit(0)

    # not implemented yet:
    # my_sensor = AirControlMini.auto_detect_sensor()
    # acm = AirControlMini(device=my_sensor)
    acm = AirControlMini()

    devnull = open("/dev/null", "w")
    subprocess.call(["sudo", "/bin/chmod", "a+rw", "/dev/hidraw0"], stderr=devnull)

    try:
        config = get_config(config_file=sys.argv[2])
    except IndexError:
        config = get_config()

    if config["use_proxy"]:
        print("using proxy")
        proxies = {
                   "http": config["http_proxy_config"],
                   "https": config["https_proxy_config"]
        }
    else:
        proxies = None

    client = InfluxDBClientProxies(host=config["host"],
                                   port=config["port"],
                                   username=config["username"],
                                   password=config["password"],
                                   database=DATABASE_NAME,
                                   ssl=config["ssl"],
                                   proxies=proxies,
                                   verify_ssl=config["verify_ssl"])

    client.validate_db()

    stamp = now()

    for cur_co2, cur_tmp in acm.get_fake_values():

        print("CO2: %4i TMP: %3.1f" % (cur_co2, cur_tmp))

        if now() - stamp > 5:
            print(">>>")

            #dataset = create_dataset(config, tmp=rand_tmp, co2=rand_co2)
            #client.write_points(dataset)

            stamp = now()

    """
    for count in range(1, 30*60*24*2):

        #_co2 = "select value from co2 where office='r1.108' order by time desc limit 1"
        #print(client.query(_co2))

        rand_tmp = random.randint(-5, 15)*2
        rand_co2 = rand_tmp * random.randint(3, 9) * 10

        mesg = "Messung " + str(count) + ": Es sind " + str(rand_tmp) + " Grad und C O 2 liegt bei " + str(rand_co2) + "."
        print(mesg)
        #audio.play_tts(mesg, lang="de-DE")

        dataset = create_dataset(config, tmp=rand_tmp, co2=rand_co2)
        client.write_points(dataset)

        time.sleep(10)

    """


if __name__ == "__main__":
    main()

