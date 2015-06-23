#!/usr/bin/python

import clc_ansible_module.clc_alert_policy as clc_alert_policy
from clc_ansible_module.clc_alert_policy import ClcAlertPolicy
import clc as clc_sdk
import mock
from mock import patch, create_autospec
import os
import unittest

# This is a pretty brute-force attack at unit testing.
# This is my first stab, so anyone reading this who is more Python-inclined
# is both welcome and encouraged to make it better.

        # self.clc.v2.SetCredentials.assert_called_once_with(api_username='hansolo', api_passwd='falcon')
def FakeAnsibleModule():
    module = mock.MagicMock()
    module.check_mode = False
    module.params = {}
    return module

class TestClcAlertPolicy(unittest.TestCase):

    def setUp(self):
        self.clc = mock.MagicMock()
        self.module = FakeAnsibleModule()
        self.policy = ClcAlertPolicy(self.module)
        self.policy.module.exit_json = mock.MagicMock()



    def notestNoCreds(self):
        self.policy.module.fail_json = mock.MagicMock(side_effect=Exception('nocreds'))
        try:
            result = self.policy.do_work()
        except:
            pass
        self.assertEqual(self.policy.module.fail_json.called, True)

    def testLoginMagic(self):
        self.policy.clc.v2.SetCredentials = mock.MagicMock()
        with patch.dict('os.environ', {'CLC_V2_API_USERNAME':'passWORD', 'CLC_V2_API_PASSWD':'UsErnaME'}):
            try:
                self.policy.process_request()
            except:
                # It'll die, and we don't care
                pass

        self.policy.clc.v2.SetCredentials.assert_called_once_with(api_username='passWORD',api_passwd='UsErnaME')

    @patch.object(ClcAlertPolicy, 'clc')
    def test_set_clc_credentials_from_env(self, mock_clc_sdk):
        with patch.dict('os.environ', {'CLC_V2_API_TOKEN': 'dummyToken',
                                       'CLC_ACCT_ALIAS': 'TEST'}):
            under_test = ClcAlertPolicy(self.module)
            under_test._set_clc_credentials_from_env()
        self.assertEqual(under_test.clc._LOGIN_TOKEN_V2, 'dummyToken')
        self.assertFalse(mock_clc_sdk.v2.SetCredentials.called)
        self.assertEqual(self.module.fail_json.called, False)

    @patch.object(ClcAlertPolicy, 'clc')
    def test_set_clc_credentials_w_creds(self, mock_clc_sdk):
        with patch.dict('os.environ', {'CLC_V2_API_USERNAME': 'dummyuser', 'CLC_V2_API_PASSWD': 'dummypwd'}):
            under_test = ClcAlertPolicy(self.module)
            under_test._set_clc_credentials_from_env()
            mock_clc_sdk.v2.SetCredentials.assert_called_once_with(api_username='dummyuser', api_passwd='dummypwd')

    @patch.object(ClcAlertPolicy, 'clc')
    def test_set_clc_credentials_w_api_url(self, mock_clc_sdk):
        with patch.dict('os.environ', {'CLC_V2_API_URL': 'dummyapiurl'}):
            under_test = ClcAlertPolicy(self.module)
            under_test._set_clc_credentials_from_env()
            self.assertEqual(under_test.clc.defaults.ENDPOINT_URL_V2, 'dummyapiurl')

    def test_set_clc_credentials_w_no_creds(self):
        with patch.dict('os.environ', {}, clear=True):
            under_test = ClcAlertPolicy(self.module)
            under_test._set_clc_credentials_from_env()
        self.assertEqual(self.module.fail_json.called, True)

    @patch.object(clc_alert_policy, 'AnsibleModule')
    @patch.object(clc_alert_policy, 'ClcAlertPolicy')
    def test_main(self, mock_ClcAlertPolicy, mock_AnsibleModule):
        mock_ClcAlertPolicy_instance       = mock.MagicMock()
        mock_AnsibleModule_instance     = mock.MagicMock()
        mock_ClcAlertPolicy.return_value   = mock_ClcAlertPolicy_instance
        mock_AnsibleModule.return_value = mock_AnsibleModule_instance

        clc_alert_policy.main()

        mock_ClcAlertPolicy.assert_called_once_with(mock_AnsibleModule_instance)
        mock_ClcAlertPolicy_instance.process_request.assert_called_once()

    @patch.object(ClcAlertPolicy, '_get_alert_policies')
    @patch.object(ClcAlertPolicy, '_ensure_alert_policy_is_present')
    @patch.object(ClcAlertPolicy, '_set_clc_credentials_from_env')
    def test_process_request_state_present(self, mock_set_clc_creds, mock_ensure_alert_policy, mock_get_alert_policies):
        test_params = {
            'name': 'testname'
            , 'alias': 'testalias'
            , 'alert_recipients': ['test']
            , 'metric': 'cpu'
            , 'duration': 'duration'
            , 'threshold': 'threashold'
            , 'state': 'present'
        }
        mock_ensure_alert_policy.return_value = True, 'success'
        self.module.params = test_params
        self.module.check_mode = False

        under_test = ClcAlertPolicy(self.module)
        under_test.process_request()

        self.module.exit_json.assert_called_once_with(changed=True, policy='success')
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcAlertPolicy, '_get_alert_policies')
    @patch.object(ClcAlertPolicy, '_ensure_alert_policy_is_absent')
    @patch.object(ClcAlertPolicy, '_set_clc_credentials_from_env')
    def test_process_request_state_absent(self, mock_set_clc_creds, mock_ensure_alert_policy, mock_get_alert_policies):
        test_params = {
            'name': 'testname'
            , 'alias': 'testalias'
            , 'alert_recipients': ['test']
            , 'metric': 'cpu'
            , 'duration': 'duration'
            , 'threshold': 'threashold'
            , 'state': 'absent'
        }
        mock_ensure_alert_policy.return_value = True, None
        self.module.params = test_params
        self.module.check_mode = False

        under_test = ClcAlertPolicy(self.module)
        under_test.process_request()

        self.module.exit_json.assert_called_once_with(changed=True, policy=None)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcAlertPolicy, '_create_alert_policy')
    @patch.object(ClcAlertPolicy, '_alert_policy_exists')
    @patch.object(ClcAlertPolicy, '_set_clc_credentials_from_env')
    def test_ensure_alert_policy_is_present_new(self, mock_set_clc_creds, mock_alert_policy_exists, mock_create):
        test_params = {
            'name': 'testname'
            , 'alias': 'testalias'
            , 'alert_recipients': ['test']
            , 'metric': 'cpu'
            , 'duration': 'duration'
            , 'threshold': 'threashold'
            , 'state': 'absent'
        }
        mock_alert_policy_exists.return_value = False
        mock_create.return_value = 'success'
        self.module.params = test_params
        self.module.check_mode = False

        under_test = ClcAlertPolicy(self.module)
        changed, policy = under_test._ensure_alert_policy_is_present()
        self.assertEqual(changed, True)
        self.assertEqual(policy,'success')

    @patch.object(ClcAlertPolicy, '_create_alert_policy')
    @patch.object(ClcAlertPolicy, '_alert_policy_exists')
    @patch.object(ClcAlertPolicy, '_set_clc_credentials_from_env')
    def test_ensure_alert_policy_is_present_no_name(self, mock_set_clc_creds, mock_alert_policy_exists, mock_create):
        test_params = {
            'alias': 'testalias'
            , 'alert_recipients': ['test']
            , 'metric': 'cpu'
            , 'duration': 'duration'
            , 'threshold': 'threashold'
            , 'state': 'absent'
        }
        mock_alert_policy_exists.return_value = False
        mock_create.return_value = 'success'
        self.module.params = test_params
        self.module.check_mode = False

        under_test = ClcAlertPolicy(self.module)
        under_test._ensure_alert_policy_is_present()
        self.module.fail_json.assert_called_once_with(msg='Policy name is a required')

    @patch.object(ClcAlertPolicy, '_ensure_alert_policy_is_updated')
    @patch.object(ClcAlertPolicy, '_alert_policy_exists')
    @patch.object(ClcAlertPolicy, '_set_clc_credentials_from_env')
    def test_ensure_alert_policy_is_present_existing(self, mock_set_clc_creds, mock_alert_policy_exists, mock_update):
        test_params = {
            'name': 'testname'
            , 'alias': 'testalias'
            , 'alert_recipients': ['test']
            , 'metric': 'cpu'
            , 'duration': 'duration'
            , 'threshold': 'threashold'
            , 'state': 'absent'
        }
        mock_alert_policy_exists.return_value = mock.MagicMock()
        mock_update.return_value = True, 'success'
        self.module.params = test_params
        self.module.check_mode = False

        under_test = ClcAlertPolicy(self.module)
        changed, policy = under_test._ensure_alert_policy_is_present()
        self.assertEqual(changed, True)
        self.assertEqual(policy,'success')

    @patch.object(ClcAlertPolicy, '_delete_alert_policy')
    @patch.object(ClcAlertPolicy, '_get_alert_policy_id')
    @patch.object(ClcAlertPolicy, '_set_clc_credentials_from_env')
    def test_ensure_alert_policy_is_absent_name_only(self, mock_set_clc_creds, mock_get_id, mock_delete):
        test_params = {
            'name': 'testname'
            , 'alias': 'testalias'
            , 'state': 'absent'
        }
        mock_get_id.return_value = '12345'
        mock_delete.return_value = 'success'
        self.module.params = test_params
        self.module.check_mode = False
        under_test = ClcAlertPolicy(self.module)
        under_test.policy_dict = {'12345', '23456'}
        changed, policy = under_test._ensure_alert_policy_is_absent()
        self.assertEqual(changed, True)
        self.assertEqual(policy,None)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcAlertPolicy, '_delete_alert_policy')
    @patch.object(ClcAlertPolicy, '_get_alert_policy_id')
    @patch.object(ClcAlertPolicy, '_set_clc_credentials_from_env')
    def test_ensure_alert_policy_is_absent_id_only(self, mock_set_clc_creds, mock_get_id, mock_delete):
        test_params = {
            'id': 'testid'
            , 'alias': 'testalias'
            , 'state': 'absent'
        }
        mock_get_id.return_value = '12345'
        mock_delete.return_value = 'success'
        self.module.params = test_params
        self.module.check_mode = False
        under_test = ClcAlertPolicy(self.module)
        under_test.policy_dict = {'12345', 'testid'}
        changed, policy = under_test._ensure_alert_policy_is_absent()
        self.assertEqual(changed, True)
        self.assertEqual(policy,None)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcAlertPolicy, '_delete_alert_policy')
    @patch.object(ClcAlertPolicy, '_get_alert_policy_id')
    @patch.object(ClcAlertPolicy, '_set_clc_credentials_from_env')
    def test_ensure_alert_policy_is_absent_no_id_present(self, mock_set_clc_creds, mock_get_id, mock_delete):
        test_params = {
            'id': 'testid'
            , 'alias': 'testalias'
            , 'state': 'absent'
        }
        mock_get_id.return_value = '12345'
        mock_delete.return_value = 'success'
        self.module.params = test_params
        self.module.check_mode = False
        under_test = ClcAlertPolicy(self.module)
        under_test.policy_dict = {'12345', '23456'}
        changed, policy = under_test._ensure_alert_policy_is_absent()
        self.assertEqual(changed, False)
        self.assertEqual(policy,None)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcAlertPolicy, '_delete_alert_policy')
    @patch.object(ClcAlertPolicy, '_get_alert_policy_id')
    @patch.object(ClcAlertPolicy, '_set_clc_credentials_from_env')
    def test_ensure_alert_policy_is_absent_no_id_no_name(self, mock_set_clc_creds, mock_get_id, mock_delete):
        test_params = {
            'alias': 'testalias'
            , 'state': 'absent'
        }
        mock_get_id.return_value = '12345'
        mock_delete.return_value = 'success'
        self.module.params = test_params
        self.module.check_mode = False
        under_test = ClcAlertPolicy(self.module)
        under_test.policy_dict = {'12345', '23456'}
        changed, policy = under_test._ensure_alert_policy_is_absent()
        self.module.fail_json.assert_called_once_with(msg='Either alert policy id or policy name is required')

    @patch.object(ClcAlertPolicy, '_update_alert_policy')
    @patch.object(ClcAlertPolicy, '_set_clc_credentials_from_env')
    def test_ensure_alert_policy_is_updated_all_changed(self, mock_set_clc_creds, mock_update):
        test_params = {
            'name': 'testname'
            , 'alias': 'testalias'
            , 'alert_recipients': ['test']
            , 'metric': 'metric'
            , 'duration': 'duration'
            , 'threshold': 'threashold'
            , 'state': 'absent'
        }
        mock_update.return_value = 'success'
        self.module.params = test_params
        self.module.check_mode = False

        policy = {"id":"51db33be37b040f6a135abbaf989e36a","name":"alert1","actions":[{"action":"email","settings":{"recipients":["test1@centurylink.com","test2@centurylink.com"]}}],"links":[{"rel":"self","href":"/v2/alertPolicies/wfad/51db33be37b040f6a135abbaf989e36a","verbs":["GET","DELETE","PUT"]}],"triggers":[{"metric":"disk","duration":"00:05:00","threshold":5.0}]}

        under_test = ClcAlertPolicy(self.module)
        changed, policy_res = under_test._ensure_alert_policy_is_updated(policy)
        self.assertEqual(changed, True)
        self.assertEqual(policy_res,'success')
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcAlertPolicy, '_update_alert_policy')
    @patch.object(ClcAlertPolicy, '_set_clc_credentials_from_env')
    def test_ensure_alert_policy_is_updated_same_metric(self, mock_set_clc_creds, mock_update):
        test_params = {
            'name': 'testname'
            , 'alias': 'testalias'
            , 'alert_recipients': ['test']
            , 'metric': 'disk'
            , 'duration': 'duration'
            , 'threshold': 15
            , 'state': 'absent'
        }
        mock_update.return_value = 'success'
        self.module.params = test_params
        self.module.check_mode = False

        policy = {"id":"51db33be37b040f6a135abbaf989e36a","name":"alert1","actions":[{"action":"email","settings":{"recipients":["test1@centurylink.com","test2@centurylink.com"]}}],"links":[{"rel":"self","href":"/v2/alertPolicies/wfad/51db33be37b040f6a135abbaf989e36a","verbs":["GET","DELETE","PUT"]}],"triggers":[{"metric":"disk","duration":"00:05:00","threshold":5.0}]}

        under_test = ClcAlertPolicy(self.module)
        changed, policy_res = under_test._ensure_alert_policy_is_updated(policy)
        self.assertEqual(changed, True)
        self.assertEqual(policy_res,'success')
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcAlertPolicy, '_update_alert_policy')
    @patch.object(ClcAlertPolicy, '_set_clc_credentials_from_env')
    def test_ensure_alert_policy_is_updated_same_met_duration(self, mock_set_clc_creds, mock_update):
        test_params = {
            'name': 'testname'
            , 'alias': 'testalias'
            , 'alert_recipients': ['test']
            , 'metric': 'disk'
            , 'duration': '00:05:00'
            , 'threshold': 15
            , 'state': 'absent'
        }
        mock_update.return_value = 'success'
        self.module.params = test_params
        self.module.check_mode = False

        policy = {"id":"51db33be37b040f6a135abbaf989e36a","name":"alert1","actions":[{"action":"email","settings":{"recipients":["test1@centurylink.com","test2@centurylink.com"]}}],"links":[{"rel":"self","href":"/v2/alertPolicies/wfad/51db33be37b040f6a135abbaf989e36a","verbs":["GET","DELETE","PUT"]}],"triggers":[{"metric":"disk","duration":"00:05:00","threshold":5.0}]}

        under_test = ClcAlertPolicy(self.module)
        changed, policy_res = under_test._ensure_alert_policy_is_updated(policy)
        self.assertEqual(changed, True)
        self.assertEqual(policy_res,'success')
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcAlertPolicy, '_update_alert_policy')
    @patch.object(ClcAlertPolicy, '_set_clc_credentials_from_env')
    def test_ensure_alert_policy_is_updated_diff_recipients(self, mock_set_clc_creds, mock_update):
        test_params = {
            'name': 'testname'
            , 'alias': 'testalias'
            , 'alert_recipients': ['test']
            , 'metric': 'disk'
            , 'duration': '00:05:00'
            , 'threshold': 5
            , 'state': 'absent'
        }
        mock_update.return_value = 'success'
        self.module.params = test_params
        self.module.check_mode = False

        policy = {"id":"51db33be37b040f6a135abbaf989e36a","name":"alert1","actions":[{"action":"email","settings":{"recipients":["test1@centurylink.com","test2@centurylink.com"]}}],"links":[{"rel":"self","href":"/v2/alertPolicies/wfad/51db33be37b040f6a135abbaf989e36a","verbs":["GET","DELETE","PUT"]}],"triggers":[{"metric":"disk","duration":"00:05:00","threshold":5.0}]}

        under_test = ClcAlertPolicy(self.module)
        changed, policy_res = under_test._ensure_alert_policy_is_updated(policy)
        self.assertEqual(changed, True)
        self.assertEqual(policy_res,'success')
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcAlertPolicy, '_set_clc_credentials_from_env')
    def test_get_alert_policy_id(self, mock_set_clc_creds):
        test_params = {
            'alias': 'testalias'
            , 'state': 'absent'
        }
        self.module.params = test_params
        self.module.check_mode = False
        under_test = ClcAlertPolicy(self.module)
        under_test.policy_dict = {'12345': {'id': '12345', 'name': 'test1'},
                                  '23456': {'id': '23456', 'name': 'test2'}}
        policy_id = under_test._get_alert_policy_id(self.module, 'test2')
        self.assertEqual(policy_id, '23456')

    @patch.object(ClcAlertPolicy, '_set_clc_credentials_from_env')
    def test_get_alert_policy_id_fail_duplicate_names(self, mock_set_clc_creds):
        test_params = {
            'alias': 'testalias'
            , 'state': 'absent'
        }
        self.module.params = test_params
        self.module.check_mode = False
        under_test = ClcAlertPolicy(self.module)
        under_test.policy_dict = {'12345': {'id': '12345', 'name': 'test1'},
                                  '23456': {'id': '23456', 'name': 'test1'}}
        policy_id = under_test._get_alert_policy_id(self.module, 'test1')
        self.module.fail_json.assert_called_once_with(msg='mutiple alert policies were found with policy name : test1')

    @patch.object(ClcAlertPolicy, '_set_clc_credentials_from_env')
    def test_alert_policy_exists_true(self, mock_set_clc_creds):
        test_params = {
            'alias': 'testalias'
            , 'state': 'absent'
        }
        self.module.params = test_params
        self.module.check_mode = False
        under_test = ClcAlertPolicy(self.module)
        under_test.policy_dict = {'12345': {'id': '12345', 'name': 'test1'},
                                  '23456': {'id': '23456', 'name': 'test2'}}
        res = under_test._alert_policy_exists('testalias', 'test1')
        self.assertEqual(res, {'id': '12345', 'name': 'test1'})

    @patch.object(ClcAlertPolicy, '_set_clc_credentials_from_env')
    def test_alert_policy_exists_false(self, mock_set_clc_creds):
        test_params = {
            'alias': 'testalias'
            , 'state': 'absent'
        }
        self.module.params = test_params
        self.module.check_mode = False
        under_test = ClcAlertPolicy(self.module)
        under_test.policy_dict = {'12345': {'id': '12345', 'name': 'test1'},
                                  '23456': {'id': '23456', 'name': 'test2'}}
        res = under_test._alert_policy_exists('testalias', 'notfound')
        self.assertEqual(res, False)

    @patch.object(clc_alert_policy, 'clc_sdk')
    @patch.object(ClcAlertPolicy, '_set_clc_credentials_from_env')
    def test_delete_alert_policy(self, mock_set_clc_creds, mock_clc_sdk):
        mock_clc_sdk.v2.API.Call.side_effect = ['success']
        test_params = {
            'alias': 'testalias'
            , 'state': 'absent'
        }
        self.module.params = test_params
        self.module.check_mode = False
        under_test = ClcAlertPolicy(self.module)
        under_test.clc = mock_clc_sdk
        res = under_test._delete_alert_policy('testalias', '12345')
        self.assertEqual(res, 'success')

    @patch.object(clc_alert_policy, 'clc_sdk')
    @patch.object(ClcAlertPolicy, '_set_clc_credentials_from_env')
    def test_delete_alert_policy_exception(self, mock_set_clc_creds, mock_clc_sdk):
        test_params = {
            'alias': 'testalias'
            , 'state': 'absent'
        }
        self.module.params = test_params
        self.module.check_mode = False
        under_test = ClcAlertPolicy(self.module)
        under_test.clc = mock_clc_sdk
        error = OSError('Failed')
        mock_clc_sdk.v2.API.Call.side_effect = error
        self.assertRaises(OSError, under_test._delete_alert_policy, 'testalias', '12345')

    @patch.object(clc_alert_policy, 'clc_sdk')
    @patch.object(ClcAlertPolicy, '_set_clc_credentials_from_env')
    def test_update_alert_policy(self, mock_set_clc_creds, mock_clc_sdk):
        mock_clc_sdk.v2.API.Call.side_effect = ['success']
        test_params = {
            'name': 'testname'
            , 'alias': 'testalias'
            , 'alert_recipients': ['test']
            , 'metric': 'disk'
            , 'duration': '00:05:00'
            , 'threshold': 5
            , 'state': 'absent'
        }
        self.module.params = test_params
        self.module.check_mode = False
        under_test = ClcAlertPolicy(self.module)
        under_test.clc = mock_clc_sdk
        res = under_test._update_alert_policy('12345')
        self.assertEqual(res, 'success')

    @patch.object(clc_alert_policy, 'clc_sdk')
    @patch.object(ClcAlertPolicy, '_set_clc_credentials_from_env')
    def test_update_alert_policy_exception(self, mock_set_clc_creds, mock_clc_sdk):
        test_params = {
            'name': 'testname'
            , 'alias': 'testalias'
            , 'alert_recipients': ['test']
            , 'metric': 'disk'
            , 'duration': '00:05:00'
            , 'threshold': 5
            , 'state': 'absent'
        }
        self.module.params = test_params
        self.module.check_mode = False
        under_test = ClcAlertPolicy(self.module)
        under_test.clc = mock_clc_sdk
        error = OSError('Failed')
        mock_clc_sdk.v2.API.Call.side_effect = error
        self.assertRaises(OSError, under_test._update_alert_policy, '12345')

    @patch.object(clc_alert_policy, 'clc_sdk')
    @patch.object(ClcAlertPolicy, '_set_clc_credentials_from_env')
    def test_create_alert_policy(self, mock_set_clc_creds, mock_clc_sdk):
        mock_clc_sdk.v2.API.Call.side_effect = ['success']
        test_params = {
            'name': 'testname'
            , 'alias': 'testalias'
            , 'alert_recipients': ['test']
            , 'metric': 'disk'
            , 'duration': '00:05:00'
            , 'threshold': 5
            , 'state': 'absent'
        }
        self.module.params = test_params
        self.module.check_mode = False
        under_test = ClcAlertPolicy(self.module)
        under_test.clc = mock_clc_sdk
        res = under_test._create_alert_policy()
        self.assertEqual(res, 'success')

    @patch.object(clc_alert_policy, 'clc_sdk')
    @patch.object(ClcAlertPolicy, '_set_clc_credentials_from_env')
    def test_create_alert_policy_exception(self, mock_set_clc_creds, mock_clc_sdk):
        test_params = {
            'name': 'testname'
            , 'alias': 'testalias'
            , 'alert_recipients': ['test']
            , 'metric': 'disk'
            , 'duration': '00:05:00'
            , 'threshold': 5
            , 'state': 'absent'
        }
        self.module.params = test_params
        self.module.check_mode = False
        under_test = ClcAlertPolicy(self.module)
        under_test.clc = mock_clc_sdk
        error = OSError('Failed')
        mock_clc_sdk.v2.API.Call.side_effect = error
        self.assertRaises(OSError, under_test._create_alert_policy)

    @patch.object(clc_alert_policy, 'clc_sdk')
    @patch.object(ClcAlertPolicy, '_set_clc_credentials_from_env')
    def test_get_alert_polices(self, mock_set_clc_creds, mock_clc_sdk):
        mock_clc_sdk.v2.API.Call.side_effect = [{
            'items': [
                {
                'id': '12345',
                'name': 'test1'
                },
                {
                'id': '23456',
                'name': 'test2'
                }
            ]
        }]
        test_params = {
            'name': 'testname'
            , 'alias': 'testalias'
            , 'alert_recipients': ['test']
            , 'metric': 'disk'
            , 'duration': '00:05:00'
            , 'threshold': 5
            , 'state': 'absent'
        }
        self.module.params = test_params
        self.module.check_mode = False
        under_test = ClcAlertPolicy(self.module)
        under_test.clc = mock_clc_sdk
        res = under_test._get_alert_policies('testalias')
        self.assertEqual(res,
                         {'12345': {'id': '12345', 'name': 'test1'}, '23456': {'id': '23456', 'name': 'test2'}})

    def testArgumentSpecContract(self):
        args = ClcAlertPolicy._define_module_argument_spec()

        self.assertEqual(args, {'argument_spec':
                                    {'name': {'default': None},
                                     'metric': {'default': None,
                                                'required': False,
                                                'choices': ['cpu', 'memory', 'disk']},
                                     'alert_recipients': {'default': None,
                                                          'required': False,
                                                          'type': 'list'},
                                     'alias': {'default': None, 'required': True},
                                     'state': {'default': 'present', 'choices': ['present', 'absent']},
                                     'threshold': {'default': None, 'required': False, 'type': 'int'},
                                     'duration': {'default': None, 'required': False, 'type': 'str'},
                                     'id': {'default': None}}, 'mutually_exclusive': [['name', 'id']]})


if __name__ == '__main__':
    unittest.main()
