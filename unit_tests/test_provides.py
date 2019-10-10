# Copyright 2019 Canonical Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import mock
import provides

import charms_openstack.test_utils as test_utils


_hook_args = {}


class _relation_mock:

    def __init__(self, application_name=None, units=None):
        self.to_publish_raw = {}
        self.application_name = application_name
        self.units = units


class TestRegisteredHooks(test_utils.TestRegisteredHooks):

    def test_hooks(self):
        defaults = []
        hook_set = {
            'when': {
                'joined': ('endpoint.{endpoint_name}.joined',),
                'changed': ('endpoint.{endpoint_name}.changed',),
            },
            'when_any': {
                'broken': ('endpoint.{endpoint_name}.broken',
                           'endpoint.{endpoint_name}.departed',),
                'departed': ('endpoint.{endpoint_name}.broken',
                             'endpoint.{endpoint_name}.departed',),
            },
        }
        # test that the hooks were registered
        self.registered_hooks_test_helper(provides, hook_set, defaults)


class TestPlacementProvides(test_utils.PatchHelper):

    def setUp(self):
        super().setUp()
        self.provides_class = provides.PlacementProvides('some-endpoint')
        self._patches = {}
        self._patches_start = {}

    def tearDown(self):
        for k, v in self._patches.items():
            v.stop()
            setattr(self, k, None)
        self._patches = None
        self._patches_start = None

    def test_joined(self):
        self.patch_object(provides, 'set_flag')
        self.provides_class.joined()
        self.set_flag.assert_called_once_with('some-endpoint.connected')

    def test_changed(self):
        self.patch_object(provides, 'set_flag')
        self.patch_object(provides, 'clear_flag')
        self.provides_class.changed()
        self.clear_flag.assert_called_once_with(
            'endpoint.some-endpoint.changed')
        self.set_flag.assert_called_once_with('some-endpoint.available')

    def test_departed(self):
        self.patch_object(provides, 'clear_flag')
        self.provides_class.departed()
        self.clear_flag.assert_has_calls([
            mock.call('some-endpoint.available'),
            mock.call('some-endpoint.connected'),
        ])

    def test_get_nova_placement_disabled(self):
        mock_all_joined_units = mock.MagicMock()
        mock_all_joined_units.received = {'nova_placement_disabled': True}
        self.provides_class._all_joined_units = mock_all_joined_units
        self.assertEqual(
            self.provides_class.get_nova_placement_disabled(),
            True)

    def test_set_placement_enabled(self):
        mock_rel = _relation_mock()
        self.provides_class._relations = [mock_rel]
        self.provides_class.set_placement_enabled()
        expect = {'placement_enabled': True}
        self.assertEqual(mock_rel.to_publish_raw, expect)
