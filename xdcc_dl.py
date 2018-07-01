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

from __future__ import print_function

import sys
import os
import argparse
import itertools
import shlex
import struct
import ssl

import irc.client

def on_connect(connection, event):
    if not irc.client.is_channel(args.channel):
        print('Channel', args.channel, 'does not exist')
        raise SystemExit(1)
    connection.join(args.channel)

def on_join(connection, event):
    connection.privmsg(args.bot, 'XDCC SEND ' + args.package)

def on_disconnect(connection, event):
    raise SystemExit()

def on_ctcp(connection, event):
    global dcc, file, received_bytes, filename, filesize, peer_address

    nick = event.source.nick
    if event.arguments[0] == "VERSION":
        version = "Python irc.bot ({version})".format(version=irc.client.VERSION_STRING)
        connection.ctcp_reply(nick, "VERSION " + version)
    elif event.arguments[0] == "PING":
        if len(event.arguments) > 1:
            connection.ctcp_reply(nick, "PING " + event.arguments[1])
    elif event.arguments[0] == "DCC":
        payload = event.arguments[1]
        parts = shlex.split(payload)
        command = parts[0]
        if command == "SEND" and args.resume == 0:
            command, filename, peer_address, peer_port, filesize = parts
            filename = os.path.join(args.save_dir, filename)
            file = open(filename, "wb")
            peer_address = irc.client.ip_numstr_to_quad(peer_address)
            peer_port = int(peer_port)
            filesize = int(filesize)
            received_bytes = 0
            dcc = reactor.dcc("raw").connect(peer_address, peer_port)
        elif command == "SEND" and args.resume > 0:
            command, filename, peer_address, peer_port, filesize = parts
            connection.ctcp_reply(nick, "DCC RESUME \"" + filename + "\" " + peer_port + " " + str(args.resume))
        elif command == "ACCEPT" and args.resume > 0:
            command, filename, peer_port, position = parts
            filename = os.path.join(args.save_dir, filename)
            file = open(filename, "ab")
            peer_address = irc.client.ip_numstr_to_quad(peer_address)
            peer_port = int(peer_port)
            filesize = int(filesize)
            received_bytes = int(position)
            dcc = reactor.dcc("raw").connect(peer_address, peer_port)
        else:
            print('Unexpected DCC message', payload)
            raise SystemExit(1)
    else:
        print('Unexpected CTCP message', event.arguments[0])

def on_dccmsg(connection, event):
    global received_bytes

    data = event.arguments[0]
    file.write(data)
    received_bytes += len(data)
    sys.stdout.write(str(received_bytes) + "\r")
    sys.stdout.flush()
    dcc.send_bytes(struct.pack("!I", received_bytes))

def on_dcc_disconnect(connection, event):
    global filename, received_bytes, file, filesize
    file.close()
    print("Received file %s (%d bytes)." % (filename, received_bytes))
    if received_bytes != filesize:
        print("Expected filesize to be %d bytes, got %d." % (filesize, received_bytes))
        raise SystemExit(2)
    raise SystemExit()

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('nickname', type=str)
    parser.add_argument('server', type=str)
    parser.add_argument('channel', type=str)
    parser.add_argument('bot', type=str)
    parser.add_argument('package', type=str)
    parser.add_argument('save_dir', type=str)
    parser.add_argument('-p', '--port', default=6667, type=int)
    parser.add_argument('-r', '--resume', default=0, type=int,
                        help='Resume downloading from provided byte offset')
    return parser.parse_args()

def main():
    global reactor

    reactor = irc.client.Reactor()
    try:
        if args.port == 6697:
            ssl_factory = irc.connection.Factory(wrapper=ssl.wrap_socket)
            c = reactor.server().connect(args.server, args.port, args.nickname,
                    connect_factory=ssl_factory)
        else:
            c = reactor.server().connect(args.server, args.port, args.nickname)
    except irc.client.ServerConnectionError:
        print(sys.exc_info()[1])
        raise SystemExit(1)

    c.add_global_handler("welcome", on_connect)
    c.add_global_handler("join", on_join)
    c.add_global_handler("disconnect", on_disconnect)
    c.add_global_handler("ctcp", on_ctcp)
    c.add_global_handler("dccmsg", on_dccmsg)
    c.add_global_handler("dcc_disconnect", on_dcc_disconnect)

    reactor.process_forever()

if __name__ == '__main__':
    args = get_args()
    main()
