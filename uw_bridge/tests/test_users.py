from unittest import TestCase
from restclients_core.exceptions import DataFailureException
from uw_bridge.models import BridgeUser, BridgeCustomField
from uw_bridge.user import (
    get_user, get_all_users, get_user_by_id, _process_json_resp_data,
    _process_apage, add_user, admin_id_url, admin_uid_url, author_id_url,
    author_uid_url, ADMIN_URL_PREFIX, AUTHOR_URL_PREFIX, _upd_uid_req_body,
    change_uid, replace_uid, restore_user_by_id, update_user, CUSTOM_FIELDS,
    restore_user, delete_user, delete_user_by_id, _get_all_users_url)
from uw_bridge.tests import fdao_bridge_override


@fdao_bridge_override
class TestBridgeUser(TestCase):

    def test_admin_id_url(self):
        self.assertEqual(admin_id_url(None),
                         ADMIN_URL_PREFIX)
        self.assertEqual(admin_id_url(123),
                         ADMIN_URL_PREFIX + '/123')

    def test_author_id_url(self):
        self.assertEqual(author_id_url(None),
                         AUTHOR_URL_PREFIX)
        self.assertEqual(author_id_url(123),
                         AUTHOR_URL_PREFIX + '/123')

    def test_admin_uid_url(self):
        self.assertEqual(admin_uid_url(None),
                         ADMIN_URL_PREFIX)
        self.assertEqual(admin_uid_url('staff'),
                         ADMIN_URL_PREFIX + '/uid%3Astaff%40uw%2Eedu')

    def test_author_uid_url(self):
        self.assertEqual(author_uid_url(None),
                         AUTHOR_URL_PREFIX)
        self.assertEqual(author_uid_url('staff'),
                         AUTHOR_URL_PREFIX + '/uid%3Astaff%40uw%2Eedu')

    def test_process_apage(self):
        bridge_users = []
        bridge_users = _process_apage(
            {"meta": {},
             "linked": {
                 "custom_fields": [{"id": "9",
                                    "name": "Regid"}],
                 "custom_field_values": [
                     {"id": "754517",
                      "value": "6B79E4406A7D1",
                      "links": {
                          "custom_field": {"id": "9",
                                           "type": "custom_fields"}}}]},
             "users": [
                 {"id": "1",
                  "uid": "bill@uw.edu",
                  "hris_id": None,
                  "first_name": "Bill",
                  "last_name": "Smith",
                  "full_name": "Bill Smith",
                  "sortable_name": "Smith, Bill",
                  "email": "bill@uw.edu",
                  "locale": "en",
                  "roles": ["author"],
                  "name": "Bill Smith",
                  "avatar_url": None,
                  "updated_at": "2019-05-14T15:12:37.502-07:00",
                  "deleted_at": None,
                  "unsubscribed": None,
                  "welcomedAt": None,
                  "loggedInAt": "2019-05-14T10:17:34.757-07:00",
                  "passwordIsSet":False,
                  "hire_date": None,
                  "is_manager":False,
                  "job_title": "Software Engineer",
                  "bio": None,
                  "department": "Unix Engineering",
                  "anonymized": None,
                  "welcomeUrl": "...",
                  "passwordUrl": "...",
                  "next_due_date": None,
                  "completed_courses_count": 0,
                  "manager_name": None,
                  "manager_id": "10",
                  "links": {"custom_field_values": ["754517"]}}]},
            bridge_users, False, False)
        user = bridge_users[0]
        self.assertEqual(
            user.to_json_patch(),
            {'user': {
                'custom_fields': [{'custom_field_id': '9',
                                   'id': '754517',
                                   'value': '6B79E4406A7D1'}],
                'uid': 'bill@uw.edu',
                'full_name': 'Bill Smith',
                'email': 'bill@uw.edu',
                'id': 1,
                'first_name': 'Bill',
                'last_name': 'Smith',
                'sortable_name': 'Smith, Bill',
                'department': 'Unix Engineering',
                'job_title': 'Software Engineer',
                'manager_id': 10}})

    def test_process_err(self):
        self.assertRaises(KeyError,
                          _process_apage,
                          {"meta": {}, "linked": {}},
                          [],
                          include_deleted=False,
                          no_custom_fields=False)

        bridge_users = _process_json_resp_data(
            b'{"linked": {"custom_fields": [], "custom_field_values": []}}')
        self.assertEqual(len(bridge_users), 0)

    def test_get_user(self):
        user_list = get_user('javerage')
        self.assertEqual(len(user_list), 1)
        user = user_list[0]
        self.assertEqual(user.bridge_id, 195)
        self.assertEqual(user.first_name, "James")
        self.assertEqual(user.last_name, "Student")
        self.assertEqual(user.full_name, "James Student")
        self.assertEqual(user.get_sortable_name(),
                         "Student, James")
        self.assertEqual(user.email, "javerage@uw.edu")
        self.assertEqual(user.netid, "javerage")
        self.assertEqual(user.get_uid(), "javerage@uw.edu")
        self.assertFalse(user.is_deleted())
        self.assertEqual(
            str(user.updated_at), '2016-07-25 16:24:42.131000-07:00')
        self.assertEqual(
            str(user.logged_in_at), "2016-09-02 15:27:01.827000-07:00")
        self.assertEqual(user.next_due_date, None)
        self.assertEqual(user.completed_courses_count, 0)
        self.assertTrue(user.has_course_summary())
        self.assertTrue(user.no_learning_history())

        cus_field = user.get_custom_field(BridgeCustomField.REGID_NAME)
        self.assertEqual(cus_field.value_id, "1")
        self.assertEqual(cus_field.field_id, "5")
        self.assertEqual(cus_field.name, "regid")
        self.assertEqual(cus_field.value,
                         "9136CCB8F66711D5BE060004AC494FFE")

        self.assertEqual(len(user.roles), 3)
        self.assertTrue(user.roles[0].is_account_admin())
        self.assertTrue(user.roles[1].is_author())
        self.assertTrue(user.roles[2].is_campus_admin())
        self.assertIsNotNone(str(user))

    def test_get_user_with_deleted(self):
        user_list = get_user_by_id(17637,
                                   include_course_summary=True,
                                   include_deleted=True)
        self.assertEqual(len(user_list), 1)
        self.verify_bill(user_list[0])
        self.assertTrue(user_list[0].is_deleted())

        self.assertRaises(DataFailureException, get_user, 'unknown')

        self.assertRaises(DataFailureException, get_user_by_id, 19567)

    def verify_bill(self, user):
        self.assertEqual(user.bridge_id, 17637)
        self.assertEqual(user.first_name, "Bill Average")
        self.assertEqual(user.last_name, "Teacher")
        self.assertEqual(user.full_name, "Bill Average Teacher")
        self.assertEqual(user.get_sortable_name(), "Teacher, Bill Average")
        self.assertEqual(user.email, "bill@u.washington.edu")
        self.assertEqual(user.netid, "bill")
        self.assertTrue(user.is_manager)
        self.assertEqual(user.get_uid(), "bill@uw.edu")
        cus_field = user.get_custom_field(BridgeCustomField.REGID_NAME)
        self.assertEqual(cus_field.value,
                         "FBB38FE46A7C11D5A4AE0004AC494FFE")

    def test_get_all_users_url(self):
        self.assertEqual(
            _get_all_users_url(False, True),
            "/api/author/users?includes%5B%5D=&limit=1000")
        self.assertEqual(
            _get_all_users_url(False, False),
            "/api/author/users?includes%5B%5D=custom_fields&limit=1000")
        self.assertEqual(
            _get_all_users_url(True, False),
            "/api/author/users?includes%5B%5D=custom_fields&"
            "includes%5B%5D=course_summary&limit=1000")

    def test_get_alluser(self):
        user_list = get_all_users(include_course_summary=True)
        self.assertEqual(len(user_list), 2)
        user = user_list[0]
        self.assertEqual(user.full_name, "Eight Class Student")
        self.assertEqual(user.bridge_id, 106)
        cus_field = user.get_custom_field(BridgeCustomField.REGID_NAME)
        self.assertEqual(cus_field.value,
                         "12345678901234567890123456789012")
        user = user_list[1]
        self.assertEqual(user.full_name, "James Student")
        self.assertEqual(user.bridge_id, 195)
        cus_field = user.get_custom_field(BridgeCustomField.REGID_NAME)
        self.assertEqual(cus_field.value,
                         "9136CCB8F66711D5BE060004AC494FFE")

        user_list = get_all_users(include_course_summary=False)
        self.assertEqual(len(user_list), 3)
        self.assertEqual(user_list[0].bridge_id, 106)
        self.assertEqual(user_list[1].bridge_id, 195)
        self.assertEqual(user_list[2].bridge_id, 17)
        user = user_list[2]
        self.assertEqual(user.full_name, "None Average Student")
        self.assertEqual(user.bridge_id, 17)
        cus_field = user.get_custom_field(BridgeCustomField.REGID_NAME)
        self.assertEqual(cus_field.value,
                         "00000000000000000000000000000001")

        user_list = get_all_users(include_course_summary=False,
                                  no_custom_fields=True)
        self.assertEqual(len(user_list), 3)
        self.assertEqual(user_list[0].bridge_id, 106)
        self.assertEqual(user_list[1].bridge_id, 195)
        self.assertEqual(user_list[2].bridge_id, 17)
        self.assertEqual(len(user_list[2].custom_fields), 0)

    def test_add_user(self):
        regid = "12345678901234567890123456789012"
        cus_fie = CUSTOM_FIELDS.new_custom_field(
            BridgeCustomField.REGID_NAME, regid)
        user = BridgeUser()
        user.netid = "eight"
        user.full_name = "Eight Class Student"
        user.first_name = "Eight Class"
        user.last_name = "Student"
        user.email = "eight@uw.edu"
        user.custom_fields[cus_fie.name] = cus_fie

        added_users = add_user(user)
        self.assertEqual(len(added_users), 1)
        added = added_users[0]
        self.assertEqual(added.bridge_id, 123)
        self.assertEqual(added.first_name, "Eight Class")
        self.assertEqual(added.last_name, "Student")
        self.assertEqual(added.full_name, "Eight Class Student")
        self.assertEqual(added.get_sortable_name(), "Student, Eight Class")
        self.assertEqual(added.email, "eight@uw.edu")
        self.assertEqual(added.netid, "eight")
        self.assertEqual(added.get_uid(), "eight@uw.edu")
        self.assertEqual(
            str(added.updated_at), '2016-09-06 21:42:48.821000-07:00')
        # cus_field = added.custom_fields[0]
        # self.assertEqual(cus_field.value,
        #                 "12345678901234567890123456789012")
        # self.assertEqual(cus_field.field_id, "5")
        # self.assertEqual(cus_field.value_id, "922202")

    def test_delete_user(self):
        self.assertTrue(delete_user("javerage"))
        self.assertTrue(delete_user_by_id(195))
        try:
            reps = delete_user("staff")
        except Exception as ex:
            self.assertEqual(ex.status, 404)

    def test_upd_uid_req_body(self):
        print(_upd_uid_req_body("netid"))
        self.assertEqual(_upd_uid_req_body("netid"),
                         '{"user":{"uid":"netid@uw.edu"}}')

    def test_change_uid(self):
        self.assertRaises(DataFailureException,
                          change_uid,
                          195, "billchanged")

        users = change_uid(17637, "billchanged")
        self.verify_uid(users)
        self.assertEqual(len(users[0].custom_fields), 0)

        users = replace_uid("bill", "billchanged")
        self.verify_uid(users)
        self.assertEqual(len(users[0].custom_fields), 0)

        users = replace_uid("oldbill", "billchanged", no_custom_fields=False)
        self.verify_uid(users)
        self.assertEqual(len(users[0].custom_fields), 1)
        cus_field = users[0].get_custom_field(BridgeCustomField.REGID_NAME)
        self.assertEqual(cus_field.value,
                         "FBB38FE46A7C11D5A4AE0004AC494FFE")

    def test_restore_user(self):
        self.assertRaises(DataFailureException,
                          restore_user_by_id,
                          195)

        self.assertRaises(DataFailureException,
                          restore_user,
                          'javerage')

        users = restore_user_by_id(17637,
                                   include_manager=False,
                                   no_custom_fields=True)
        self.verify_uid(users)
        self.assertEqual(len(users[0].custom_fields), 0)

        users = restore_user_by_id(17637,
                                   include_manager=False)
        self.verify_uid(users)
        self.assertEqual(len(users[0].custom_fields), 1)
        cus_fie = users[0].get_custom_field(BridgeCustomField.REGID_NAME)
        self.assertEqual(cus_fie.value,
                         "FBB38FE46A7C11D5A4AE0004AC494FFE")

        users = restore_user_by_id(17637)
        self.verify_uid(users)
        self.assertTrue(users[0].has_manager())
        cus_fie = users[0].get_custom_field(BridgeCustomField.REGID_NAME)
        self.assertEqual(cus_fie.value,
                         "FBB38FE46A7C11D5A4AE0004AC494FFE")

        users = restore_user("billchanged",
                             include_manager=False,
                             no_custom_fields=True)
        self.verify_uid(users)
        self.assertFalse(users[0].has_custom_field())

        users = restore_user("billchanged", include_manager=False)
        self.verify_uid(users)
        cus_fie = users[0].get_custom_field(BridgeCustomField.REGID_NAME)
        self.assertEqual(cus_fie.value,
                         "FBB38FE46A7C11D5A4AE0004AC494FFE")

        users = restore_user("billchanged")
        self.verify_uid(users)
        self.assertTrue(users[0].has_manager())
        cus_fie = users[0].get_custom_field(BridgeCustomField.REGID_NAME)
        self.assertEqual(cus_fie.value,
                         "FBB38FE46A7C11D5A4AE0004AC494FFE")

    def test_update_user(self):
        orig_users = get_user_by_id(17637)
        upded_users = update_user(orig_users[0])
        self.assertEqual(len(upded_users), 1)
        self.verify_bill(upded_users[0])
        self.assertFalse(upded_users[0].is_deleted())
        self.assertEqual(
            str(upded_users[0].updated_at),
            '2016-09-08 13:58:20.635000-07:00')

        user = BridgeUser(netid='bill',
                          first_name='Bill Average',
                          last_name='Teacher',
                          email='bill@u.washington.edu',
                          full_name='Bill Average Teacher')
        upded_users = update_user(user)
        self.assertEqual(len(upded_users), 1)
        self.verify_bill(upded_users[0])

        orig_users = get_user('javerage')
        self.assertRaises(DataFailureException,
                          update_user, orig_users[0])

    def verify_uid(self, users):
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0].bridge_id, 17637)
        self.assertEqual(users[0].get_uid(), "billchanged@uw.edu")
