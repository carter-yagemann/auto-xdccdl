This project is a `xchat` (XChat, HexChat, etc.) plugin that can be used to
automatically query [nibl](https://nibl.co.uk) for a bot packlist and download new files that match
regular expressions (regex).

# Setup

1. Install python module packages:

    pip install requests lxml

2. Copy `autoxdcc.py` into your plugins directory (e.g. `~/.config/hexchat/addons`)
and enable it.

3. It'll create its own config directory (e.g. `~/.config/AutoXdcc`). Make a config
in this directory for each bot. See `example.conf`.

# Usage

In your IRC client, use the command:

    /autoxdcc <config_name>

For example, if you created a config named `example.conf`:

    /autoxdcc example
