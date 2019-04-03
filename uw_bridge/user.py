from datetime import datetime
import json
import logging
import re
from dateutil.parser import parse
from restclients_core.exceptions import InvalidNetID
from uw_pws import PWS
from uw_bridge.models import BridgeUser, BridgeUserRole, BridgeCustomField
from uw_bridge import get_resource, patch_resource, post_resource,\
    delete_resource


logger = logging.getLogger(__name__)
ADMIN_URL_PREFIX = "/api/admin/users"
AUTHOR_URL_PREFIX = "/api/author/users"
CUSTOM_FIELD = "includes%5B%5D=custom_fields"
COURSE_SUMMARY = "includes%5B%5D=course_summary"
PAGE_MAX_ENTRY = "limit=1000"
RESTORE_SUFFIX = "restore"


def __add_custom_field_to_url(base_url, no_custom_fields):
    if no_custom_fields is True:
        return base_url
    return "{0}?{1}".format(base_url, CUSTOM_FIELD)


def admin_id_url(bridge_id, no_custom_fields=True):
    url = ADMIN_URL_PREFIX
    if bridge_id:
        url = "{0}/{1:d}".format(url, bridge_id)
    return __add_custom_field_to_url(url, no_custom_fields)


def admin_uid_url(uwnetid, no_custom_fields=True):
    url = ADMIN_URL_PREFIX
    if uwnetid is not None:
        url = "{0}/uid%3A{1}%40uw%2Eedu".format(url, uwnetid)
    return __add_custom_field_to_url(url, no_custom_fields)


def author_id_url(bridge_id, no_custom_fields=True):
    url = AUTHOR_URL_PREFIX
    if bridge_id:
        url = "{0}/{1:d}".format(url, bridge_id)
    return __add_custom_field_to_url(url, no_custom_fields)


def author_uid_url(uwnetid, no_custom_fields=True):
    url = AUTHOR_URL_PREFIX
    if uwnetid is not None:
        url = "{0}/uid%3A{1}%40uw%2Eedu".format(url, uwnetid)
    return __add_custom_field_to_url(url, no_custom_fields)


def add_user(bridge_user):
    """
    Add the bridge_user given
    Return a list of BridgeUser objects with custom fields
    """
    url = admin_uid_url(None, no_custom_fields=False)
    body = json.dumps(bridge_user.to_json_post(), separators=(',', ':'))
    resp = post_resource(url, body)
    return _process_json_resp_data(resp, no_custom_fields=True)


def __upd_uid_req_body(new_uwnetid):
    return "{0}{1}@uw.edu'}}".format("{'user': {'uid': '", new_uwnetid)


def change_uid(bridge_id, new_uwnetid, no_custom_fields=True):
    """
    :param bridge_id: integer
    :param no_custom_fields: return objects with or without custom_fields
    Return a list of BridgeUser objects
    """
    url = author_id_url(bridge_id, no_custom_fields=no_custom_fields)
    resp = patch_resource(url, __upd_uid_req_body(new_uwnetid))
    return _process_json_resp_data(resp,
                                   no_custom_fields=no_custom_fields)


def replace_uid(old_uwnetid, new_uwnetid, no_custom_fields=True):
    """
    :param no_custom_fields: return objects with or without custom_fields
    Return a list of BridgeUser objects
    """
    url = author_uid_url(old_uwnetid, no_custom_fields=no_custom_fields)
    resp = patch_resource(url, __upd_uid_req_body(new_uwnetid))
    return _process_json_resp_data(resp,
                                   no_custom_fields=no_custom_fields)


def delete_user(uwnetid):
    """
    Return True when the HTTP repsonse status is 204 -
    the user is deleted successfully
    """
    resp = delete_resource(admin_uid_url(uwnetid))
    return resp.status == 204


def delete_user_by_id(bridge_id):
    """
    :param bridge_id: integer
    Return True when the HTTP repsonse status is 204 -
    the user is deleted successfully
    """
    resp = delete_resource(admin_id_url(bridge_id))
    return resp.status == 204


def get_user(uwnetid, exclude_deleted=True, include_course_summary=True):
    """
    Return a list of BridgeUsers objects with custom fields
    """
    url = author_uid_url(uwnetid, no_custom_fields=False)
    if include_course_summary:
        url = "{0}&{1}".format(url, COURSE_SUMMARY)
    resp = get_resource(url)
    return _process_json_resp_data(resp, exclude_deleted=exclude_deleted)


def get_user_by_id(bridge_id, exclude_deleted=True,
                   include_course_summary=True):
    """
    :param bridge_id: integer
    Return a list of BridgeUsers objects with custom fields
    """
    url = author_id_url(bridge_id, no_custom_fields=False)
    if include_course_summary:
        url = "{0}&{1}".format(url, COURSE_SUMMARY)
    resp = get_resource(url)
    return _process_json_resp_data(resp, exclude_deleted=exclude_deleted)


def get_all_users(include_course_summary=True):
    """
    Return a list of BridgeUser objects with custom fields.
    """
    url = author_uid_url(None, no_custom_fields=False)

    if include_course_summary:
        url = "{0}&{1}".format(url, COURSE_SUMMARY)

    url = "{0}&{1}".format(url, PAGE_MAX_ENTRY)

    resp = get_resource(url)

    return _process_json_resp_data(resp)


def __restore_user_url(base_url):
    return "{0}/{1}?{2}".format(base_url, RESTORE_SUFFIX, CUSTOM_FIELD)


