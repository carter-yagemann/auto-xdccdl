This project is a `xchat` (XChat, HexChat, etc.) plugin that can be used to
automatically query [nibl](https://nibl.co.uk) for a bot packlist and download new files that match
regular expressions (regex).

# Setup

## Linux

1. Install Python and HexChat: `sudo apt install python3 python3-pip hexchat hexchat-python3`

2. Install python module packages: `sudo pip install requests lxml`

3. Copy `autoxdcc.py` into your plugins directory (`~/.config/hexchat/addons`).

4. It'll create its own config directory (`~/.config/AutoXdcc`). Make a config
in this directory for each bot (see `example.conf`).

## Windows

1. Install [HexChat](https://hexchat.github.io/downloads.html), make sure
to check `Python Interface => Python 3.6`.

2. Start Command Prompt as Administrator and install python module
packages: `python -m pip install requests lxml`

3. Copy `autoxdcc.py` into your plugins directory (`%APPDATA%\HexChat\addons`).

4. It'll create its own config directory (`%HOMEPATH%\.config\AutoXdcc`). Make a config
in this directory for each bot (see `example.conf`).

# Usage

In your IRC client, use the command:

    /autoxdcc <config_name>

For example, for a config named `example.conf`:

    /autoxdcc example
