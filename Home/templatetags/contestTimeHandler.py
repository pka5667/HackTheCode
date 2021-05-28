import threading
from datetime import datetime
from time import sleep

import pymongo
import requests
from bson import ObjectId

client = pymongo.MongoClient(
    'mongodb+srv://pka5667:I4umh4UfJvWJhi48@cluster0.cfw04.mongodb.net/test?ssl=true&ssl_cert_reqs=CERT_NONE')


def sortLeaderBoard(contestId):
    mydb = client['hackerRankClone']
    contestsColl = mydb.contests  # collection name is contests
    # https: // docs.mongodb.com / manual / reference / method / db.collection.aggregate
    # https: // stackoverflow.com / questions / 12432727 / sort - nested - array - of - objects
    a = contestsColl.aggregate([
        {"$match": {"_id": ObjectId(contestId)}},
        {"$unwind": "$leaderboard"},
        {"$sort": {"leaderboard.points": -1}},
        {"$group": {"_id": "$_id", "leaderboard": {"$push": "$leaderboard"}}}
    ])
    x = list(a)  # will be of length 1 only
    for i in x:
        contestsColl.update(
            {"_id": i["_id"]},
            {"$set": {"leaderboard": i["leaderboard"]}}
        )


def contestStatusChacker():
    mydb = client['hackerRankClone']  # database name is hackerRankClone
    contestsColl = mydb.contests  # collection name is contests
    contests = contestsColl.find()
    contestsArr = list(contests)
    for contest in contestsArr:
        if contest["contestStatus"] == "upcoming":
            if datetime.now() > contest["start"]:
                contestsColl.update({"_id": contest["_id"]},
                                    {"$set": {"contestStatus": "live"}})
                # print("Updated One upcoming to live")
        if contest["contestStatus"] == "live":
            # end the contest
            if datetime.now() > contest["end"]:
                contestsColl.update({"_id": contest["_id"]},
                                    {"$set": {"contestStatus": "past"}})
                # print("Updated One live to past")

                # update points to the each user profile according to percentile system


# handle upcoming past and live contest time and leaderboard
def pri():
    while True:
        # check if to update upcoming contest to live and live to past
        contestStatusChacker()
        requests.get("https://hackthecode.herokuapp.com/")
        sleep(60)


start_time = threading.Thread(target=pri)
start_time.start()
