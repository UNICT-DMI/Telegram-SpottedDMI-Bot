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