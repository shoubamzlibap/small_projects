#!/bin/bash
# Installer script for auto_copy
# APR-2016 Isaac Hailperin <isaac.hailperin@gmail.com>

files="
    /usr/local/sbin/auto_copy_daemon.py
    /usr/local/bin/auto_copy.py
    /usr/lib/systemd/system/autocopy.service
    /etc/udev/rules.d/autodvd.rules
    /usr/local/bin/config_parser.py
    /usr/local/sbin/send_siguser1.sh
    /usr/local/bin/trayopen
"
config="/etc/auto_copy.yml"

print_help(){
cat <<EOF
usage:
setup.sh [install|check|remove]

    install - install files and enable service
    check   - check if installed files are up to date
    remove  - remove files from system
EOF
}

compile_trayopen(){
    which gcc >/dev/null 2>&1
    if [ $? -eq 0 ]; then
        gcc -o trayopen trayopen.c 2>/dev/null
    else
        echo "No gcc found - using precompiled trayopen binary."
    fi
}

install_files(){
    compile_trayopen
    for binary in ${files}; do
        s_binary=$(basename ${binary})
        install ${s_binary} ${binary} -o root -g root
    done
    chmod 644 /usr/lib/systemd/system/autocopy.service
    chmod 644 /etc/udev/rules.d/autodvd.rules
    chmod 644 /usr/local/bin/config_parser.py
    if [ ! -f ${config} ]; then
        install auto_copy.yml.example ${config} -o root -g root
    fi
}

check_files(){
    for binary in ${files}; do
        if [ -f ${binary} ]; then
            s_binary=$(basename ${binary})
            s_sum=$(sha256sum ${s_binary}|cut -d ' ' -f 1)
            d_sum=$(sha256sum ${binary}|cut -d ' ' -f 1)
            if [ "${s_sum}" != "${d_sum}" ]; then
                echo "${binary} is not current or was modified locally"
            fi
        else
            echo "${binary} is not installed"
        fi
    done

}

remove_files(){
    for binary in ${files}; do
        if [ ! -f ${binary} ]; then
            continue
        fi
        # do not accitentally delete something that could get close to /
        if [ ${#binary} -lt 4 ]; then
            echo "Not removing ${binary} / seems system related"
        else
            rm -f ${binary}
        fi
    done
}

case $1 in
    install)
        install_files
        ;;
    check)
        check_files
        ;;
    remove)
        remove_files
        ;;
    *)
        print_help
esac
