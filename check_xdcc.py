#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Copyright 2018 Carter Yagemann
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import re
import subprocess
import sys
if sys.version_info.major <= 2:
    from ConfigParser import RawConfigParser
else:
    from configparser import RawConfigParser

import requests

def parse_config(filepath):
    if not os.path.isfile(filepath):
        return None

    config = RawConfigParser()
    config.read(filepath)

    required = [('main', 'packlist_url'), ('main', 'output_dir'), ('main', 'retries'),
                ('irc', 'irc_nick'), ('irc', 'irc_server'), ('irc', 'irc_port'),
                ('irc', 'irc_channel'), ('irc', 'irc_bot')]

    for section, item in required:
        if not config.has_option(section, item):
            sys.stderr.write(u"In config " + section + ", " + item + " is required\n")
            return None

    if not config.has_section('regex'):
        sys.stderr.write(u"Section regex is required\n")
        return None

    if len(config.items('regex')) == 0:
        sys.stdout.write(u"Warning, regex section is empty\n")

    return config

def save_downloads(downloads):
    with open('history.txt', 'w') as ofile:
        for download in downloads:
            ofile.write(download + "\n")

def parse_downloads():
    res = list()

    if os.path.isfile('history.txt'):
        with open('history.txt', 'r') as ifile:
            res = [line.strip() for line in ifile]

    return res

def get_packlist_matches(config):
    patterns = list()
    for pattern in config.items('regex'):
        patterns.append(re.compile(pattern[1]))

    matches = list()
    packlist = config.get('main', 'packlist_url')
    for line in requests.get(packlist).text.split("\n"):
        if len(line) == 0 or line[0] != '#':
            continue
        parts = [part for part in line.split(' ') if part != '']
        packnum = parts[0][1:]
        filename = ' '.join(parts[3:])
        if True in [not pat.match(filename) is None for pat in patterns]:
            matches.append((filename, packnum))

    return matches

def xdcc_send(config, package_info):
    filename, package = package_info
    retries = config.getint('main', 'retries')
    odir = config.get('main', 'output_dir')
    nick = config.get('irc', 'irc_nick')
    server = config.get('irc', 'irc_server')
    port = config.get('irc', 'irc_port')
    channel = config.get('irc', 'irc_channel')
    bot = config.get('irc', 'irc_bot')
    filepath = os.path.join(odir, filename)

    for attempt in range(retries):
        # Create command
        cmd = ['/usr/bin/python', 'xdcc_dl.py', '-p', port]
        if attempt == 0:
            pass
        elif os.path.isfile(filepath):
            # There was an error, but some data was received, attempt resume
            resume_from = os.path.getsize(filepath)
            cmd += ['-r', str(resume_from)]
        else:
            # There was an error and no data, bail out!
            break
        cmd += [nick, server, channel, bot, package, odir]

        ret_code = subprocess.call(cmd, stdout=open('/dev/null', 'wb'))
        if ret_code == 0:
            break

    if ret_code == 2 and os.path.isfile(filepath):
        os.remove(filepath)  # Incomplete file
    return ret_code

def main():
    if len(sys.argv) != 2:
        sys.stdout.write(u'Usage: ' + sys.argv[0] + u" <config>\n")
        sys.exit(1)

    # set cwd to directory containing this script
    os.chdir(os.path.dirname(sys.argv[0]))

    config = parse_config(sys.argv[1])
    if config is None:
        sys.stderr.write(u"Invalid config file\n")
        sys.exit(1)

    xdcc_dl = 'xdcc_dl.py'
    if not os.path.isfile(xdcc_dl):
        sys.stderr.write(u"Cannot find xdcc_dl.py\n")
        sys.exit(1)

    history = parse_downloads()

    matched_files = get_packlist_matches(config)
    # Remove files we've already downloaded before
    matched_files = [file for file in matched_files if not file[0] in history]
    # Update history
    history = [file[0] for file in matched_files] + history

    for file in matched_files:
        ret = xdcc_send(config, file)
        if ret != 0:
            sys.stderr.write(u'Failed to download file' + file[0] + u"\n")
            sys.exit(1)

    save_downloads(history)

if __name__ == '__main__':
    main()
