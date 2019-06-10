# REST client for the Bridge Web Service API
# Uw-Restclients-Bridge

[![Build Status](https://api.travis-ci.com/uw-it-aca/uw-restclients-bridge.svg?branch=master)](https://travis-ci.com/uw-it-aca/uw-restclients-bridge)
[![Coverage Status](https://coveralls.io/repos/uw-it-aca/uw-restclients-bridge/badge.svg?branch=master)](https://coveralls.io/r/uw-it-aca/uw-restclients-bridge?branch=master)
[![PyPi Version](https://img.shields.io/pypi/v/uw-restclients-bridge.svg)](https://pypi.python.org/pypi/uw-restclients-bridge)
![Python versions](https://img.shields.io/pypi/pyversions/uw-restclients-bridge.svg)

Installation:

    pip install Uw-Restclients-Bridge

To use this client, you'll need these settings in your application or script:

    # Specifies whether requests should use live or mocked resources,
    # acceptable values are 'Live' or 'Mock' (default)
    RESTCLIENTS_BRIDGE_DAO_CLASS='Live'

    # Basic Auth key and value pair
    RESTCLIENTS_BRIDGE_BASIC_AUTH_KEY='...'
    RESTCLIENTS_BRIDGE_BASIC_AUTH_SECRET='...'

    # Bridge WS URL prefix
    RESTCLIENTS_BRIDGE_HOST='https://...bridgeapp.com'

Optional settings:

    # Customizable parameters for urllib3
    RESTCLIENTS_BRIDGE_TIMEOUT=60
    RESTCLIENTS_BRIDGE_POOL_SIZE=10
