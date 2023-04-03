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
        path = '.repo/manifests/**/*.xml'
        files = glob.glob(path, recursive=True)

        for file in files:
            print(file)
            if os.path.getsize(file) > 0:
                self.EnvSubst(file)


    def EnvSubst(self, infile):
        doc = minidom.parse(infile)

        # Replace environment variables in all element texts and attribute values
        for elem in doc.getElementsByTagName('*'):
            for key, value in elem.attributes.items():
                # Check if the attribute value contains an environment variable
                if '$' in value:
                    # Replace the environment variable with its value
                    elem.setAttribute(key, os.path.expandvars(value))
            if elem.firstChild and elem.firstChild.nodeType == elem.TEXT_NODE and '$' in elem.firstChild.nodeValue:
                # Replace the environment variable with its value
                elem.firstChild.nodeValue = os.path.expandvars(
                    elem.firstChild.nodeValue)

        pretty_print = lambda data: '\n'.join([
            line
            for line in parseString(data).toprettyxml(indent=' ' * 2).split('\n')
            if line.strip()
        ])

        # Save the modified XML document with comments and the XML header
        os.rename(infile, infile + '.bak')

        with open(infile, 'wb') as f:
            f.write(str.encode(pretty_print(doc.toprettyxml(encoding="utf-8"))))
            #f.write(doc.toprettyxml(encoding="utf-8"))
        f.writelines
        f.close
