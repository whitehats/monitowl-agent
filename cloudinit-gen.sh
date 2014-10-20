if [ $# -ne 2 ]; then
    echo "usage: ./agent-gen.sh <WEBAPI_URL> <CACERT_URL>"
    exit 1
fi
WEBAPI_URL=$1
CACERT_URL=$2

SYSVINIT=$(mktemp)
GETAGENT=$(mktemp)
AGENT=$(mktemp)
CACERT=$(mktemp)

cat > "$SYSVINIT" <<EOF
#part-handler
from cloudinit import util

def list_types():
    return ["text/sysvinit"]

def handle_part(data, ctype, filename, payload):
    if ctype in ["__begin__", "__end__"]:
        return

    util.write_file("/etc/init.d/monitowl-agent", payload, 0755)
EOF

cat > "$GETAGENT" <<EOF
#!/bin/sh
git clone https://github.com/whitehats/monitowl-agent.git /opt/monitowl
mkdir "/opt/monitowl/virtualenv"
pip install --target="/opt/monitowl/virtualenv" -r "/opt/monitowl/requirements.txt"
EOF

cat > "$AGENT" <<EOF
#!/bin/sh
### BEGIN INIT INFO
# Provides:          monitowl-agent
# Required-Start:    \$remote_fs \$syslog
# Required-Stop:     \$remote_fs \$syslog
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: MonitOwl.com  Agent
# Description:       This file should be used to construct scripts to be
#                    placed in /etc/init.d.  This example start a
#                    single forking daemon capable of writing a pid
#                    file.  To get other behaviour, implement
#                    do_start(), do_stop() or other functions to
#                    override the defaults in /lib/init/init-d-script.
### END INIT INFO

# Author: Dev Team <biuro@whitehats.pl>

DESC="MonitOwl agent service"
DAEMON="/opt/monitowl/run_agent"
DAEMON_ARGS="-c /opt/monitowl/agentconfig.yaml -r --webapi-url $WEBAPI_URL"
PIDFILE=/var/run/monitowl-agent.pid

# Functions
do_start()
{
    . /opt/monitowl/virtualenv/bin/activate
    start-stop-daemon -v -d /opt/monitowl/ --start --oknodo --background --make-pidfile --no-close --pidfile \$PIDFILE --exec \$DAEMON -- \$DAEMON_ARGS  >> /opt/monitowl/agent.log 2>&1
    RETVAL=\$?
}
do_stop()
{
    . /opt/monitowl/virtualenv/bin/activate
    start-stop-daemon --stop --oknodo --pidfile \$PIDFILE --retry 5
    RETVAL=\$?
}



case "\$1" in
  start)
        do_start
        ;;
  stop)
        do_stop
        ;;
esac
exit 0
EOF

cat > "$CACERT" <<EOF
#!/bin/sh
curl -Lo /opt/monitowl/ca.crt "$CACERT_URL"
EOF

write-mime-multipart "$SYSVINIT" "$GETAGENT" "$AGENT:text/sysvinit" "$CACERT"
