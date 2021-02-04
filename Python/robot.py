#!/usr/bin/python

""" 
        Version history:
        ================
        
        -------------------------------------------------
        30.7.2014       | 0.1   | initial version
        02.12.2014      | 0.2   | converted for python 3.x
        16.04.2019      | 0.3   | OpenAPI v2 target urls
        15.10.2020      | 0.4   | SingleAPI 
        -------------------------------------------------
        
        About:
        ==================      
        This is a simple script that can be used to place multiple wagers from input file in to Veikkaus gaming system. 
        Purpose of this script is to demonstrate how the JSON API provided by Veikkaus website works. Following functionality
        is included:
        
        - login
        - moniveto (multiscore) wagers
        - vakio (sport) wagers
        
        
        Notes:
        ==================      
        This script requires 'requests' package from http://docs.python-requests.org/en/latest/ for session management, ensuring that the 
        site cookies are always properly included in the requests. 
        
        Using a http-client framework that supports authenticated sessions (i.e. cookies) out of the box is highly recommended.
        Veikkaus' website may change the cookies (names and content) unnoticed, and the clients (browsers or custom scripts), shall always use the
        cookies accordingly. It is not only the authentication, but also other requests may set and/or update the cookies. 
        Misbehavior may force us to close your gaming account.
        
        Requests that do not require authentication can be made "without session". However, making the requests as authenticated provides
        us valuable information on how you use the provided services, and thus further helps us to develop it to suite your needs better. 


        Usage:
        ==================      
        How to display usage: 
        robot.py -h
        
        How to request winshares for set of Vakio (SPORT) boards:
        robot.py -a WINSHARE -g SPORT -d 12345 -f sport_input.txt
        
        How to list open draws for moniveto (MULTISORE):
        robot.py -a LIST_DRAWS -g MULTISCORE
        
        How to place moniveto (MULTISCORE) wagers for list index 2:
        robot.py -a PLAY -g MULTISCORE -l 2 -u myaccount -p p4ssw0rd -f multiscore_input.txt -s 20 

        How to place Vakio (SPORT) wagers for list index 1 with miniVakio:
        robot.py -a PLAY -g SPORT -l 1 -u myaccount -p p4ssw0rd -f sport_input.txt -s 25 -m

        How to get account balance
        robot.py -a BALANCE -u myaccount -p p4ssw0rd

        It is possible to run multiple instances of this robot. But it is recommended to run maximum of 5 robots at a same time for a single account.
        This is because debiting the single account becomes the bottleneck for robot-wagering, and multiple instances do no longer provide the benefit in speed.        
        
""" 

import sys
import requests
import json
import copy
import time
import datetime
import getopt

""" 
        properties
        
"""

# the veikkaus site address
host="https://www.veikkaus.fi"

# required headers
headers = {
        'Content-type':'application/json',
        'Accept':'application/json',
        'X-ESA-API-Key':'ROBOT'
}

# wager teamplate with common fields
wager_template = {
	"listIndex":0,
	"gameName":"",
        "price": 0,
	"boards":[]
}

# winshare teamplate with common fields
winshare_template = {
	"additionalPrizeTier": False,
	"page":0,
        "pageSize":100,
	"selections":[]
}

"""
        get account balance

"""
def get_balance ( session ):
        r = session.get(host + "/api/v1/players/self/account", verify=True, headers=headers)
        j = r.json()
        return j["balances"]["CASH"]["usableBalance"]

"""
        Create winshare request for vakio. 
        For most of the games, the odds are provided as flat files. It is highly recommended to use those as long as they are available. 

        Vakio winshare request takes only the "selections" as input, so we can reuse the create_sport_wager code.
        
"""
def get_sport_winshare ( draw, matches ):
        # the winshare request takes nearly similar request, so lets use create_sport_wager, and copy selections to winshare_req
        winshare_req = create_sport_wager("", 0, matches, False)

        print (winshare_req)
        r = requests.post(host + "/api/sport-winshare/v1/games/SPORT/draws/"+draw+"/winshare", verify=True, data=json.dumps(winshare_req), headers=headers)
        j = r.json()
        print(j)
        for winshare in j["winShares"]:
                # each winshare has only one selection that contains the board (outcomes)
                
                board = []
                for selection in winshare["selections"]:
                        for outcome in selection["outcomes"]:
                                board.append(outcome)

                print("value=%d,numberOfBets=%d,board=%s" % (winshare["value"], winshare["numberOfBets"],",".join(board)))

                
