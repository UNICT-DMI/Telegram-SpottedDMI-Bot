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

# Function: load_pending_post
# Load an existing pending spot
def load_pending_spot(candidate_msgid):
    spotfile = open("data/pending_spots/{}.json".format(candidate_msgid), "r") 

    return json.load(spotfile)

# Function: delete_pending_post
# Delete an existing pending spot
def delete_pending_spot(candidate_msgid):
    os.remove("data/pending_spots/{}.json".format(candidate_msgid)) 

# Function: add_spot_data
# Create a data file for an already posted spot
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

# Function: load_spot_data
# Load spot data
def load_spot_data(msgid):
    spotfile = open("data/spots/{}.json".format(msgid), "r")
    
    return json.load(spotfile)

# Function: save_spot_data
# Save spot data
def save_spot_data(msgid, spotdata):
    spotfile = open("data/spots/{}.json".format(msgid), "w")
    json.dump(spotdata, spotfile)
    spotfile.close()
