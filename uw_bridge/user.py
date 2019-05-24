from datetime import datetime
import json
import logging
import re
from dateutil.parser import parse
from restclients_core.exceptions import InvalidNetID
from uw_bridge.models import BridgeUser, BridgeCustomField, BridgeUserRole
from uw_bridge.custom_fields import CustomFields
from uw_bridge.user_roles import UserRoles
from uw_bridge import (
    get_resource, patch_resource, post_resource, delete_resource)


CUSTOM_FIELDS = CustomFields()
USER_ROLES = UserRoles()
logger = logging.getLogger(__name__)
ADMIN_URL_PREFIX = "/api/admin/users"
AUTHOR_URL_PREFIX = "/api/author/users"
INCLUDES = "includes%5B%5D="
CUSTOM_FIELD = "{0}custom_fields".format(INCLUDES)
COURSE_SUMMARY = "{0}course_summary".format(INCLUDES)
MANAGER = "{0}manager".format(INCLUDES)
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


def _upd_uid_req_body(new_uwnetid):
    return "{0}{1}@uw.edu{2}".format('{"user":{"uid":"', new_uwnetid, '"}}')


def change_uid(bridge_id, new_uwnetid, no_custom_fields=True):
    """
    :param bridge_id: integer
    :param no_custom_fields: return objects with or without custom_fields
    Return a list of BridgeUser objects
    """
    url = author_id_url(bridge_id, no_custom_fields=no_custom_fields)
    resp = patch_resource(url, _upd_uid_req_body(new_uwnetid))
    return _process_json_resp_data(resp,
                                   no_custom_fields=no_custom_fields)


def replace_uid(old_uwnetid, new_uwnetid, no_custom_fields=True):
    """
    :param no_custom_fields: return objects with or without custom_fields
    Return a list of BridgeUser objects
    """
    url = author_uid_url(old_uwnetid, no_custom_fields=no_custom_fields)
    resp = patch_resource(url, _upd_uid_req_body(new_uwnetid))
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


def __add_includes_to_url(url, include_manager, include_course_summary):
    if include_course_summary:
        url = "{0}&{1}".format(url, COURSE_SUMMARY)
    if include_manager:
        url = "{0}&{1}".format(url, MANAGER)
    return url


def get_user(uwnetid,
             include_course_summary=True,
             include_manager=True):
    """
    Return a list of BridgeUsers objects with custom fields,
    only returns the active records associated with the uid.
    """
    url = __add_includes_to_url(
        author_uid_url(uwnetid, no_custom_fields=False),
        include_manager, include_course_summary)
    resp = get_resource(url)
    return _process_json_resp_data(resp)


def get_user_by_id(bridge_id,
                   include_course_summary=True,
                   include_manager=True,
                   include_deleted=True):
    """
    :param bridge_id: integer
    Return a list of BridgeUsers objects of active (and deleted)
    records associated with the bridge_id with custom fields.
    """
    url = __add_includes_to_url(
        author_id_url(bridge_id, no_custom_fields=False),
        include_manager, include_course_summary)
    if include_deleted:
        url = "{0}&{1}".format(url, "with_deleted=true")
    resp = get_resource(url)
    return _process_json_resp_data(resp, include_deleted=include_deleted)


def _get_all_users_url(include_course_summary, no_custom_fields):
    if not include_course_summary and no_custom_fields:
        url = "{0}?{1}".format(author_uid_url(None), INCLUDES)
    else:
        url = author_uid_url(None, no_custom_fields=no_custom_fields)
        if include_course_summary:
            url = "{0}&{1}".format(url, COURSE_SUMMARY)
    return "{0}&{1}".format(url, PAGE_MAX_ENTRY)


def get_all_users(include_course_summary=True, no_custom_fields=False):
    """
    Return a list of BridgeUser objects of the active user records.
    """
    resp = get_resource(
        _get_all_users_url(include_course_summary, no_custom_fields))
    return _process_json_resp_data(resp,
                                   no_custom_fields=no_custom_fields)