"""
        Creates a vakio (sport) wager, for which the selections of row in input file:
        2;1X2;X;1;X;2;X;1;X;2;1;12;X

{
        "listIndex": 1,
        "gameName": "SPORT",
        "price": 150,
        "boards": [
          {
            "betType": "FREE 6",
            "stake": 25,
            "selections": [
                { "outcomes":["2"] },
                { "outcomes":["1","X","2"] },
                { "outcomes":["X"] },
                { "outcomes":["1"] },
                { "outcomes":["X"] },
                { "outcomes":["2"] },
                { "outcomes":["X"] },
                { "outcomes":["1"] },
                { "outcomes":["X"] },
                { "outcomes":["2"] },
                { "outcomes":["1"] },
                { "outcomes":["1","2"] },
                { "outcomes":["X"] }
            ]
          }
        ]
}

        Notes:
          - supports multiple regular wagers from input file, w/ or wo/ minivakio
          - supports system wagers from input file, no minivakio 
          - no reduced system support

"""
def create_sport_wager ( listIndex, stake, matches, miniVakio ):
        if stake > 0:
                req = copy.deepcopy(wager_template)

                req["gameName"] = "SPORT"
                req["listIndex"] = listIndex
                req["price"] = stake

                ## this implementation supports only one row (selection) per wager
                if miniVakio:
                        req["additionalPrizeTier"] = True
                        req["price"] = 2*stake
                        
                selection = {
                        "stake": stake,
                        "selections":[]
                }
        
                sysSize = 1
                for m in matches:
                        if len(m) == 1:
                                outcome = { "outcomes":[m] }
                        else:
                                sels = []
                                for i in m:
                                        if i != "\n":
                                                sels.append(i)
                                                
                                outcome = { "outcomes":sels }
                                sysSize *= len(sels)

                        ## add outcome to selection
                        selection["selections"].append(outcome)

                ## add betType based on size
                if sysSize == 1:
                        selection["betType"] = "Regular"
                else:
                        selection["betType"] = "FREE " + str(sysSize)
                
                ## ... and the selection to wager request
                req["boards"].append(selection)
                
        else:
                req = copy.deepcopy(winshare_template)

                for m in matches:
                        if len(m) == 1:
                                outcome = { "outcomes":[m] }
                        else:
                                sels = []
                                for i in m:
                                        if i != "\n":
                                                sels.append(i)
                                                
                                outcome = { "outcomes":sels }
                                                
                        ## add outcome to selection
                        req["selections"].append(outcome)
                                                
        return req


"""
        Create a moniveto (multiscore) wager, for which the selections in input file:
        0-0,1;2-3,4;4-2,5

{
        "listIndex": 1,
        "gameName": "MULTISCORE",
        "price": 160,
        "boards": [
           {
              "betType": "FULL 8",
              "stake": 20,
              "selections": [
                  {
                    "homeScores": [ 0 ],
                    "awayScores": [ 0,1 ]
                  },
                  {
                    "homeScores": [ 2 ],
                    "awayScores": [ 3,4 ]
                  },
                  {
                    "homeScores": [ 4 ],
                    "awayScores": [ 2,5 ]
                  }
              ]
           }
        ]
}

        Notes:
          - supports multiple regular or system wagers from input file
          - no reduced system support

"""
def create_multiscore_wager ( listIndex, stake, matches ):
        wager_req = copy.deepcopy(wager_template)
        wager_req["gameName"] = "MULTISCORE"
        wager_req["listIndex"] = listIndex
        wager_req["price"] = stake

        selection = {
                "stake": stake,
                "betType":"Regular",
                "selections":[]
        }

        sysSize = 1
        for match in matches:
                home, away = match.split("-")
                sels = {
                        "homeScores":[], "awayScores":[]
                }
                sels["homeScores"] = list(map(int, home.split(",")))
                sels["awayScores"] = list(map(int, away.split(",")))
                sysSize *= len(sels["homeScores"]) * len(sels["awayScores"])
                selection["selections"].append(sels)

        if sysSize > 1:
                wager_req["price"] = stake * sysSize
                selection["betType"] = "FULL " + str(sysSize)
                
        wager_req["boards"].append(selection)
        
        return wager_req

""" 
        Places wagers on the system. Prints out the serial numbers of all accpeted wagers and error codes for rejected wagers. 

"""
def place_wagers ( wager_req, session ):
        rt = time.time()
        r = session.post(host + "/api/sport-interactive-wager/v1/tickets", verify=True, data=json.dumps(wager_req), headers=headers)
        rt = time.time() - rt;

        if r.status_code == 200:
                j = r.json()
                print("%s - placed wager in %.3f seconds, serial %s\n" % (datetime.datetime.now(), rt, j["serialNumber"][:17]))
        else:
                print("Request failed:\n" + r.text)


