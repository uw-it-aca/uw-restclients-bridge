# Copyright 2022 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

import json
from restclients_core import models


class BridgeCustomField(models.Model):

    # Field names:
    REGID_NAME = "regid"
    EMPLOYEE_ID_NAME = "employee_id"
    STUDENT_ID_NAME = "student_id"

    POS1_BUDGET_CODE = "pos1_budget_code"
    POS1_JOB_CODE = "pos1_job_code"
    POS1_JOB_CLAS = "pos1_job_class"    # job classification
    POS1_LOCATION = "pos1_location"
    POS1_ORG_CODE = "pos1_org_code"
    POS1_ORG_NAME = "pos1_org_name"
    POS1_UNIT_CODE = "pos1_unit_code"

    POS2_BUDGET_CODE = "pos2_budget_code"
    POS2_JOB_CODE = "pos2_job_code"
    POS2_JOB_CLAS = "pos2_job_class"
    POS2_LOCATION = "pos2_location"
    POS2_ORG_CODE = "pos2_org_code"
    POS2_ORG_NAME = "pos2_org_name"
    POS2_UNIT_CODE = "pos2_unit_code"

    field_id = models.CharField(max_length=10)
    name = models.CharField(max_length=64)
    value_id = models.CharField(max_length=10, null=True, default=None)
    value = models.CharField(max_length=256, null=True, default=None)

    def to_json(self):
        value = {"custom_field_id": self.field_id,
                 "value": self.value}
        if self.value_id is not None:
            value["id"] = self.value_id
        return value

    def to_json_short(self):
        return {"name": self.name, "value": self.value}

    def __init__(self, *args, **kwargs):
        super(BridgeCustomField, self).__init__(*args, **kwargs)

    def __str__(self):
        return json.dumps(self.to_json_short())