def restore_user(uwnetid, no_custom_fields=True):
    """
    :param no_custom_fields: return objects with or without custom_fields
    Return a list of BridgeUsers objects
    """
    resp = post_resource(__restore_user_url(author_uid_url(uwnetid)), '{}')
    return _process_json_resp_data(resp, no_custom_fields=no_custom_fields)


def restore_user_by_id(bridge_id, no_custom_fields=True):
    """
    :param bridge_id: integer
    :param no_custom_fields: return objects with or without custom_fields
    Return a list of BridgeUsers objects
    """
    resp = post_resource(__restore_user_url(author_id_url(bridge_id)), '{}')
    return _process_json_resp_data(resp, no_custom_fields=no_custom_fields)


def update_user(bridge_user):
    """
    Update only the user attributes provided.
    Return a list of BridgeUsers objects with custom fields.
    """
    if bridge_user.bridge_id:
        url = author_id_url(bridge_user.bridge_id, no_custom_fields=False)
    else:
        url = author_uid_url(bridge_user.netid, no_custom_fields=False)
    body = json.dumps(bridge_user.to_json_patch(), separators=(',', ':'))
    resp = patch_resource(url, body)
    return _process_json_resp_data(resp)


def _process_json_resp_data(resp,
                            exclude_deleted=True,
                            no_custom_fields=False):
    """
    process the response and return a list of BridgeUser
    """
    bridge_users = []
    while True:
        resp_data = json.loads(resp)
        link_url = None
        if "meta" in resp_data and\
                "next" in resp_data["meta"]:
            link_url = resp_data["meta"]["next"]

        try:
            bridge_users = _process_apage(resp_data, bridge_users,
                                          exclude_deleted,
                                          no_custom_fields)
        except Exception as err:
            logger.error("{0} in {1}".format(str(err), resp_data))

        if link_url is None:
            break
        resp = get_resource(link_url)

    return bridge_users


def _process_apage(resp_data, bridge_users,
                   exclude_deleted, no_custom_fields):
    custom_fields_value_dict = _get_custom_fields_dict(resp_data["linked"],
                                                       no_custom_fields)
    # a dict of {custom_field_value_id: BridgeCustomField}

    for user_data in resp_data["users"]:

        if (exclude_deleted and
            "deleted_at" in user_data and
                user_data.get("deleted_at") is not None):
            # skip deleted entry
            continue

        user = BridgeUser(
            bridge_id=int(user_data["id"]),
            netid=re.sub('@uw.edu', '', user_data["uid"]),
            email=user_data.get("email", ""),
            name=user_data.get("name", None),
            full_name=user_data.get("full_name", ""),
            first_name=user_data.get("first_name", None),
            last_name=user_data.get("last_name", None),
            sortable_name=user_data.get("sortable_name", None),
            locale=user_data.get("locale", "en"),
            is_manager=user_data.get("is_manager"),
            avatar_url=user_data.get("avatar_url", None),
            deleted_at=None,
            logged_in_at=None,
            updated_at=None,
            unsubscribed=user_data.get("unsubscribed", None),
            next_due_date=None,
            completed_courses_count=user_data.get("completed_courses_count",
                                                  -1),
            )

        if user_data.get("deleted_at") is not None:
            user.deleted_at = parse(user_data["deleted_at"])

        if user_data.get("loggedInAt") is not None:
            user.logged_in_at = parse(user_data["loggedInAt"])

        if user_data.get("updated_at") is not None:
            user.updated_at = parse(user_data["updated_at"])

        if user_data.get("next_due_date") is not None:
            user.next_due_date = parse(user_data["next_due_date"])

        if (no_custom_fields is False and
                "links" in user_data and len(user_data["links"]) > 0 and
                "custom_field_values" in user_data["links"]):
            values = user_data["links"]["custom_field_values"]
            for custom_field_value in values:
                if custom_field_value in custom_fields_value_dict:
                    user.custom_fields.append(
                        custom_fields_value_dict[custom_field_value])

        if "roles" in user_data and len(user_data["roles"]) > 0:
            for role_data in user_data["roles"]:
                user.roles.append(_get_roles_from_json(role_data))

        bridge_users.append(user)

    return bridge_users


def _get_custom_fields_dict(linked_data, no_custom_fields):
    """
    :except KeyError:
    """
    custom_fields_value_dict = {}
    # a dict of {value_id: BridgeCustomField}

    if no_custom_fields is True:
        return custom_fields_value_dict

    custom_fields_name_dict = {}
    # a dict of {custom_field_id: name}

    for id_name_pair in linked_data["custom_fields"]:
        custom_fields_name_dict[id_name_pair["id"]] = id_name_pair["name"]

    for value in linked_data["custom_field_values"]:
        custom_field = BridgeCustomField(
            value_id=value["id"],
            value=value["value"],
            field_id=value["links"]["custom_field"]["id"]
            )
        custom_field.name = custom_fields_name_dict[custom_field.field_id]
        custom_fields_value_dict[custom_field.value_id] = custom_field

    return custom_fields_value_dict


def get_regid_from_custom_fields(custom_fields):
    if custom_fields is not None and\
            len(custom_fields) > 0:
        for custom_field in custom_fields:
            if custom_field.is_regid():
                return custom_field.value
    return None


def _get_roles_from_json(role_data):
    # roles in data is a list of strings currently.
    return BridgeUserRole(role_id=role_data,
                          name=role_data)
