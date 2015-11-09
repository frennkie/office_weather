# -*- coding: utf-8 -*-
"""
Name
Author
Created

based on


based on code by henryk ploetz
https://hackaday.io/project/5301-reverse-engineering-a-low-cost-usb-co-monitor/log/17909-all-your-base-are-belong-to-us
"""

from __future__ import print_function
import os
import sys
import time
import yaml
import socket
import subprocess

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
        s.bind('\0ow_monitor_lock')
    except socket.error:
        # if script is already running just exit silently
        sys.exit(0)

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

    # not implemented yet:
    # acm = AirControlMini(device=AirControlMini.auto_detect_sensor())
    acm = AirControlMini()

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

