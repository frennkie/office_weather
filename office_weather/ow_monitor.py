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
from __future__ import absolute_import

import os
import sys
import time
import yaml
import socket
import subprocess

from office_weather.acm import AirControlMini
from office_weather.my_influxdb import MyInfluxDBClient

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
    """now as an int"""
    return int(time.time())


def main():
    """main"""

    # use lock on socket to indicate that script is already running
    try:
        lock_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        ## Create an abstract socket, by prefixing it with null.
        lock_socket.bind('\0ow_monitor_lock')
    except socket.error:
        # if script is already running just exit silently
        sys.exit(0)

    device = AirControlMini.auto_detect_sensor()

    devnull = open("/dev/null", "w")
    subprocess.call(["sudo", "/bin/chmod", "a+rw", device], stderr=devnull)

    acm = AirControlMini(device=device)
    acm.connect()

    try:
        config = get_config(config_file=sys.argv[1])
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

    client = MyInfluxDBClient(host=config["host"],
                              port=config["port"],
                              username=config["username"],
                              password=config["password"],
                              database=DATABASE_NAME,
                              ssl=config["ssl"],
                              proxies=proxies,
                              verify_ssl=config["verify_ssl"])

    client.validate_db()

    stamp = now()

    for cur_co2, cur_tmp in acm.get_values():
        print("CO2: %4i TMP: %3.1f" % (cur_co2, cur_tmp))

        if now() - stamp > 5:
            print(">>>")
            dataset = client.create_dataset(config, tmp=cur_tmp, co2=cur_co2)
            client.write_points(dataset)
            stamp = now()

if __name__ == "__main__":
    main()