def __restore_user_url(base_url, include_manager):
    return __add_includes_to_url(
        "{0}/{1}?{2}".format(base_url, RESTORE_SUFFIX, CUSTOM_FIELD),
        include_manager, False)


def restore_user(uwnetid,
                 include_manager=True,
                 no_custom_fields=False):
    """
    :param no_custom_fields: return objects with or without custom_fields
    Return a list of BridgeUsers objects
    """
    url = __restore_user_url(author_uid_url(uwnetid), include_manager)
    resp = post_resource(url, '{}')
    return _process_json_resp_data(resp, no_custom_fields=no_custom_fields)


def restore_user_by_id(bridge_id,
                       include_manager=True,
                       no_custom_fields=False):
    """
    :param bridge_id: integer
    :param no_custom_fields: return objects with or without custom_fields
    Return a list of BridgeUsers objects
    """
    url = __restore_user_url(author_id_url(bridge_id), include_manager)
    resp = post_resource(url, '{}')
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
                            include_deleted=False,
                            no_custom_fields=False):
    """
    process the response and return a list of BridgeUser
    """
    bridge_users = []
    while True:
        resp_data = json.loads(resp)
        link_url = None
        if (resp_data.get("meta") is not None and
                resp_data["meta"].get("next") is not None):
            link_url = resp_data["meta"]["next"]

        try:
            bridge_users = _process_apage(resp_data,
                                          bridge_users,
                                          include_deleted,
                                          no_custom_fields)
        except Exception as err:
            logger.error("{0} in {1}".format(str(err), resp_data))

        if link_url is None:
            break
        resp = get_resource(link_url)

    return bridge_users


def _process_apage(resp_data,
                   bridge_users,
                   include_deleted,
                   no_custom_fields):
    custom_fields_value_dict = _get_custom_fields_dict(resp_data["linked"],
                                                       no_custom_fields)
    # a dict of {custom_field_value_id: BridgeCustomField}

    for user_data in resp_data["users"]:
        if (include_deleted is False and
                user_data.get("deleted_at") is not None):
            # skip deleted entry
            continue

        user = BridgeUser(
            bridge_id=int(user_data["id"]),
            netid=re.sub('@uw.edu', '', user_data["uid"]),
            email=user_data.get("email", ""),
            full_name=user_data.get("full_name", ""),
            first_name=user_data.get("first_name", None),
            last_name=user_data.get("last_name", None),
            department=user_data.get("department", None),
            job_title=user_data.get("job_title", None),
            locale=user_data.get("locale", "en"),
            is_manager=user_data.get("is_manager", None),
            deleted_at=None,
            logged_in_at=None,
            updated_at=None,
            unsubscribed=user_data.get("unsubscribed", None),
            next_due_date=None,
            completed_courses_count=user_data.get("completed_courses_count",
                                                  -1),
            )

        if user_data.get("manager_id") is not None:
            user.manager_id = int(user_data["manager_id"])

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
                    custom_field = custom_fields_value_dict[custom_field_value]
                    user.custom_fields[custom_field.name] = custom_field

        if user_data.get("roles") is not None:
            for role_data in user_data["roles"]:
                user.roles.append(
                    USER_ROLES.new_user_role_by_id(role_data))

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
        field_id = id_name_pair.get("id")
        name = id_name_pair.get("name")
        if field_id is not None and name is not None:
            custom_fields_name_dict[field_id] = name.lower()

    for value in linked_data["custom_field_values"]:
        custom_field = BridgeCustomField(
            value_id=value["id"],
            value=value["value"],
            field_id=value["links"]["custom_field"]["id"]
            )
        custom_field.name = custom_fields_name_dict[custom_field.field_id]
        custom_fields_value_dict[custom_field.value_id] = custom_field

    return custom_fields_value_dict
