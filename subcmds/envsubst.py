# Copyright (C) 2011 The Android Open Source Project
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

import os
import glob

from command import Command, MirrorSafeCommand
from xml.dom import minidom
from xml.dom.minidom import parseString


class Envsubst(Command, MirrorSafeCommand):
    COMMON = True
    helpSummary = "Replace ENV vars in all xml manifest files"
    helpUsage = """
%prog [-f]
"""
    helpDescription = """
Replace ENV vars in all xml manifest files

Finds all XML files in the manifests and replaces environment variables with values.
"""
    path = '.repo/manifests/**/*.xml'

    # def _Options(self, p):
    #     p.add_option(
    #         "-f",
    #         "--fullpath",
    #         dest="fullpath",
    #         action="store_true",
    #         help="display the full work tree path instead of the relative path",
    #     )

    # def ValidateOptions(self, opt, args):
    #     if opt.fullpath and opt.name_only:
    #         self.OptionParser.error("cannot combine -f and -n")

    #     # Resolve any symlinks so the output is stable.
    #     if opt.relative_to:
    #         opt.relative_to = os.path.realpath(opt.relative_to)

    def Execute(self, opt, args):
        """Substitute all ${ENVVAR} references in manifest xml files.

        Lorem ipsum...

        Args:
            opt: The options.
            args: Positional args.  Can be a list of projects to list, or empty.
        """
        print(f"Executing envsubst {opt}, {args}")
        files = glob.glob(self.path, recursive=True)

        for file in files:
            print(file)
            if os.path.getsize(file) > 0:
                self.EnvSubst(file)

    def EnvSubst(self, infile):
        doc = minidom.parse(infile)
        self.search_replace_placeholders(doc)
        self.inject_attrbutes(doc)
        # backup file before we modified it - for troubleshooting
        os.rename(infile, infile + '.bak')
        self.save(infile,doc)

    def save(self,outfile,doc):
        """
        Save the modified XML document with comments and the XML header
        """
        def pretty_print(data): return '\n'.join([
            line
            for line in parseString(data).toprettyxml(indent=' ' * 2).split('\n')
            if line.strip()
        ])
        with open(outfile, 'wb') as f:
            f.write(str.encode(pretty_print(doc.toprettyxml(encoding="utf-8"))))
        f.writelines
        f.close

    def search_replace_placeholders(self, doc):
        """
        Replace in all element texts and attribute values any ${PLACEHOLDER} by value as returned from #resolveVariable
        """
        for elem in doc.getElementsByTagName('*'):
            for key, value in elem.attributes.items():
                # Check if the attribute value contains an environment variable
                if self.is_placeholder_detected(value):
                    # Replace the environment variable with its value
                    elem.setAttribute(key, self.resolve_variable(value))
            if elem.firstChild and elem.firstChild.nodeType == elem.TEXT_NODE and self.is_placeholder_detected(elem.firstChild.nodeValue):
                # Replace the environment variable with its value
                elem.firstChild.nodeValue = self.resolve_variable(
                    elem.firstChild.nodeValue)

    def is_placeholder_detected(self, value):
        return '$' in value

    def resolve_variable(self, var_name):
        """
        resolves variables from OS env vars
        """
        return os.path.expandvars(var_name)

    def inject_attrbutes(self, doc):
        """
        When encounters XML element <any_element attrname='any value' dso_override_attribute_attrname="replacement">
        or <any_element  dso_override_attribute_attrname="replacement">
        Replace it by <any_element attrname="replacement">
        """
        for elem in doc.getElementsByTagName('*'):
            while self.attr_2_override_detected(elem):
                override_info = self.get_next_attr_override(elem)
                self.inject_or_replace(elem, override_info[0], override_info[1])
                elem.removeAttribute(override_info[2])

    def attr_2_override_detected(self, elem) -> bool:
        for key, value in elem.attributes.items():
            if key.startswith('dso_override_attribute_'):
                return True
        return False

    def get_next_attr_override(self, node) -> [str, str, str]:
        """
        when node is <any_element attrname='any value' dso_override_attribute_attrname="replacement">
        returns ['attrname','replacement','dso_override_attribute_attrname'] 
        otherwise returns an empty array
        """
        for key, value in node.attributes.items():
            if key.startswith('dso_override_attribute_'):
                attr_2_override = key[len('dso_override_attribute_'):]
                attr_2_override_value = value
                attr_2_delete = key
                return [attr_2_override, attr_2_override_value, attr_2_delete]
        return []

    def inject_or_replace(self, elem, attr_name, attr_value) -> None:
        if self.is_placeholder_detected(attr_value):
            return
        if elem.hasAttribute(attr_name):
            elem.removeAttribute(attr_name)
        elem.setAttribute(attr_name, attr_value)
