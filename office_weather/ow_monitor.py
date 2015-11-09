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

import requests
requests.packages.urllib3.disable_warnings()

from acm import AirControlMini

#import random

DATABASE_NAME = "climate"

def decrypt(key,  data):
    cstate = [0x48,  0x74,  0x65,  0x6D,  0x70,  0x39,  0x39,  0x65]
    shuffle = [2, 4, 0, 7, 1, 6, 5, 3]

    phase1 = [0] * 8
    for i, o in enumerate(shuffle):
        phase1[o] = data[i]

    phase2 = [0] * 8
    for i in range(8):
        phase2[i] = phase1[i] ^ key[i]

    phase3 = [0] * 8
    for i in range(8):
        phase3[i] = ( (phase2[i] >> 3) | (phase2[ (i-1+8)%8 ] << 5) ) & 0xff

    ctmp = [0] * 8
    for i in range(8):
        ctmp[i] = ( (cstate[i] >> 4) | (cstate[i]<<4) ) & 0xff

    out = [0] * 8
    for i in range(8):
        out[i] = (0x100 + phase3[i] - ctmp[i]) & 0xff

    return out

def hd(d):
    return " ".join("%02X" % e for e in d)

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


    key = [0xc4, 0xc6, 0xc0, 0x92, 0x40, 0x23, 0xdc, 0x96]
    fp = open(sys.argv[1], "a+b",  0)
    HIDIOCSFEATURE_9 = 0xC0094806
    set_report = "\x00" + "".join(chr(e) for e in key)
    fcntl.ioctl(fp, HIDIOCSFEATURE_9, set_report)

    values = {}
    stamp = now()

    while True:
        data = list(ord(e) for e in fp.read(8))
        decrypted = decrypt(key, data)
        if decrypted[4] != 0x0d or (sum(decrypted[:3]) & 0xff) != decrypted[3]:
            print(hd(data), " => ", hd(decrypted),  "Checksum error")
        else:
            op = decrypted[0]
            val = decrypted[1] << 8 | decrypted[2]
            values[op] = val

            if (0x50 in values) and (0x42 in values):
                co2 = values[0x50]
                tmp = (values[0x42]/16.0-273.15)
                print("CO2: %4i TMP: %3.1f" % (co2, tmp))
                if now() - stamp > 5:
                    print(">>>")
                    #publish(client, config["prefix"], co2, tmp)

                    dataset = create_dataset(config, tmp=tmp, co2=co2)
                    client.write_points(dataset)

                    stamp = now()

    """
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

    """

if __name__ == "__main__":
    main()

