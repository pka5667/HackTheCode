import random
import string

import pymongo
from allauth.socialaccount.models import SocialAccount
from bson import ObjectId
from django.contrib.auth import logout
from django.shortcuts import render, HttpResponse, redirect

from .templatetags.compiler import submitCodeToCompiler
from .templatetags.contestTimeHandler import sortLeaderBoard

from datetime import datetime, timedelta

client = pymongo.MongoClient(
    'mongodb+srv://pka5667:I4umh4UfJvWJhi48@cluster0.cfw04.mongodb.net/test?ssl=true&ssl_cert_reqs=CERT_NONE')

mydb = client['hackerRankClone']  # database name is hackerRankClone


# Create your views here.
def index(request):
    totalPoints = 0
    userinfo = mydb.users  # collection name is users
    if request.user.is_authenticated:
        # find user in mongodb database
        user = userinfo.find({'email': str(request.user.email)})
        if user.count() == 0:
            # if not there in mongodb then generate new username add user
            checkUserName = str(request.user)
            while True:
                findUserName = userinfo.find({'username': checkUserName})
                if findUserName.count() == 0:
                    userName = str(request.user)
                    break
                else:
                    checkUserName = checkUserName + random.choice(string.ascii_letters)
            userDataFromDjangoAuth = SocialAccount.objects.filter(extra_data__contains=request.user.email)
            userProfilePicture = userDataFromDjangoAuth[0].extra_data["picture"]
            userFullName = userDataFromDjangoAuth[0].extra_data["name"]
            record = {
                'username': userName,
                'email': request.user.email,
                'name': userFullName,
                'profilePicture': userProfilePicture
            }
            userinfo.insert_one(record)  # insert to dbsqlite(django default database)
        else:
            userArr = list(user)
            userName = userArr[0]["username"]
            if "totalPoints" in userArr[0]:
                totalPoints = userArr[0]["totalPoints"]

        # check if the username is same in both mongoDb and sqLite db
        # if not then change in sqlite
        reqUser = request.user
        if str(request.user.username) != userName:
            reqUser.username = userName
            reqUser.save()

    # get all the contests
    contestsColl = mydb.contests  # collection name is contests
    contests = contestsColl.find({})
    contests = list(contests)
    liveContests = []
    upcomingContests = []
    pastContests = []
    for contest in contests:
        contest["id"] = contest["_id"]
        contest["start"] += timedelta(hours=5, minutes=30)
        contest["end"] += timedelta(hours=5, minutes=30)
        if contest["contestStatus"] == "past":
            pastContests.append(contest)
        elif contest["contestStatus"] == "upcoming":
            upcomingContests.append(contest)
        elif contest["contestStatus"] == "live":
            liveContests.append(contest)
    return render(request, 'Home/Home.html', {"totalPoints": totalPoints, "liveContests": liveContests,
                                              "upcomingContests": upcomingContests,
                                              "pastContests": pastContests})


def about(request):
    return render(request, 'Home/about.html')


def contact(request):
    formSubmitted = "No"
    if request.method == 'POST':
        try:
            name = request.POST.get('name', default='')
            email = request.POST.get('email', default='')
            phone = request.POST.get('phone', default='')
            textarea = request.POST.get('txtarea', default='')

            mydb = client["hackerRankClone"]
            contact_us = mydb.contact_us
            record = {
                "email": email,
                "message": textarea,
                "name": name,
                "phone": phone,
                "time": datetime.utcnow()
            }

            contact_us.insert_one(record)

            formSubmitted = "True"
        except:
            formSubmitted = "False"

    params = {
        'formSubmitted': formSubmitted
    }
    return render(request, 'Home/contact.html', params)


def contestPageHandler(request, contestId):
    contestsColl = mydb.contests  # collection name is practiceProblems
    contests = contestsColl.find({"_id": ObjectId(contestId)})
    contestsArr = list(contests)
    contest = contestsArr[0]
    problemsArr = contest["problems"]
    for problem in problemsArr:
        problem["id"] = str(problem["_id"])
        problem["testCases"] = 'cannot show test cases'
    contestParams = {
        'contestId': contestId,
        'contestHostedBy': contest["hostedBy"]
    }
    return render(request, 'Home/contest.html', {'problems': problemsArr, 'contestParams': contestParams})


