#!/bin/sh

BINDIR="/opt/monitowl"
SYSTEMDDIR="/etc/systemd/system/monitowl-agent.service"
SYSVDIR="/etc/init.d/monitowl-agent"

REPOURL="https://github.com/whitehats/monitowl-agent"
BINURL="${REPOURL}/releases/download/latest"
BINNAME="monitowl-agent_linux_amd64"  # TODO: Other systems
SYSTEMDURL="${REPOURL}/raw/master/scripts/monitowl-agent.service"
SYSVURL="${REPOURL}/raw/master/scripts/monitowl-agent"

CONFIGFILE="${BINDIR}/agentconfig.ini"
WEBAPIURL="demo.monitowl.com"

echo "Creating directory \`${BINDIR}\`."
mkdir -p "${BINDIR}"

echo "Downloading monitowl-agent binary from \`${BINURL}/${BINNAME}\` to \`${BINDIR}\`."
curl -L --progress-bar -o "${BINDIR}/monitowl-agent" "${BINURL}/${BINNAME}"
chmod +x "${BINDIR}/monitowl-agent"

if [ -n "$1" ]; then
    WEBAPIURL=$1
fi

if [ ! -f "${CONFIGFILE}" ]; then
    echo "Writing minimal configuration file to \`${CONFIGFILE}\`, using webapi URL \`${WEBAPIURL}\`."
    cat > "${CONFIGFILE}" <<EOF
[main]
run = true
sensors-config = ${BINDIR}/sensorsconfig.yaml
webapi-url = ${WEBAPIURL}
EOF
else
    echo "Configuration file exists, updating webapi URL with \`${WEBAPIURL}\`."
    if grep -q "^webapi-url[[:space:]]*=" "${CONFIGFILE}"; then
        sed -i "s!^webapi-url\s*=.*!webapi-url = ${WEBAPIURL}!" "${CONFIGFILE}"
    else
        echo "webapi-url = ${WEBAPIURL}" >> "${CONFIGFILE}"
    fi
fi

if init --version > /dev/null 2>&1 | grep -q "systemd"; then
    echo "Detected systemd, downloading service file from \`${SYSTEMDURL}\` to \`${SYSTEMDDIR}\`."
    curl -L --progress-bar -o "${SYSTEMDDIR}" "${SYSTEMDURL}"
    systemctl daemon-reload
    systemctl restart monitowl-agent
    systemctl enable monitowl-agent
else
    echo "Detected SysV/Upstart, downloading init script from \`${SYSVURL}\` to \`${SYSVDIR}\`."
    curl -L --progress-bar -o "${SYSVDIR}" "${SYSVURL}"
    service monitowl-agent stop
    service monitowl-agent start
    update-rc.d -f monitowl-agent defaults
fi
