# imports
from decimal import Decimal
import sys
from threading import local
import requests
import json
from datetime import datetime
from decouple import config
import time
import simplejson as json
from decimal import Decimal

from Helper import PrintDetail

# env vars
token = config('SECRET_TOKEN')
sesionsTable = config('SESION_TABLE')
movesTable = config('MOVES_TABLE')
excersizesTable = config('EXCERSIZE_TABLE')

# make sure to get the most recent notion version
notionVersion = "2021-08-16"

databaseUrl = f"https://api.notion.com/v1"
headers = {
    "Authorization" : "Bearer " + token,
    "Content-Type" : "application/json",
    "Notion-Version" : notionVersion
}

now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    
def SaveThePage(updateUrl, updateData):
    data = json.dumps(updateData, use_decimal=True)

    res = requests.request("PATCH", updateUrl, headers=headers, data=data)
    PrintDetail("LOG", "UPDATE STATUS", res.status_code)
    if (res.status_code != 200):
        PrintDetail("ERROR", "UPDATE CONTENT", res.content)

def UpdateMove(move, suggestion, pe):
    update = False

    if move["properties"]["Sugested Begining"]["number"] == None or move["properties"]["Sugested Begining"]["number"] < suggestion:
        update = True
    else:
        suggestion = move["properties"]["Sugested Begining"]["number"]

    if move["properties"]["Personal Best"]["number"] == None or move["properties"]["Personal Best"]["number"] < pe:
        update = True
    else:
        pe = move["properties"]["Personal Best"]["number"]
    

    if update:
        updateUrl = f"{databaseUrl}/pages/{move['id']}"
        updateData = {
            "properties" : {
                "Sugested Begining" : {
                    "number" : suggestion
                },
                "Personal Best" : {
                    "number" : pe
                }
            }
        }
        SaveThePage(updateUrl, updateData)

def UpdateExcersize(excersize, score):    
    updateUrl = f"{databaseUrl}/pages/{excersize['id']}"
    updateData = {
        "properties" : {
            "Score" : {
                "number": score
            }
        }
    }
    SaveThePage(updateUrl, updateData)

def UpdateSesion(sesion):
    updateUrl = f"{databaseUrl}/pages/{sesion['id']}"

    updateData = {
        "properties" : {
            "Calculated" : {
                "checkbox" : True
            }
        }
    }
    SaveThePage(updateUrl, updateData)

def GetDataFromUrl(url, localDB):
    res = requests.request("POST", url, headers=headers)
    PrintDetail("LOG", f"READ DB from {url} :", res.status_code)
    data = res.json()

    # saving
    with open(localDB, 'w', encoding='utf8') as f:
        json.dump(data, f, ensure_ascii=False)

    return data

def GetFromDBWithIds(localdb, ids):
    arr = []
    for element in localdb["results"]:
        if element["id"] in ids:
            arr.append(element)
    return arr

# return arr socre, suggestion, pe
def CalculateExcersize(excersize):
    i = 1
    score = 0
    pe = 0
    suggestion = 0
    size = 0
    while i < 8:
        if (len(excersize["properties"][f"{i}. Weight"]["rich_text"]) > 0 and excersize["properties"][f"{i}. Rep"]["number"] != None):
            weight = excersize["properties"][f"{i}. Weight"]["rich_text"][0]["plain_text"].split()
            level = excersize["properties"]["Level"]["rollup"]["array"][0]["number"]
            if len(weight) > 1:
                if weight[1] == "sec":
                    score += excersize["properties"][f"{i}. Rep"]["number"] * int(weight[0]) * level
                    pe = int(weight[0]) if int(weight[0]) > pe else pe
                    suggestion += int(weight[0])
                elif weight[1] == "min":
                    w = 0
                    if len(weight[0].split('.')) > 1:
                        w = int(weight[0].split('.')[0]) * 60 + int(weight[0].split('.')[1])
                    else:
                        w = int(weight[0]) * 60
                    score += excersize["properties"][f"{i}. Rep"]["number"] * w * level
                    pe = w if w > pe else pe
                    suggestion += w
                elif weight[1] == "hr":
                    w = 0
                    if len(weight[0].split('.')) > 1:
                        w = int(weight[0].split('.')[0]) * 60 * 60 + int(weight[0].split('.')[1]) * 60
                    else:
                        w = int(weight[0]) * 60 * 60
                    score += excersize["properties"][f"{i}. Rep"]["number"] * w * level
                    pe = w if w > pe else pe
                    suggestion += w
                else:
                    PrintDetail("ERROR", "WTF IS THIS WEIGHT", weight)
                    score = -sys.maxint - 1
            else:
                score += excersize["properties"][f"{i}. Rep"]["number"] * Decimal(weight[0]) * level
                pe = Decimal(weight[0]) if Decimal(weight[0]) > pe else pe
                suggestion += Decimal(weight[0])
            size+=1
        i+=1

    pe = pe if size != 0 else -1
    suggestion = suggestion/size if size != 0 else -1
    return [score, suggestion, pe]


def IterateAndUpdateDatabase():
    readSesionsUrl = f"{databaseUrl}/databases/{sesionsTable}/query"
    readMovesUrl = f"{databaseUrl}/databases/{movesTable}/query"
    readExcersizesUrl = f"{databaseUrl}/databases/{excersizesTable}/query"

    sesionsData = GetDataFromUrl(readSesionsUrl, "./sesions_db.json")
    movesData = GetDataFromUrl(readMovesUrl, "./moves_db.json")
    excersizesData = GetDataFromUrl(readExcersizesUrl, "./excersizes_db.json")

    # check the sesion if it is calculated 
    # if not calculate looking at the excersizes a sesion has
    # calculate the scores for the excersizes
    # get the pe and suggestion
    # update the excersize data
    # update the move data
    # update the session calculated

    for sesion in sesionsData["results"]:
        sesionId = sesion['id']

        if (sesion["properties"]["Calculated"]["checkbox"] == False):
            
            excersizeIds = [ex['id'] for ex in sesion["properties"]["Related to Exercises (Session)"]["relation"]]
            excersizes = GetFromDBWithIds(excersizesData, excersizeIds)
            for ex in excersizes:
                exScore = CalculateExcersize(ex)

                move = GetFromDBWithIds(movesData, [ex["properties"]["Move"]["relation"][0]["id"]])[0]
                UpdateMove(move, exScore[1], exScore[2])
                UpdateExcersize(ex, exScore[0])
            
            UpdateSesion(sesion)



if __name__ == "__main__":
    # main
    start_time = time.time()
    print(f"STARTING COACH , {start_time}")
    IterateAndUpdateDatabase()
    print(f"DONE, {time.time() - start_time}")