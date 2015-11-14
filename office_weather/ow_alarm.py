# -*- coding: utf-8 -*-
"""office_weather alarm"""

from __future__ import print_function
from __future__ import absolute_import

import os
import sys
import yaml

import audio
from my_influxdb import MyInfluxDBClient


DATABASE_NAME = "climate"
CO2_LIMIT = 1400


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


def main():
    """main"""
    config = get_config()

    if config["use_proxy"]:
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

    qry_co2 = "select last(value) as last_co2 from co2 WHERE time > now() - 1d"
    if qry_co2:
        for item in client.query(qry_co2):
            _dict = item
        last_co2 = int(_dict[0][u'last_co2'])

    qry_tmp = "select last(value) as last_tmp from tmp WHERE time > now() - 1d"
    if qry_tmp:
        for item in client.query(qry_tmp):
            _dict = item
        last_tmp = int(_dict[0][u'last_tmp'])

    print("Last Temp: " + str(last_tmp) + " last CO2: " + str(last_co2))

    # it above limit play audo message
    if last_co2 > CO2_LIMIT:
        mesg = "Achtung: Der aktuelle C O 2 Wert beträgt " + str(last_co2)
        print(mesg)
        audio.play_tts(mesg, lang="de-DE")

if __name__ == "__main__":
    main()