def practiceContestPageHandler(request):
    problemsColl = mydb.practiceProblems  # collection name is practiceProblems
    problems = problemsColl.find({})
    problems_list = list(problems)
    for i in problems_list:
        i['id'] = str(i["_id"])
        i["testCases"] = 'cannot show test cases'
    contestParams = {
        'contestId': "practiceProblems",
    }
    return render(request, 'Home/contest.html', {'problems': problems_list, 'contestParams': contestParams})


def problemPageHandler(request, contestId, problemId):
    if contestId == "practiceProblems":
        problemsColl = mydb.practiceProblems  # collection name is practiceProblems
        problem = problemsColl.find({'_id': ObjectId(problemId)})
        problemAsArray = list(problem)
        problem = problemAsArray[0]
        problem["id"] = str(problem["_id"])
    else:
        contestsColl = mydb.contests  # collection name is practiceProblems
        contests = contestsColl.find({"_id": ObjectId(contestId)})
        contestsArr = list(contests)
        contest = contestsArr[0]
        problemAsArray = contest["problems"]
        for i in problemAsArray:
            if i["_id"] == ObjectId(problemId):
                problem = i
                break
    problem["testCases"] = 'cannot show test cases'
    for sample in problem["sampleInOut"]:
        sample[0] = sample[0].replace("\n", "<br>")
        sample[1] = sample[1].replace("\\n", "<br>")
    return render(request, 'Home/problem.html',
                  {'problem': problem, 'contestId': contestId, 'problemId': problemId})


def profilePageHandler(request, userName):
    userinfo = mydb.users  # collection name is users
    user = userinfo.find({'username': userName})
    user = list(user)
    user = user[0]

    contestsColl = mydb.contests  # collection name is practiceProblems

    submittedProblems = [
        # [contestId,contestName,totalSolvedProblemsNumber]
        # [contestId,contestName,contestTime,[problems]]
    ]

    if "submittedProblems" in user:
        for key in user["submittedProblems"]:
            if key != "practiceProblems":
                contests = contestsColl.find({'_id': ObjectId(key)})
                contests = list(contests)
                if len(contests) == 1:
                    contest = contests[0]
                    contestName = contest["contestName"]
                    contestStart = contest["start"]
                    submittedProblems.append([key, contestName, contestStart, user["submittedProblems"][key]])

    # userDataFromDjangoAuth = SocialAccount.objects.filter(extra_data__contains=request.user.email)
    # userProfilePicture = userDataFromDjangoAuth[0].extra_data["picture"]
    userProfilePicture = user["profilePicture"]
    if "totalPoints" in user:
        totalPoints = user["totalPoints"]
    else:
        totalPoints = 0

    submissions = {
        "successful": 0,
        "wrong_answer": 0,
        "tle": 0,
        "runtime_error": 0,
        "compile_error": 0
    }
    if "submissions" in user:
        for key in user["submissions"]:
            submissions[key] = user["submissions"][key]

    name = user["name"]
    params = {
        "name": name,
        "userName": userName,
        "profilePicture": userProfilePicture,
        "submittedProblems": submittedProblems,
        "submissions": submissions,
        "totalPoints": totalPoints
    }
    return render(request, 'Home/profile.html', params)


def handleLogout(request):
    logout(request)
    request.session.flush()  # it will clear the session
    return redirect('home')