"""
        Logins to veikkaus website, and returns the session object.
        It is important to use same session for all requests, so that the session cookies are handled properly.  
        If you want to manage the cookies manually, you have to take all the cookies from each response (even wagering) and update them accordingly. 

"""
def login (username, password): 
        s = requests.Session()
        login_req = {"type":"STANDARD_LOGIN","login":username,"password":password}
        r = s.post(host + "/api/bff/v1/sessions", verify=True, data=json.dumps(login_req), headers=headers)
        if r.status_code != 200:
                raise Exception("Authentication failed", r.status_code)

        return s

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
                "listIndex":0,
                "miniVakio": False,
                "input":"",
                "stake":0
        }
        for o, a in optlist:
                if o == '-h':
                        print("-h prints this help")
                        print("-a <action> (PLAY, WINSHARE, LIST_DRAWS, BALANCE)")
                        print("-u <username>")
                        print("-p <password>")
                        print("-g <game> (MULTISCORE, SCORE, SPORT)")
                        print("-d <draw number>")
                        print("-l <list index>")
                        print("-m (play with miniVakio")
                        print("-f <input file> containing the wagers")
                        print("-s <stake> (in cents, same stake used for all wagers)")
                        sys.exit(0)
                elif o == '-a':
                        params["action"] = a
                elif o == '-u':
                        params["username"] = a
                elif o == '-p':
                        params["password"] = a
                elif o == '-g':
                        params["game"] = a
                elif o == '-d':
                        params["draw"] = a
                elif o == '-l':
                        params["listIndex"] = int(a)
                elif o == '-m':
                        params["miniVakio"] = True
                elif o == '-f':
                        params["input"] = a
                elif o == '-s':
                        params["stake"] = int(a)
        return params
        
"""
        Lists open draws
        The request only takes game name as an input, e.g.
        This implementation only prints common fields such as game name, index, draw and status. 
        More (game specific) details are available in the returned JSON document. 

"""
def list_draws ( params ):
        r = requests.get(host + "/api/sport-open-games/v1/games/"+params["game"]+"/draws", verify=True, headers=headers)
        if r.status_code == 200:
                try:
                        j = r.json()
                        for draw in j:
                                print("game: %s, listIndex: %2s, draw: %6s, status: %s, number events: %d" % (draw["gameName"],draw["listIndex"],draw["id"],draw["status"],len(draw["rows"])))
                except: 
                        print("request failed: " + r.text)
        else:
                print("request failed: " + r.text)

"""
        Places the wagers based on input file.
        Prints out balance in the end. 

"""
def play ( params ):
        session = login(params["username"], params["password"])
        f = open(params["input"],"r")

        for line in f:
                if line.startswith("#"): continue
                wager_req = copy.deepcopy(wager_template)
                if params["game"] == "MULTISCORE":
                        wager_req = create_multiscore_wager(params["listIndex"], params["stake"], line.split(";"))
                elif params["game"] == "SPORT":
                        wager_req = create_sport_wager(params["listIndex"], params["stake"], line.split(";"),params["miniVakio"])

                place_wagers(wager_req, session)

        balance = get_balance( session )
        print("\n\taccount balance: %.2f\n" % (balance/100.0))

"""
        Login and get balance. 
"""
def balance ( params ):
        session = login(params["username"], params["password"])
        balance = get_balance( session )
        print("\n\taccount balance: %.2f\n" % (balance/100.0))

"""
        Performs winshare request for each set of wagers from input file
"""
def winshare ( params ):
        f = open(params["input"],"r")
        
        for line in f:
                if line.startswith("#"): continue
                if params["game"] == "SPORT":
                         get_sport_winshare(params["draw"], line.split(";"))

"""
        Robot main function
        - login
        - read the wagers from input file
        - places wagers 

"""
def robot( arguments ): 
        params = parse_arguments( arguments )
        
        if params["action"] == "LIST_DRAWS":
                list_draws(params)
        elif params["action"] == "PLAY":
                play(params)
        elif params["action"] == "WINSHARE":
                winshare(params)
        elif params["action"] == "BALANCE":
                balance(params)

"""
        MAIN

"""
if __name__ == "__main__":
        robot(sys.argv[1:])
