#!/usr/bin/env python3

"""
        Version history:
        ================

        -------------------------------------------------
        30.11.2021      | 0.1   | initial version
        -------------------------------------------------

        About:
        ==================
        This script sends given input files to veikkaus file upload API.

        Notes:
        ==================
        This script requires 'requests' package from http://docs.python-requests.org/en/latest/ for session management, ensuring that the
        site cookies are always properly included in the requests.

        Usage:
        ==================

        All files are played to the game/draw given in parameters.

        play-file.py -u <username> -p <password> -g <SPORT|MULTISCORE> -d <draw> <file> [<file> ...]

"""

import sys
import requests
import json
import copy
import time
import datetime
import getopt
from os.path import exists

"""
        properties
"""

# Veikkaus
host="https://www.veikkaus.fi"

# required headers
headers_text = {
        'Content-type':'text/plain',
        'Accept':'application/json',
        'X-ESA-API-Key':'ROBOT'
}

"""
        Logins to veikkaus website, and returns the session object.
"""
def login (username, password):
        s = requests.Session()
        login_req = {"type":"STANDARD_LOGIN","login":username,"password":password}
        r = s.post(host + "/api/bff/v1/sessions", verify=True, data=json.dumps(login_req))
        if r.status_code != 200:
                raise Exception("Authentication failed", r.status_code)

        return s

"""
        Places the wagers based on input file.
        Prints out balance in the end.
"""
def play (session, game, draw, file):
        rb = session.post(host + "/api/wager-file/v1beta/batches/games/"+game+"/draws/"+draw+"/stream", data=open(file,'r').read(), headers={ 'content-type': 'text/plain' })
        if rb.status_code == 200:
                batch = rb.json()
                print("[%s] file %s uploaded." % (batch["fileId"], file))
                ra = session.put(host + "/api/wager-file/v1beta/batches/by-id/"+batch["fileId"]+"/state/approved")
                if ra.status_code == 200:
                        print("[%s] file %s approved." % (batch["fileId"], file))
                else:
                        print("[%s] approval failed."  % (batch["fileId"]))
                        print(ra)
        else:
                print("[-] file %s was rejected." % (file))
                print(rb)

"""
        Parse arguments.
"""
def parse_arguments ( arguments ):
        optlist, args = getopt.getopt(arguments, 'ha:u:p:g:d:l:mf:s:')

        params = {
                "username":"",
                "passowrd":"",
                "game":"",
                "draw":"",
                "input":[]
        }

        for o, a in optlist:
                if o == '-h':
                        print("-h prints this help")
                        print("-u <username>")
                        print("-p <password>")
                        print("-g <game> (MULTISCORE, SPORT)")
                        print("-d <draw number>")
                        print("list of files to play")
                        sys.exit(0)
                elif o == '-u':
                        params["username"] = a
                elif o == '-p':
                        params["password"] = a
                elif o == '-g':
                        params["game"] = a
                elif o == '-d':
                        params["draw"] = a

        params["input"] = args
        return params

"""
        MAIN
"""
if __name__ == "__main__":
        params = parse_arguments(sys.argv[1:])
        session = login(params["username"], params["password"])
        for file in params["input"]:
                if exists(file):
                        play(session, params["game"], params["draw"], file)
                else:
                        print("file not found: " + file)
