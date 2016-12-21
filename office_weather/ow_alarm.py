# -*- coding: utf-8 -*-
"""office_weather alarm"""

from __future__ import print_function
from __future__ import absolute_import

import os
import sys
import yaml

import audio
from influxdb import InfluxDBClient


DATABASE_NAME = "climate"
CO2_LIMIT = 1400

def create_dataset(tags, **kwargs):
    """create and return a json dataset ready to sent to API as POST

    Args:
        tags (dict): A dict of tags that will be associated with the data points
        **kwargs: keyword arguments containing the values will be put into the db

    Returns:
        dataset in json format that should then be sent as the POST body
    """

    json_body = list()

    for key in kwargs:
        dct = {
            "measurement": key,
            "tags": tags,
            "fields": {
                "value": kwargs[key]
            }
        }
        json_body.append(dct)

    return json_body

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

    client = InfluxDBClient(host=config["host"],
                            port=config["port"],
                            username=config["username"],
                            password=config["password"],
                            database=DATABASE_NAME,
                            ssl=config["ssl"],
                            proxies=proxies,
                            verify_ssl=config["verify_ssl"])

    client.create_database(DATABASE_NAME)

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

