import json
import os

# Function: add_pending_spot
# Handle pending spot data creation/editing
def add_pending_spot(candidate_msgid, userid, msgid):
    spotfile = open("data/pending_spots/{}.json".format(candidate_msgid), "w") 

    msg_data = {
        'userid': userid,
        'msgid': msgid,
        'published': False 
    }

    json.dump(msg_data, spotfile)

    spotfile.close()

def load_pending_spot(candidate_msgid):
    spotfile = open("data/pending_spots/{}.json".format(candidate_msgid), "r") 

    return json.load(spotfile)

def delete_pending_spot(candidate_msgid):
    os.remove("data/pending_spots/{}.json".format(candidate_msgid)) 

def add_spot_data(msgid):
    spotfile = open("data/spots/{}.json".format(msgid), "w") 

    spot_data = {
        "user_reactions": {
            "u": 0,
            "d": 0
        },
        "voting_userids": {}
    }

    json.dump(spot_data, spotfile)

    spotfile.close()

def load_spot_data(msgid):
    spotfile = open("data/spots/{}.json".format(msgid), "r")
    
    return json.load(spotfile)

def save_spot_data(msgid, spotdata):
    spotfile = open("data/spots/{}.json".format(msgid), "w")
    json.dump(spotdata, spotfile)