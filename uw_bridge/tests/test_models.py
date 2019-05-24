from datetime import datetime
from unittest import TestCase
from dateutil.parser import parse
from uw_bridge.models import BridgeUser, BridgeCustomField, BridgeUserRole


class TestBridgeModel(TestCase):

    def test_bridge_custom_field(self):
        self.assertEqual(len(BridgeCustomField.POS1), 5)
        bcf = BridgeCustomField(value_id="1",
                                field_id="5",
                                name=BridgeCustomField.REGID_NAME,
                                value="787")
        self.assertEqual(bcf.to_json(),
                         {'id': '1',
                          'value': '787',
                          'custom_field_id': '5'})
        self.assertTrue(bcf.is_regid())
        self.assertEqual(bcf.value, '787')
        self.assertIsNotNone(str(bcf))

        bcf = BridgeCustomField(field_id="5",
                                name=BridgeCustomField.REGID_NAME,
                                value="787")
        self.assertEqual(bcf.to_json(),
                         {'custom_field_id': '5',
                          'value': '787'})

    def test_bridge_user(self):
        user = BridgeUser()
        user.netid = "iamstudent"
        user.email = "iamstudent@uw.edu"
        user.full_name = "Iam Student"
        self.assertEqual(user.to_json(),
                         {'uid': 'iamstudent@uw.edu',
                          'full_name': 'Iam Student',
                          'email': 'iamstudent@uw.edu',
                          'custom_fields': []})
        self.assertEqual(user.get_uid(), "iamstudent@uw.edu")
        self.assertIsNotNone(str(user))
        self.assertFalse(user.has_bridge_id())
        self.assertFalse(user.has_bridge_id())
        self.assertFalse(user.has_last_name())
        self.assertFalse(user.has_first_name())
        self.assertFalse(user.has_manager())
        self.assertFalse(user.is_deleted())
        self.assertFalse(user.has_course_summary())
        self.assertFalse(user.no_learning_history())
        self.assertFalse(user.has_custom_field())

        user.first_name = "Iam A"
        user.last_name = "Student"
        self.assertTrue(user.has_last_name())
        self.assertTrue(user.has_first_name())
        self.assertEqual(user.get_sortable_name(),
                         "Student, Iam A")
        self.assertFalse(user.has_manager())

        user.updated_at = parse("2016-08-08T13:58:20.635-07:00")
        self.assertIsNotNone(str(user))

        user.manager_id = 1
        user.department = 'XYZ'
        self.assertTrue(user.has_manager())
        self.assertEqual(
            user.to_json(),
            {'custom_fields': [],
             'email': 'iamstudent@uw.edu',
             'first_name': 'Iam A',
             'full_name': 'Iam Student',
             'last_name': 'Student',
             'manager_id': 1,
             'department': 'XYZ',
             'sortable_name': 'Student, Iam A',
             'uid': 'iamstudent@uw.edu'}
        )
        self.assertIsNotNone(str(user))

        user.manager_netid = "a"
        user.manager_id = 0
        self.assertTrue(user.has_manager())
        self.assertEqual(
            user.to_json(),
            {'custom_fields': [],
             'email': 'iamstudent@uw.edu',
             'first_name': 'Iam A',
             'full_name': 'Iam Student',
             'last_name': 'Student',
             'department': 'XYZ',
             'manager_id': 'uid:a@uw.edu',
             'sortable_name': 'Student, Iam A',
             'uid': 'iamstudent@uw.edu'}
        )

        user.completed_courses_count = 3
        self.assertTrue(user.has_course_summary())
        self.assertFalse(user.no_learning_history())
        self.assertIsNotNone(str(user))

        regid = BridgeCustomField(
            field_id="5",
            name=BridgeCustomField.REGID_NAME,
            value="12345678901234567890123456789012")
        eid = BridgeCustomField(
            field_id="6",
            name=BridgeCustomField.EMPLOYEE_ID_NAME,
            value="1234567")

        user.custom_fields[regid.name] = regid
        user.custom_fields[eid.name] = eid
        self.assertTrue(user.has_custom_field())

        self.assertEqual(
            user.get_custom_field(BridgeCustomField.REGID_NAME).value,
            "12345678901234567890123456789012")

        self.assertIsNotNone(str(user))
        self.assertEqual(
            user.to_json(),
            {'custom_fields': [
                {'custom_field_id': '5',
                 'value': '12345678901234567890123456789012'},
                {'custom_field_id': '6', 'value': '1234567'}],
             'department': 'XYZ',
             'email': 'iamstudent@uw.edu',
             'first_name': 'Iam A',
             'full_name': 'Iam Student',
             'last_name': 'Student',
             'manager_id': 'uid:a@uw.edu',
             'sortable_name': 'Student, Iam A',
             'uid': 'iamstudent@uw.edu'})

        user.bridge_id = 123
        self.assertEqual(
            user.to_json_patch(),
            {'user': {
                'custom_fields': [
                    {'custom_field_id': '5',
                     'value': '12345678901234567890123456789012'},
                    {'custom_field_id': '6', 'value': '1234567'}],
                'uid': 'iamstudent@uw.edu',
                'id': 123,
                'email': 'iamstudent@uw.edu',
                'first_name': 'Iam A',
                'last_name': 'Student',
                'full_name': 'Iam Student',
                'department': 'XYZ',
                'manager_id': 'uid:a@uw.edu',
                'sortable_name': 'Student, Iam A',
            }})

        self.assertEqual(
            user.to_json_post(),
            {'users': [
                {'custom_fields': [
                    {'custom_field_id': '5',
                     'value': '12345678901234567890123456789012'},
                    {'custom_field_id': '6', 'value': '1234567'}],
                 'uid': 'iamstudent@uw.edu',
                 'id': 123,
                 'email': 'iamstudent@uw.edu',
                 'first_name': 'Iam A',
                 'last_name': 'Student',
                 'full_name': 'Iam Student',
                 'department': 'XYZ',
                 'manager_id': 'uid:a@uw.edu',
                 'sortable_name': 'Student, Iam A'}]})

    def test_bridge_user_role(self):
        role1 = BridgeUserRole(role_id='9a0d0b25', name='Campus Admin')
        self.assertEqual(role1.to_json(),
                         {'id': '9a0d0b25', 'name': 'Campus Admin'})
        self.assertTrue(role1.is_campus_admin())

        role = BridgeUserRole(role_id='author', name='Author')
        self.assertEqual(role.to_json(),
                         {'id': 'author', 'name': 'Author'})
        self.assertTrue(role.is_author())
        self.assertIsNotNone(str(role))

        role = BridgeUserRole(role_id="account_admin", name="Account Admin")
        self.assertTrue(role.is_account_admin())

        role = BridgeUserRole(role_id="it_admin", name="IT Admin")
        self.assertTrue(role.is_it_admin())

        role = BridgeUserRole(role_id="admin", name="Admin")
        self.assertTrue(role.is_admin())