class BridgeUser(models.Model):
    bridge_id = models.IntegerField(default=0)
    netid = models.CharField(max_length=32)
    email = models.CharField(max_length=128, default="")
    full_name = models.CharField(max_length=256, default="")
    first_name = models.CharField(max_length=128, null=True, default=None)
    last_name = models.CharField(max_length=128, null=True, default=None)
    department = models.CharField(max_length=256, null=True, default=None)
    job_title = models.CharField(max_length=160, null=True, default=None)
    is_manager = models.NullBooleanField(default=None)
    locale = models.CharField(max_length=2, default='en')
    manager_id = models.IntegerField(default=0)
    manager_netid = models.CharField(max_length=32, null=True, default=None)
    deleted_at = models.DateTimeField(null=True, default=None)
    logged_in_at = models.DateTimeField(null=True, default=None)
    updated_at = models.DateTimeField(null=True, default=None)
    unsubscribed = models.NullBooleanField(default=None)
    next_due_date = models.DateTimeField(null=True, default=None)
    completed_courses_count = models.IntegerField(default=-1)

    def add_role(self, user_role):
        if user_role not in self.roles:
            self.roles.append(user_role)

    def delete_role(self, user_role):
        if user_role in self.roles:
            self.roles.remove(user_role)

    def is_deleted(self):
        return self.deleted_at is not None

    def get_uid(self):
        return "{}@uw.edu".format(self.netid)

    def get_sortable_name(self):
        return "{0}, {1}".format(self.last_name, self.first_name)

    def has_course_summary(self):
        # having the data field
        return self.completed_courses_count >= 0

    def has_bridge_id(self):
        return self.bridge_id > 0

    def has_first_name(self):
        return self.first_name and len(self.first_name) > 0

    def has_last_name(self):
        return self.last_name and len(self.last_name) > 0

    def has_manager(self):
        return self.manager_id > 0 or self.manager_netid is not None

    def no_learning_history(self):
        return self.has_course_summary() and self.completed_courses_count == 0

    def get_custom_field(self, field_name):
        # return the corresponding BridgeCustomField object
        return self.custom_fields.get(field_name)

    def update_custom_field(self, field_name, new_value):
        # update an existing custom field
        cf = self.get_custom_field(field_name)
        if cf is not None:
            cf.value = new_value

    def has_custom_field(self):
        return len(self.custom_fields.keys()) > 0

    def to_json(self, omit_custom_fields=False):
        ret_user = {"uid": self.get_uid(),
                    "full_name": self.full_name,
                    "email": self.email,
                    }

        if self.has_bridge_id():
            ret_user["id"] = self.bridge_id

        if self.has_first_name():
            ret_user["first_name"] = self.first_name

        if self.has_last_name():
            ret_user["last_name"] = self.last_name

        if self.has_last_name() and self.has_first_name():
            ret_user["sortable_name"] = self.get_sortable_name()

        if self.department is not None:
            ret_user["department"] = self.department

        if self.job_title is not None:
            ret_user["job_title"] = self.job_title

        if self.manager_id > 0:
            ret_user["manager_id"] = self.manager_id
        elif self.manager_netid is not None:
            ret_user["manager_id"] = "uid:{0}@uw.edu".format(
                self.manager_netid)
        else:
            ret_user["manager_id"] = None

        return ret_user

    def custom_fields_json(self):
        return [field.to_json() for field in self.custom_fields.values()]

    def to_json_post(self):
        # for POST (add new or restore a user)
        user_data = self.to_json()
        user_data["custom_field_values"] = self.custom_fields_json()
        return {"users": [user_data]}

    def to_json_patch(self):
        # for PATCH, PUT (update)
        user_data = self.to_json()
        user_data["custom_field_values"] = self.custom_fields_json()
        return {"user": user_data}

    def roles_to_json(self):
        return [r.role_id for r in self.roles]

    def __str__(self):
        json_data = self.to_json()
        json_data["deleted_at"] = self.deleted_at
        json_data["logged_in_at"] = self.logged_in_at
        json_data["updated_at"] = self.updated_at
        json_data["completed_courses_count"] = self.completed_courses_count

        if len(self.custom_fields):
            json_data["custom_fields"] = [f.to_json_short()
                                          for f in self.custom_fields.values()]

        if len(self.roles) > 0:
            json_data["roles"] = self.roles_to_json()

        return json.dumps(json_data, default=str)

    def __init__(self, *args, **kwargs):
        super(BridgeUser, self).__init__(*args, **kwargs)
        self.custom_fields = {}
        # A user may have a long list of custom fields.
        # For a quick lookup, use a dict of {field_name: BridgeCustomField}
        self.roles = []


class BridgeUserRole(models.Model):
    # Role names
    ACCOUNT_ADMIN_NAME = "Account Admin"
    ADMIN_NAME = "Admin"
    AUTHOR_NAME = "Author"
    CAMPUS_ADMIN_NAME = "Campus Admin"
    IT_ADMIN_NAME = "IT Admin"

    role_id = models.CharField(max_length=64)
    name = models.CharField(max_length=64, null=True, default=None)

    def is_account_admin(self):
        return self.name == BridgeUserRole.ACCOUNT_ADMIN_NAME

    def is_admin(self):
        return self.name == BridgeUserRole.ADMIN_NAME

    def is_author(self):
        return self.name == BridgeUserRole.AUTHOR_NAME

    def is_campus_admin(self):
        return self.name == BridgeUserRole.CAMPUS_ADMIN_NAME

    def is_it_admin(self):
        return self.name == BridgeUserRole.IT_ADMIN_NAME

    def __eq__(self, role):
        return self.role_id == role.role_id

    def __init__(self, *args, **kwargs):
        super(BridgeUserRole, self).__init__(*args, **kwargs)
        # self.permissions = []   # unknown 2016/11

    def to_json(self):
        return {"id": self.role_id, "name": self.name}

    def __str__(self):
        return json.dumps(self.to_json())
