# -*- coding: utf-8 -*-

from __future__ import print_function

import sys
import socket
import json

from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError
from influxdb.exceptions import InfluxDBServerError

import requests
requests.packages.urllib3.disable_warnings()


class MyInfluxDBClient(InfluxDBClient):

    def validate_db(self):
        """Make sure the database exists

        Returns:
            bool: True if successful, False otherwise.

        """

        db_missing = True
        try:
            self.query("show measurements")
            db_missing = False
        except InfluxDBClientError as err:
            if "database not found" in str(err.content):
                # db is missing.. we can handle that
                pass
            else:
                print("An error occured: " + str(err.content))
                sys.exit(1)

        if db_missing:
            print("Creating non-existent database: " + self._database)
            self.create_database(self._database)

        return True

    @staticmethod
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

if __name__ == "__main__":
    pass

