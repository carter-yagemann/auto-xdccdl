#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Copyright 2019 Carter Yagemann
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

from __future__ import print_function

__module_name__ = "AutoXdcc"
__module_version__ = "1.0"
__module_description__ = "Queries a packlist and requests new files matching provided regular expressions."
__module_author__ = "Carter Yagemann <yagemann@protonmail.com>"

import xchat
import requests
import os
import re
import sys
import platform
from time import sleep
if sys.version_info.major <= 2:
    from ConfigParser import RawConfigParser
else:
    from configparser import RawConfigParser

def whoami():
    try:
        cmd = os.popen("whoami")
        try:
            user = cmd.readlines()
            user = user[0].strip("\n")
        finally:
            cmd.close()
    except IOError:
        return None
    return user

def get_config_dir():
    user = whoami()
    if user is None:
        return None
    system = platform.system()
    if system == 'Windows':
        return 'C:/Users/' + user + '/.config/AutoXdcc/'
    elif system == 'Linux':
        return '/home/' + user + '/.config/AutoXdcc/'
    else:
        print("Unsupported OS: " + str(system))
        return None

def parse_config(filepath):
    if not os.path.isfile(filepath):
        return None

    config = RawConfigParser()
    config.read(filepath)

    required = [('main', 'packlist'), ('irc', 'channel'), ('irc', 'bot')]

    for section, item in required:
        if not config.has_option(section, item):
            print("In config " + section + ", " + item + " is required")
            return None

    if not config.has_section('regex'):
        print("Section regex is required\n")
        return None

    if len(config.items('regex')) == 0:
        print("Warning, regex section is empty")

    return config

def save_downloads(downloads):
    dl_path = os.path.join(config_dir, 'history.txt')
    with open(dl_path, 'w') as ofile:
        for download in downloads:
            ofile.write(download + "\n")

def parse_downloads():
    res = list()
    dl_path = os.path.join(config_dir, 'history.txt')

    if os.path.isfile(dl_path):
        with open(dl_path, 'r') as ifile:
            res = [line.strip() for line in ifile]

    return res

def get_packlist_matches(config):
    patterns = list()
    for pattern in config.items('regex'):
        patterns.append(re.compile(pattern[1]))

    matches = list()

    packlist = config.get('main', 'packlist')
    res = requests.get(packlist)
    if res.status_code != 200:
        print("Unexpected HTTP response: " + str(res.getcode()))
        return matches

    for line in res.text.split("\n"):
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
    bot = config.get('irc', 'bot')
    try:
        xchat.command('msg ' + bot + ' XDCC SEND ' + str(package))
    except AttributeError:
        return 1
    return 0

def check_and_send(config_name):
    config_path = os.path.join(config_dir, config_name + ".conf")
    if not os.path.isfile(config_path):
        print("Cannot find " + config_path)
        return

    config = parse_config(config_path)
    if config is None:
        print(config_path + " has an invalid format")
        return

    chan = xchat.get_info("channel")
    if chan is None or chan != config.get('irc', 'channel'):
        print("Wrong channel. Expected " + config.get('irc', 'channel') + ", currently in " + str(chan))
        return

    bot = config.get('irc', 'bot')
    found_bot = False
    for user in xchat.get_list('users'):
        if xchat.nickcmp(bot, user.nick) == 0:
            found_bot = True
            break
    if not found_bot:
        print("Failed to find " + bot + " in current channel")
        return

    history = parse_downloads()

    matched_files = get_packlist_matches(config)
    # Remove files we've already downloaded before
    matched_files = [file for file in matched_files if not file[0] in history]

    for idx, file in enumerate(matched_files):
        ret = xdcc_send(config, file)
        if ret == 0:
            history.append(file[0])
        else:
            print("Failed to request package from " + bot)
        if idx < len(matched_files) - 1:
            sleep(3)

    save_downloads(history)

def main(word, word_eol, userdata):
    argc = len(word)

    if argc == 2:
        check_and_send(word[1])
    else:
        print("Invalid command")

    return xchat.EAT_ALL

def init():
    if config_dir is None:
        print("Failed to find config directory path")
        return
    if not os.path.isdir(config_dir):
        if os.path.exists(config_dir):
            print(config_dir + " exists and is not a directoy, cannot initialize")
            return
        os.makedirs(config_dir)

    xchat.hook_command("autoxdcc", main, help="/autoxdcc <config_name>")
    print("AutoXdcc loaded")

config_dir = get_config_dir()
init()
