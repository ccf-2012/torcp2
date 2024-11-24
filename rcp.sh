#!/bin/bash
#
# qBittorrent 'Run after completion':
# /home/ccf2012/torcp/rcp.sh "%F"  "%N"

# # example 1: hardlink to local emby folder
torcp "$1" -d "/home/ccf2012/emby/" -s --torcpdb-url your_torcp_server --lang cn,jp  >>/home/ccf2012/rcp.log 2>>/home/ccf2012/rcp_error.log

# # example 2: rclone copy to gd drive
# torcp "$1" -d "/home/ccf2012/emby/$2/" -s --tmdb-api-key <tmdb api key> --lang cn,jp
# rclone copy "/home/ccf2012/emby/$2/"  gd:/media/148/emby/
# rm -rf "/home/ccf2012/emby/$2/"
