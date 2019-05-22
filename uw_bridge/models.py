import json
from restclients_core import models


class BridgeCustomField(models.Model):
    REGID_NAME = "regid"
    EMPLOYEE_ID_NAME = "eid"
    STUDENT_ID_NAME = "sid"
    POS1_JOB_CODE = "job_code1"
    POS1_JOB_CLAS = "job_class1"  # employment program, job classification
    POS1_ORG_CODE = "org_code1"

    field_id = models.CharField(max_length=10)
    name = models.CharField(max_length=64)
    value_id = models.CharField(max_length=10, null=True, default=None)
    value = models.CharField(max_length=256, null=True, default=None)

    def is_regid(self):
        return self.name.lower() == BridgeCustomField.REGID_NAME

    def is_employee_id(self):
        return self.name.lower() == BridgeCustomField.EMPLOYEE_ID_NAME

    def is_student_id(self):
        return self.name.lower() == BridgeCustomField.STUDENT_ID_NAME

    def is_pos1_job_code(self):
        return self.name.lower() == BridgeCustomField.POS1_JOB_CODE

    def is_pos1_job_clas(self):
        return self.name.lower() == BridgeCustomField.POS1_JOB_CLAS

    def is_pos1_org_code(self):
        return self.name.lower() == BridgeCustomField.POS1_ORG_CODE

    def to_json(self):
        value = {"custom_field_id": self.field_id,
                 "value": self.value,
                 }
        try:
            if self.value_id:
                value["id"] = self.value_id
        except AttributeError:
            pass
        return value

    def __init__(self, *args, **kwargs):
        super(BridgeCustomField, self).__init__(*args, **kwargs)

    def __str__(self):
        data = self.to_json()
        data["name"] = self.name
        return json.dumps(data)


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
    unsubscribed = models.CharField(max_length=128, null=True, default=None)
    next_due_date = models.DateTimeField(null=True, default=None)
    completed_courses_count = models.IntegerField(default=-1)

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

    def to_json(self, omit_custom_fields=False):
        ret_user = {"uid": self.get_uid(),
                    "full_name": self.full_name,
                    "email": self.email,
                    }

        if len(self.custom_fields) > 0 or not omit_custom_fields:
            custom_fields_json = []
            for field in self.custom_fields:
                custom_fields_json.append(field.to_json())
            ret_user["custom_fields"] = custom_fields_json

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

        return ret_user

    def to_json_post(self):
        # for POST (add new or restore a user)
        return {"users": [self.to_json()]}

    def to_json_patch(self):
        # for PATCH, PUT (update)
        return {"user": self.to_json(omit_custom_fields=True)}

    def __str__(self, orig=True):
        json_data = self.to_json()
        if orig:
            json_data["deleted_at"] = self.deleted_at
            json_data["logged_in_at"] = self.logged_in_at
            json_data["updated_at"] = self.updated_at
            json_data["completed_courses_count"] =\
                self.completed_courses_count
        return json.dumps(json_data, default=str)

    def __init__(self, *args, **kwargs):
        super(BridgeUser, self).__init__(*args, **kwargs)
        self.custom_fields = []
        self.roles = []


class BridgeUserRole(models.Model):
    CAMPUS_ADMIN_NAME = 'campus admin'
    AUTHOR_NAME = 'author'

    role_id = models.CharField(max_length=64)
    name = models.CharField(max_length=64)

    def is_campus_admin(self):
        return self.name.lower() == BridgeUserRole.CAMPUS_ADMIN_NAME

    def is_author(self):
        return self.name.lower() == BridgeUserRole.AUTHOR_NAME

    def __init__(self, *args, **kwargs):
        super(BridgeUserRole, self).__init__(*args, **kwargs)
        # self.permissions = []   # unknown 2016/11

    def to_json(self):
        return {
            "id": self.role_id,
            "name": self.name,
            # "permissions": self.permissions
            }

    def __str__(self):
        return json.dumps(self.to_json())
