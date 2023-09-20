# Copyright (C) 2020 The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Unittests for the subcmds/envsubst.py module."""

import os
import unittest
import unittest.mock
from unittest.mock import patch, mock_open, MagicMock
from unittest.mock import call

from subcmds import envsubst


def _mock_os_env_var_resolve(var_name):
    if var_name == '${GITBASE}':
        return 'fake_gitbase'
    elif var_name == '${GITREV}':
        return 'fake_gitrev'
    elif var_name == '${TEST}':
        return 'test'
    else:
        return os.path.expandvars(var_name)


class EnvsubstCommand(unittest.TestCase):
    """Test envsubst subcommand"""
    mock_top_level_manifest_file_content = r"""<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <remote name="launch-dso-platform" fetch="${GITBASE}" revision="${GITREV}"/>
  <!-- <default remote="launch-dso-platform" revision="update" /> -->
</manifest>
"""
    mock_expected_top_level_manifest_file_overwritten_content = b"""<?xml version="1.0" ?>
<manifest>
  <remote name="launch-dso-platform" fetch="fake_gitbase" revision="fake_gitrev"/>
  <!-- <default remote="launch-dso-platform" revision="update" /> -->
</manifest>"""

    mock_top_level_manifest_no_local_override_supplied_file_content = r"""<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <remote name="launch-dso-platform" fetch="${GITBASE_NOT_EXISTS}" revision="${GITREV}"/>
  <!-- <default remote="launch-dso-platform" revision="update" /> -->
</manifest>
"""
    mock_expected_top_level_manifest_no_local_override_supplied_file_overwritten_content = b"""<?xml version="1.0" ?>
<manifest>
  <remote name="launch-dso-platform" fetch="${GITBASE_NOT_EXISTS}" revision="fake_gitrev"/>
  <!-- <default remote="launch-dso-platform" revision="update" /> -->
</manifest>"""

    mock_2nd_level_manifest_file_content = r"""<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <project name="caf-components-tf-module" path="components/module" remote="launch-dso-platform" dso_override_attribute_revision="${GITREV}">
    <linkfile src="linkfiles/Makefile" dest="components/Makefile" />
    <!-- <linkfile src="artifacts/terraform_modules/Makefile" dest="components/terraform_modules/Makefile" /> -->
  </project>
</manifest>
"""
    mock_expected_2nd_level_manifest_file_overwritten_content = b"""<?xml version="1.0" ?>
<manifest>
  <project name="caf-components-tf-module" path="components/module" remote="launch-dso-platform" revision="fake_gitrev">
    <linkfile src="linkfiles/Makefile" dest="components/Makefile"/>
    <!-- <linkfile src="artifacts/terraform_modules/Makefile" dest="components/terraform_modules/Makefile" /> -->
  </project>
</manifest>"""

    mock_2nd_level_manifest_negative_file_content = r"""<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <project name="caf-components-tf-module" path="components/module" remote="launch-dso-platform" dso_override_attribute_revision="${GITREV_NOT_SET}">
    <linkfile src="linkfiles/Makefile" dest="components/Makefile" />
    <!-- <linkfile src="artifacts/terraform_modules/Makefile" dest="components/terraform_modules/Makefile" /> -->
  </project>
</manifest>
"""
    mock_expected_2nd_level_manifest_negative_file_overwritten_content = b"""<?xml version="1.0" ?>
<manifest>
  <project name="caf-components-tf-module" path="components/module" remote="launch-dso-platform">
    <linkfile src="linkfiles/Makefile" dest="components/Makefile"/>
    <!-- <linkfile src="artifacts/terraform_modules/Makefile" dest="components/terraform_modules/Makefile" /> -->
  </project>
</manifest>"""

    mock_2nd_level_manifest_existing_attr_file_content = r"""<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <project name="caf-components-tf-module" path="components/module" remote="launch-dso-platform" revision="1.2.3" dso_override_attribute_revision="${GITREV}">
    <linkfile src="linkfiles/Makefile" dest="components/Makefile" />
    <!-- <linkfile src="artifacts/terraform_modules/Makefile" dest="components/terraform_modules/Makefile" /> -->
  </project>
</manifest>
"""
    mock_expected_2nd_level_manifest_existing_attr_file_overwritten_content = b"""<?xml version="1.0" ?>
<manifest>
  <project name="caf-components-tf-module" path="components/module" remote="launch-dso-platform" revision="fake_gitrev">
    <linkfile src="linkfiles/Makefile" dest="components/Makefile"/>
    <!-- <linkfile src="artifacts/terraform_modules/Makefile" dest="components/terraform_modules/Makefile" /> -->
  </project>
</manifest>"""

    mock_2nd_level_manifest_multi_attrs_file_content = r"""<?xml version="1.0" encoding="UTF-8"?>
<manifest>
  <project name="caf-components-tf-module" path="components/module" remote="launch-dso-platform" revision="1.2.3" dso_override_attribute_revision="${GITREV}" dso_override_attribute_dest-branch="${TEST}">
    <linkfile src="linkfiles/Makefile" dest="components/Makefile" />
    <!-- <linkfile src="artifacts/terraform_modules/Makefile" dest="components/terraform_modules/Makefile" /> -->
  </project>
</manifest>
"""
    mock_expected_2nd_level_manifest_multi_attrs_file_overwritten_content = b"""<?xml version="1.0" ?>
<manifest>
  <project name="caf-components-tf-module" path="components/module" remote="launch-dso-platform" revision="fake_gitrev" dest-branch="test">
    <linkfile src="linkfiles/Makefile" dest="components/Makefile"/>
    <!-- <linkfile src="artifacts/terraform_modules/Makefile" dest="components/terraform_modules/Makefile" /> -->
  </project>
</manifest>"""


    def setUp(self):
        self.cmd = envsubst.Envsubst()

    def test_replacement_basic(self):
        """Check baseline xml attr value string replacement """
        self.util_generic_test(self.mock_top_level_manifest_file_content,self.mock_expected_top_level_manifest_file_overwritten_content)

    def test_replacement_when_no_local_overrides_requested(self):
        """Check  xml attr value replacement when no local OS substitutions supplied """
        self.util_generic_test(self.mock_top_level_manifest_no_local_override_supplied_file_content,self.mock_expected_top_level_manifest_no_local_override_supplied_file_overwritten_content)

    def test_attr_injection_basic(self):
        """Check xml attr injection from override configuration"""
        self.util_generic_test(self.mock_2nd_level_manifest_file_content,self.mock_expected_2nd_level_manifest_file_overwritten_content)

    def test_attr_injection_basic_negative(self):
        """Check xml attr injection from override configuration"""
        self.util_generic_test(self.mock_2nd_level_manifest_negative_file_content,self.mock_expected_2nd_level_manifest_negative_file_overwritten_content)

    def test_attr_injection_attr_already_exists(self):
        """Check xml attr override when attr already exists"""
        self.util_generic_test(self.mock_2nd_level_manifest_existing_attr_file_content,self.mock_expected_2nd_level_manifest_existing_attr_file_overwritten_content)

    def test_attr_injection_multi_attrs(self):
        """Check xml attr override when attr already exists"""
        self.util_generic_test(self.mock_2nd_level_manifest_multi_attrs_file_content,self.mock_expected_2nd_level_manifest_multi_attrs_file_overwritten_content)
                
    def util_generic_test(self,input_file_content,expected_file_content):
        """
        generic test fixture test for expected output vs actual
        """
        with patch('os.rename') as rename:
            with patch('builtins.open', new=mock_open(read_data=input_file_content)) as mocked_file:
                self.cmd.resolve_variable = _mock_os_env_var_resolve
                self.cmd.EnvSubst("mock-ignored.xml")
                self.assertEqual(rename.call_args_list,[call('mock-ignored.xml', 'mock-ignored.xml.bak')],"test of Manifest backup before overwrite")
                mocked_file().write.assert_called_once_with(
                    expected_file_content)
