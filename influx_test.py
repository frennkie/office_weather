#!/usr/bin/env python
"""
based on code by henryk ploetz
https://hackaday.io/project/5301-reverse-engineering-a-low-cost-usb-co-monitor/log/17909-all-your-base-are-belong-to-us

"""

from __future__ import print_function
import os
import sys
import fcntl
import time
import yaml
import influxdb

import random

DATABASE_NAME = "climate"

def get_config(config_file=None):
    """Get config from file; if no config_file is passed in as argument
        default to "config.yaml" in script dir"""

    if config_file is None:
        script_base_dir = os.path.dirname(os.path.realpath(sys.argv[0])) + "/"
        config_file = script_base_dir + "config.yaml"

    with open(config_file, 'r') as stream:
        return yaml.load(stream)

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

def main():
    """main"""
    config = get_config()

    if config["use_proxy"]:
        print("using proxy")
        proxies = {
                "http": config["http_proxy_config"],
                "https": config["https_proxy_config"]
        }
    else:
        proxies = None

    print(config)

    client = influxdb.InfluxDBClient(host=config["host"],
                                     port=config["port"],
                                     username=config["username"],
                                     password=config["password"],
                                     database=DATABASE_NAME,
                                     ssl=config["ssl"],
                                     proxies=proxies,
                                     verify_ssl=config["verify_ssl"])

    validate_db(client)

    for count in range(1, 30*60*24*2):

        rand_tmp = random.randint(-5, 15)*2
        rand_co2 = rand_tmp * random.randint(3, 9) * 10
        print(str(count) + ": " + str(rand_tmp) + ", " + str(rand_co2))

        dataset = create_dataset(config, tmp=rand_tmp, co2=rand_co2)
        #print("write dataset")
        client.write_points(dataset)

        time.sleep(2)

if __name__ == "__main__":
    main()
