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
import fcntl
import time
import yaml
import socket
import influxdb
import subprocess

import requests
requests.packages.urllib3.disable_warnings()

from acm import AirControlMini


DATABASE_NAME = "climate"

def now():
    return int(time.time())

def get_config(config_file=None):
    """Get config from file; if no config_file is passed in as argument
        default to "config.yaml" in script dir"""

    if config_file is None:
        script_base_dir = os.path.dirname(os.path.realpath(sys.argv[0])) + "/"
        config_file = script_base_dir + "config.yaml"

    with open(config_file, 'r') as stream:
        return yaml.load(stream)

def validate_db(_client):
    """Make sure the database exists"""

    db_missing = True
    try:
        _client.query("show measurements")
        db_missing = False
    except influxdb.exceptions.InfluxDBClientError as err:
        if "database not found" in str(err.content):
            # db is missing.. we can handle that
            pass
        else:
            print("An error occured: " + str(err.content))
            sys.exit(1)

    if db_missing:
        print("Creating non-existant database: " + DATABASE_NAME)
        _client.create_database(DATABASE_NAME)

    return True

def create_dataset(_config, tmp=None, co2=None):
    """create and return a json dataset ready to sent to API as POST"""

    sensor = _config["sensor"]
    office = _config["office"]

    json_body = [
        {
            "measurement": "tmp",
            "tags": {
                "sensor": sensor,
                "office": office
            },
            "fields": {
                "value": tmp
            }
        },
        {
            "measurement": "co2",
            "tags": {
                "sensor": sensor,
                "office": office
            },
            "fields": {
                "value": co2
            }
        }
    ]

    return json_body


def main():
    """main"""

    # use lock on socket to indicate that script is already running
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        ## Create an abstract socket, by prefixing it with null.
        s.bind('\0postconnect_gateway_notify_lock')
    except socket.error, e:
        # if script is already running just exit silently
        sys.exit(0)


    devnull = open("/dev/null","w")
    subprocess.call(["sudo", "/bin/chmod", "a+rw", "/dev/hidraw0"],stderr=devnull)

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

    client = influxdb.InfluxDBClient(host=config["host"],
                                     port=config["port"],
                                     username=config["username"],
                                     password=config["password"],
                                     database=DATABASE_NAME,
                                     ssl=config["ssl"],
                                     #proxies=proxies,
                                     verify_ssl=config["verify_ssl"])

    validate_db(client)

    acm = AirControlMini()

    stamp = now()

    for dct in acm.get_values():
        co2 = dct[0]
        tmp = dct[1]

        print("CO2: %4i TMP: %3.1f" % (co2, tmp))

        if now() - stamp > 5:
            print(">>>")

            dataset = create_dataset(config, tmp=tmp, co2=co2)
            client.write_points(dataset)

            stamp = now()

if __name__ == "__main__":
    main()