def setSuccessfulSubmission(request, contestId, problemId):
    if contestId == "practiceProblems":
        problemsColl = mydb.practiceProblems  # collection name is practiceProblems
        problem = problemsColl.find({'_id': ObjectId(problemId)})
        problemAsArray = list(problem)
        problem = problemAsArray[0]
        problemMaxScore = problem["maxScore"]
        if "submittedBy" not in problem:
            problem["submittedBy"] = []
        if str(request.user) not in problem["submittedBy"]:
            myquery = {'_id': ObjectId(problemId)}
            newvalues = {"$push": {"submittedBy": str(request.user)}}
            problemsColl.update_one(myquery, newvalues)

    else:
        contestsColl = mydb.contests  # collection name is contests
        contests = contestsColl.find({"_id": ObjectId(contestId)})
        contestsArr = list(contests)
        contest = contestsArr[0]
        problemAsArray = contest["problems"]
        for i in problemAsArray:
            if i["_id"] == ObjectId(problemId):
                problemMaxScore = i["maxScore"]
                problem = i
                break
        if "submittedBy" not in problem:
            problem["submittedBy"] = []
        # update leaderboard if live and add solved to problem id and user profile
        if str(request.user) not in problem["submittedBy"]:
            # add to contest.problem.submittefBy
            myquery = {"problems._id": ObjectId(problemId)}
            newValues = {"$push": {"problems.$.submittedBy": str(request.user)}}
            contestsColl.update(myquery, newValues)

            # then update leaderboard if live
            if contest["contestStatus"] == "live":
                # first check how many questions are solved by user
                userinfo = mydb.users  # collection name is users
                users = userinfo.find({'username': str(request.user)})
                user = list(users)[0]
                submittedProblems = user["submittedProblems"][contestId]
                score = (len(submittedProblems) + 1) * 100
                # for time
                time = datetime.utcnow() - contest["start"]
                if not datetime.utcnow() > contest["end"]:
                    # then update to leaderboard
                    # update value to existing leaderboard value else add new
                    myquery = {"_id": ObjectId(contestId), "leaderboard.userName": str(request.user)}
                    userInLeaderBoard = contestsColl.find(myquery)
                    if len(list(userInLeaderBoard)) == 0:
                        myquery = {"_id": ObjectId(contestId)}
                        newValues = {"$push": {"leaderboard": {"userName": str(request.user), "points": score}}}
                    else:
                        newValues = {"$set": {"leaderboard.$.points": score}}
                    contestsColl.update(myquery, newValues)
                    # leaderboard will be sorted automatically from contestTimeHandler script or we can sort here alse
                    sortLeaderBoard(contestId)

    # update in users profile also
    userinfo = mydb.users  # collection name is users
    user = userinfo.find({'username': str(request.user)})
    user = list(user)[0]
    if "submittedProblems" not in user:
        user["submittedProblems"] = {}
    submittedProblems = user["submittedProblems"]
    if contestId not in submittedProblems:
        submittedProblems[contestId] = []
    if problemId not in submittedProblems[contestId]:
        myQuery = {'username': str(request.user)}
        newValues = {"$push": {"submittedProblems." + contestId: problemId}}
        userinfo.update_one(myQuery, newValues)

        # add points to user profile for solving problem
        if "totalPoints" in user:
            usersTotalPoints = user["totalPoints"]
        else:
            usersTotalPoints = 0
        if contestId == "practiceProblems":
            newValues = {"$set": {"totalPoints": usersTotalPoints + problemMaxScore}}
            userinfo.update_one(myQuery, newValues)

        # increase successful problem number in user profile
        userinfo = mydb.users  # collection name is users
        user = userinfo.find({'email': str(request.user.email)})
        if "submissions" in user:
            submissions = user["submissions"]
        else:
            submissions = {}

        if "successful" in submissions:
            submissions["successful"] += 1
        else:
            submissions["successful"] = 1
        userinfo.update({'email': str(request.user.email)}, {"$set": {"submissions": submissions}})

    # check if contest ended to check  what to return after adding user submitted problem on all the places(
    # userProfile, problem[submittedBy], leaderboard)
    if contestId != "practiceProblems":
        if datetime.utcnow() > contest["end"]:
            return HttpResponse("You have submitted all correct but Contest Already Ended")
    return HttpResponse("All Correct")


