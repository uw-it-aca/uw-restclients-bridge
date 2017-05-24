"""
Contains Bridge DAO implementations.
"""

import logging
import os
from os.path import abspath, dirname
from restclients_core.dao import DAO


logger = logging.getLogger(__name__)


class Bridge_DAO(DAO):
    def service_name(self):
        return 'bridge'

    def service_mock_paths(self):
        return [abspath(os.path.join(dirname(__file__), "resources"))]

    def _get_basic_auth(self):
        return "%s:%s" % (
            self.get_service_setting("BASIC_AUTH_KEY", ""),
            self.get_service_setting("BASIC_AUTH_SECRET", ""))

    def _custom_headers(self, method, url, headers, body):
        headers["Authorization"] = "Basic %s" % self._get_basic_auth()
        return headers

    def _edit_mock_response(self, method, url, headers, body, response):
        if response.status == 404:
            backend = self.get_implementation()
            alternative_url = "%s.%s" % (url, method)
            new_resp = backend.load(method, alternative_url, headers, body)
            # assigning to response doesn't carry to the caller
            response.status = new_resp.status
            response.data = new_resp.data
            logger.debug("%s ==> %s", alternative_url, response.status)

    def is_mock(self):
        return self.get_implementation().is_mock()
