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


class InfluxDBClientProxies(InfluxDBClient):
    """The :class:`~.InfluxDBClient` object holds information necessary to
    connect to InfluxDB. Requests can be made to InfluxDB directly through
    the client.
    :param host: hostname to connect to InfluxDB, defaults to 'localhost'
    :type host: str
    :param port: port to connect to InfluxDB, defaults to 8086
    :type port: int
    :param username: user to connect, defaults to 'root'
    :type username: str
    :param password: password of the user, defaults to 'root'
    :type password: str
    :param database: database name to connect to, defaults to None
    :type database: str
    :param ssl: use https instead of http to connect to InfluxDB, defaults to
        False
    :type ssl: bool
    :param verify_ssl: verify SSL certificates for HTTPS requests, defaults to
        False
    :type verify_ssl: bool
    :param timeout: number of seconds Requests will wait for your client to
        establish a connection, defaults to None
    :type timeout: int
    :param use_udp: use UDP to connect to InfluxDB, defaults to False
    :type use_udp: int
    :param udp_port: UDP port to connect to InfluxDB, defaults to 4444
    :type udp_port: int
    :param proxies: HTTP(S) proxy to use for Requests, defaults to {}
    :type proxies: dict
    """

    def __init__(self,
                 host='localhost',
                 port=8086,
                 username='root',
                 password='root',
                 database=None,
                 ssl=False,
                 verify_ssl=False,
                 timeout=None,
                 use_udp=False,
                 udp_port=4444,
                 proxies=None,
                 ):
        """Construct a new InfluxDBClient object."""
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._database = database
        self._timeout = timeout

        self._verify_ssl = verify_ssl

        self.use_udp = use_udp
        self.udp_port = udp_port
        self._session = requests.Session()
        if use_udp:
            self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self._scheme = "http"

        if ssl is True:
            self._scheme = "https"

        if proxies is None:
            self._proxies = {}
        else:
            self._proxies = proxies

        self._baseurl = "{0}://{1}:{2}".format(
            self._scheme,
            self._host,
            self._port)

        self._headers = {
            'Content-type': 'application/json',
            'Accept': 'text/plain'
        }

    def request(self, url, method='GET', params=None, data=None,
                expected_response_code=200, headers=None):
        """Make a HTTP request to the InfluxDB API.
        :param url: the path of the HTTP request, e.g. write, query, etc.
        :type url: str
        :param method: the HTTP method for the request, defaults to GET
        :type method: str
        :param params: additional parameters for the request, defaults to None
        :type params: dict
        :param data: the data of the request, defaults to None
        :type data: str
        :param expected_response_code: the expected response code of
            the request, defaults to 200
        :type expected_response_code: int
        :returns: the response from the request
        :rtype: :class:`requests.Response`
        :raises InfluxDBServerError: if the response code is any server error
            code (5xx)
        :raises InfluxDBClientError: if the response code is not the
            same as `expected_response_code` and is not a server error code
        """
        url = "{0}/{1}".format(self._baseurl, url)

        if headers is None:
            headers = self._headers

        if params is None:
            params = {}

        if isinstance(data, (dict, list)):
            data = json.dumps(data)

        # Try to send the request a maximum of three times. (see #103)
        # TODO (aviau): Make this configurable.
        for i in range(0, 3):
            try:
                response = self._session.request(
                    method=method,
                    url=url,
                    auth=(self._username, self._password),
                    params=params,
                    data=data,
                    headers=headers,
                    proxies=self._proxies,
                    verify=self._verify_ssl,
                    timeout=self._timeout
                )
                break
            except requests.exceptions.ConnectionError as e:
                if i < 2:
                    continue
                else:
                    raise e

        if response.status_code >= 500 and response.status_code < 600:
            raise InfluxDBServerError(response.content)
        elif response.status_code == expected_response_code:
            return response
        else:
            raise InfluxDBClientError(response.content, response.status_code)

    def validate_db(self):
        """Make sure the database exists

        Args:
            client (InfluxDBClient)

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

    @classmethod
    def create_dataset(cls, tags, **kwargs):
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

