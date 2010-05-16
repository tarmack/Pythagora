# -*- coding: utf-8 -*
#-------------------------------------------------------------------------------{{{
# Copyright 2010 B. Kroon <bart@tarmack.eu>.
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
#-------------------------------------------------------------------------------}}}
import sys

STDOUT = sys.stdout

class Verbose:
    msg = ''
    def write(self, msg):
        self.msg += msg
        if msg == '\n' and self.msg:
            if not self.msg.startswith('debug:'):
                STDOUT.write(self.msg)
            self.msg = ''

class Error:
    msg = ''
    def write(self, msg):
        self.msg += msg
        if msg == '\n' and self.msg:
            if self.msg.startswith('error:'):
                STDOUT.write(self.msg)
            self.msg = ''

class Quiet:
    def write(self, msg):
        pass

if sys.argv and sys.argv != ['']:
    args = sys.argv[1:]
    if not args:
        sys.stdout = Error()
    for opt in args:
        if opt in ('-v', '--verbose'):
            sys.stdout = Verbose()
        elif opt in ('-d', '--debug'):
            sys.stdout = STDOUT
        elif opt in ('-q', '--quiet'):
            sys.stdout = Quiet()
            sys.stderr = Quiet()
        else: sys.stdout = Error()
