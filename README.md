This project can be used to automatically track an IRC XDCC bot and download
files that match regular expressions (regex).

# Setup

Install the requirements:

    pip install -r requirements.txt

And create a configuration for each bot you want to track. See `example.conf`.

Finally, set a cronjob to run `check_xdcc.py` however often you want to check
for new files.

# Usage

    ./check_xdcc.py <config>
