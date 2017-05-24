import logging
import json
from uw_bridge.models import BridgeCustomField
from uw_bridge import get_resource


logger = logging.getLogger(__name__)
URL_PREFIX = "/api/author/custom_fields"


def get_custom_fields():
    """
    Return a list of BridgeCustomField objects
    """
    resp = get_resource(URL_PREFIX)
    return _process_json_resp_data(resp)


def _process_json_resp_data(resp):
    fields = []
    resp_data = json.loads(resp)
    if "custom_fields" in resp_data and\
            len(resp_data["custom_fields"]) > 0:
        for value in resp_data["custom_fields"]:
            if "id" in value and "name" in value:
                custom_field = BridgeCustomField(field_id=value["id"],
                                                 name=value["name"]
                                                 )
                fields.append(custom_field)
    return fields


def get_regid_field_id():
    fields = get_custom_fields()
    if len(fields) > 0:
        for cf in fields:
            if cf.is_regid():
                return cf.field_id
    return None


def new_regid_custom_field(uwregid):
    """
    Return a BridgeCustomField object for REGID
    to be used in a POST, PATCH request
    """
    return BridgeCustomField(
        field_id=get_regid_field_id(),
        name=BridgeCustomField.REGID_NAME,
        value=uwregid
        )
