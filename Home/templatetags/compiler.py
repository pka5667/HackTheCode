from time import sleep

import requests


def getSubmissionsResults(sid, count):
    count += 1
    url = 'https://ide.geeksforgeeks.org/submissionResult.php'
    data = {
        'sid': str(sid),
        'requestType': 'fetchResults'
    }
    r = requests.post(url, data=data)
    response = r.json()
    if count > 10:
        returnVal = {
            'status': 'ERROR',
            'outputType': 'rntError',
            'error': "TLE"
        }
        return returnVal
    if response['status'] == 'IN-QUEUE':
        sleep(1)
        return getSubmissionsResults(sid, count)
    returnVal = {
        'status': response['status'],
        'outputType': "output/error type"
    }
    if response['status'] == 'SUCCESS':
        if 'rntError' in response:
            returnVal['outputType'] = 'rntError'
            returnVal['error'] = response['rntError']
        if 'cmpError' in response:
            returnVal['outputType'] = 'cmpError'
            returnVal['error'] = response['cmpError']
            # if response['compResult'] == 'F':
            #     print("\ncompResult\n" + response['compResult'])
            # else:
            #     print("\ncompResult\n" + response['compResult'])
        returnVal['time'] = response['time']
        returnVal['memory'] = response['memory']
        if 'output' in response:
            returnVal['outputType'] = 'output'
            returnVal['output'] = response['output']
        else:
            returnVal['output'] = "No Output"
    return returnVal


def submitCodeToCompiler(language, code, input):
    try:
        url = 'https://ide.geeksforgeeks.org/main.php'
        data = {
            'lang': language,
            'code': code,
            'input': input,
            'save': False
        }
        count = 0
        r = requests.post(url, data=data)
        response = r.json()
        # print(response)
        if response['status'] == "ERROR":
            print(response['message'])
        elif response['status'] == 'SUCCESS':
            subResult = getSubmissionsResults(response['sid'], count)
            return subResult
    except Exception as e:
        return e


# submitCodeToCompiler("Python3",
# """
# a = input()'
# print(a)
# """,
#                      "14\n")

