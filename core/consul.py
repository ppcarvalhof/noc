# ----------------------------------------------------------------------
# Consul client
# ----------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ----------------------------------------------------------------------

# Third-party modules
import tornado.httpclient
import consul.base
import consul.tornado

# NOC modules
from noc.config import config


CONSUL_CONNECT_TIMEOUT = config.consul.connect_timeout
CONSUL_REQUEST_TIMEOUT = config.consul.request_timeout
CONSUL_NEAR_RETRY_TIMEOUT = config.consul.near_retry_timeout

ConsulRepeatableErrors = consul.base.Timeout


class ConsulHTTPClient(consul.tornado.HTTPClient):
    """
    Gentler version of tornado http client
    """

    async def _request(self, callback, request):
        client = tornado.httpclient.AsyncHTTPClient(force_instance=True, max_clients=1)
        try:
            response = await client.fetch(request)
        except tornado.httpclient.HTTPError as e:
            if e.code == 599:
                raise consul.base.Timeout
            response = e.response
        finally:
            client.close()
            # Resolve CurlHTTPClient circular dependencies
            client._force_timeout_callback = None
            client._multi = None
        return callback(self.response(response))

    def get(self, callback, path, params=None):
        uri = self.uri(path, params)
        request = tornado.httpclient.HTTPRequest(
            uri,
            method="GET",
            validate_cert=self.verify,
            connect_timeout=CONSUL_CONNECT_TIMEOUT,
            request_timeout=CONSUL_REQUEST_TIMEOUT,
        )
        return self._request(callback, request)

    def put(self, callback, path, params=None, data=""):
        uri = self.uri(path, params)
        request = tornado.httpclient.HTTPRequest(
            uri,
            method="PUT",
            body="" if data is None else data,
            validate_cert=self.verify,
            connect_timeout=CONSUL_CONNECT_TIMEOUT,
            request_timeout=CONSUL_REQUEST_TIMEOUT,
        )
        return self._request(callback, request)

    def delete(self, callback, path, params=None):
        uri = self.uri(path, params)
        request = tornado.httpclient.HTTPRequest(
            uri,
            method="DELETE",
            validate_cert=self.verify,
            connect_timeout=CONSUL_CONNECT_TIMEOUT,
            request_timeout=CONSUL_REQUEST_TIMEOUT,
        )
        return self._request(callback, request)

    def post(self, callback, path, params=None, data=""):
        uri = self.uri(path, params)
        request = tornado.httpclient.HTTPRequest(
            uri,
            method="POST",
            body=data,
            validate_cert=self.verify,
            connect_timeout=CONSUL_CONNECT_TIMEOUT,
            request_timeout=CONSUL_REQUEST_TIMEOUT,
        )
        return self._request(callback, request)


class ConsulClient(consul.base.Consul):
    def connect(self, host, port, scheme, verify=True, cert=None):
        return ConsulHTTPClient(host, port, scheme, verify=verify, cert=cert)
