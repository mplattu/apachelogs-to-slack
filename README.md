# apachelogs-to-slack

This script reads your Apache combined logs and sends messages to Slack based
on the configuration.

The script is intended to be used in a standard LAMP (Linux-Apache-MariaDB-PHP)
server (e.g. cPanel) where are unable to thoroughly configure the http server
and hook into it.

## Operation

The script is intended to be executed as a cron job. You can execute it as often
as you want. There are no methods to avoid running two instances at the same time
so make sure you are not firing the script too often.

First, the script reads its configuration file. After this it starts to read
the log from STDIN line by line. Whenever any of the `regex`es in the `rules`
array match, a message string is generated.

When the script gets EOF from log file it writes a sha256 digest to `hashFile`.
This hex digest is used to avoid processing same lines (in the top part of the file)
multiple times.

## Configuration

The script reads its configuration from `apachelogs-to-slack.json` and expects it
to be located in the same directory with the script.

* `slackWebHookUrl`: A Slack App webhook URL (see https://api.slack.com/apps).
* `hashFile`: Path to a writeable file. Used to store hex digest of the last processed
   line. If missing, the complete log file is processed and a new hex digest is stored.
* `rules`: Array containing rules of this to monitor in the log files.
    * `field`: Refers to Apache combined log data field to monitor. Is absent, the
      matching is done against the complete log row.
    * `regex`: Regular expression to do the matching. Backtracking is not allowed.
    * `message`: Message to send. Tags starting with hash character refer to the
      combined log fields. `Error #3` expands to "Error" + value of the field 3
      (HTTP status code).

## Installation

The script is written for Python 3 and it uses only standard libraries. All you need
to do is to
* copy `apachelogs-to-slack.py` somewhere where cron finds it
* copy `apachelogs-to-slack.json.sample` to the saame location as
  `apachelogs-to-slack.json` and edit as required
* write a wrapper (typically a shell script) which pipes your log file content to
  the script, e.g. `cat /var/log/apache/access.log | python3 apachelogs-to-slack.py`
* profit!