def handleCodeSubmision(request, contestId, problemId):
    if not request.user.is_authenticated:
        return HttpResponse("Login/Signup to submit the problem")
    if request.method == 'POST':
        userinfo = mydb.users  # collection name is users
        user = userinfo.find({'email': str(request.user.email)})
        user = list(user)
        user = user[0]
        if "submissions" in user:
            submissions = user["submissions"]
        else:
            submissions = {}

        try:
            language = request.POST.get('language', default='')
            code = request.POST.get('code', default='')
            if contestId == "practiceProblems":
                problemsColl = mydb.practiceProblems  # collection name is practiceProblems
                problems = problemsColl.find({'_id': ObjectId(problemId)})
                problemAsArray = list(problems)
                problem = problemAsArray[0]
            else:
                contestsColl = mydb.contests  # collection name is contests
                contests = contestsColl.find({"_id": ObjectId(contestId)})
                contestsArr = list(contests)
                contest = contestsArr[0]
                problemAsArray = contest["problems"]
                problemAsArray = contest["problems"]
                for i in problemAsArray:
                    if i["_id"] == ObjectId(problemId):
                        problem = i
                        break

            for testCase in problem["testCases"]:
                testCase[0] = testCase[0].replace("\\n", "\n")
                testCase[1] = testCase[1].replace("\\n", "\n")
                output = submitCodeToCompiler(language, code, testCase[0])

                while " \n" in testCase[1]:
                    testCase[1] = testCase[1].replace(" \n", "\n")

                while testCase[1][-1] == ' ' or testCase[1][-1] == '\n':
                    testCase[1] = testCase[1].rstrip(testCase[1][-1])

                while " \n" in output["output"]:
                    output["output"] = output["output"].replace(" \n", "\n")

                while output["output"][-1] == ' ' or output["output"][-1] == '\n':
                    output["output"]["output"] = output["output"].rstrip(output[-1])

                # check output for correct output or errors or wrong answer
                if output["outputType"] == "output":
                    if output["output"] == testCase[1]:
                        # check TLE also
                        if int(output["time"]) >= int(problem["time"]):
                            if "tle" in submissions:
                                submissions["tle"] += 1
                            else:
                                submissions["tle"] = 1
                            userinfo.update({'email': str(request.user.email)}, {"$set": {"submissions": submissions}})

                            return HttpResponse(
                                "Error in test case " + str(
                                    problem["testCases"].index(testCase) + 1) + "\nTLE")
                        else:
                            # check for next test case
                            pass
                    else:
                        if "tle" in submissions:
                            submissions["wrong_answer"] += 1
                        else:
                            submissions["wrong_answer"] = 1
                        userinfo.update({'email': str(request.user.email)}, {"$set": {"submissions": submissions}})

                        return HttpResponse("Error in test case " + str(
                            problem["testCases"].index(testCase) + 1) + "\nWrong answer")
                else:
                    if output["outputType"] == "rntError":
                        if "runtime_error" in submissions:
                            submissions["runtime_error"] += 1
                        else:
                            submissions["runtime_error"] = 1
                    elif output["outputType"] == "cmpError":
                        if "compile_error" in submissions:
                            submissions["compile_error"] += 1
                        else:
                            submissions["compile_error"] = 1
                    userinfo.update({'email': str(request.user.email)}, {"$set": {"submissions": submissions}})

                    returnStr = "Error " + output["outputType"] + " in test case " + str(
                        problem["testCases"].index(testCase) + 1) + "\nError:\n" + output["error"]
                    return HttpResponse(returnStr)

            # when all test cases are passed
            # set succesful submission in users profile and in problem  id also
            returnStatement = setSuccessfulSubmission(request, contestId, problemId)
            return returnStatement
        except Exception as e:
            if "compile_error" in submissions:
                submissions["compile_error"] += 1
            else:
                submissions["compile_error"] = 1
            userinfo.update({'email': str(request.user.email)}, {"$set": {"submissions": submissions}})

            if str(e) == "'KeyError' object is not subscriptable":
                return HttpResponse("Compilation Error")
            return HttpResponse(e)
    else:
        return HttpResponse("Error 404! - Not found")


def leaderBoardPageHandler(request, contestId):
    if not request.user.is_authenticated:
        return HttpResponse("Login/Signup to see leaderboard")

    myRank = 0
    myPoints = 0
    if contestId == "allUsers":
        userinfo = mydb.users  # collection name is users
        users = userinfo.aggregate([
            # First sort all the docs by totalPoints
            {"$sort": {"totalPoints": -1}},
            # Take the first 100 of those
            # {"$limit": 100}
        ])
        users = list(users)
        leaderboard = []
        flag = 0
        myRank = 0
        for i in range(0, len(users)):
            if i <= 100 and "username" in users[i] and "totalPoints" in users[i]:
                leaderboard.append({
                    "userName": users[i]["username"],
                    "points": users[i]["totalPoints"]
                })
            if "username" in users[i]:
                if users[i]["username"] == str(request.user):
                    myRank = i + 1
                    if "totalPoints" in users[i]:
                        myPoints = users[i]["totalPoints"]
                    else:
                        myPoints = 0

                    flag += 1
            if i > 100 and flag >= 1:
                flag += 1
            if flag >= 2:
                break
        # contestName = "Top 100 users"
        contestName = "All users"
    else:
        contestsColl = mydb.contests  # collection name is contests
        contests = contestsColl.find({"_id": ObjectId(contestId)})
        contestsArr = list(contests)
        contest = contestsArr[0]
        contestName = contest["contestName"]
        if "leaderboard" in contest:
            leaderboard = contest["leaderboard"]
        else:
            leaderboard = []
    return render(request, "Home/leaderboard.html",
                  {"contestName": contestName, "leaderboard": leaderboard, "myRank": myRank, "myPoints": myPoints})
