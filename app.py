import requests
import json
import time
import sqlite3
import os
from flask import Flask, flash, jsonify, redirect, render_template, request
from sys import argv, exit

request_time = []
request_per_time = 99
time_limit = 120
apikey_input = '<<YOUR API KEY>>'
regions = {'Brazil':'BR1', 'EU North':'EUN1', 'EU West':'EUW1', 'Japan':'JP1', 'Korea':'KR', 'Latin America 1':'LA1', 'Latin America 2':'LA2', 'North America':'NA1', 'Oceanea':'OC1', 'Turkey':'TR1', 'Russia':'RU'}
has_champlist = False

app = Flask(__name__)
app.secret_key = os.urandom(24)


@app.route("/")
def index():
    global connection
    global cursor
    connection = sqlite3.connect('history.db', isolation_level=None)
    cursor = connection.cursor()
    get_champ_list()
    return render_template("index.html")

@app.route("/history", methods=["GET", "POST"])
def history():
    global champlist
    global connection
    global cursor
    connection = sqlite3.connect('history.db', isolation_level=None)
    cursor = connection.cursor()
    if request.method == "POST":
        cursor.execute("SELECT id FROM users WHERE summonername=? AND region=?;", (request.form.get('summonername'), request.form.get('region')))
        accountID_temp = cursor.fetchall()
        if not accountID_temp:
            flash("That summoner does not exist in the database yet!")
            return redirect("/history")
        accountID = accountID_temp[0][0]
        cursor.execute("SELECT COUNT(matchid) FROM match_account WHERE id=?;", [accountID])
        max_match = cursor.fetchall()[0][0]
        if int(request.form.get('max_game')) > max_match:
            flash("Not enough match data for that summoner!")
            return redirect("/history")
        games = get_player_history(accountID, request.form.get('max_game'))
        version = request_query("https://ddragon.leagueoflegends.com/api/versions.json").json()[0]
        get_champ_list()
        return render_template("history2.html", games=games, champlist=champlist, version=version, champnames=champnames)
    else:
        global regions
        return render_template("history1.html", regions=regions)

@app.route("/request", methods=["GET", "POST"])
def store_data():
    global connection
    global cursor
    connection = sqlite3.connect('history.db', isolation_level=None)
    cursor = connection.cursor()
    if request.method == "POST":
        summoner_input = request.form.get('summonername')
        region_input = request.form.get('region')
        end_input = 0
        if request.form.get('max_game'):
            end_input = int(request.form.get('max_game'))        
        return render_template("progress1.html", summoner_input=summoner_input, region_input=region_input, end_input=end_input)
    else:
        cursor.execute("SELECT summonername, region, COUNT(matchid) FROM users JOIN match_account ON match_account.id = users.id GROUP BY users.id, region;")
        tables = cursor.fetchall()
        global regions
        return render_template("request.html", regions=regions, tables=tables)

@app.route("/request2", methods=["POST"])
def store_data2():
    global connection
    global cursor
    connection = sqlite3.connect('history.db', isolation_level=None)
    cursor = connection.cursor()
    if request.method == "POST":
        summoner_input = request.form.get('summonername')
        region_input = request.form.get('region')
        end_input = 0
        if request.form.get('max_game'):
            end_input = int(request.form.get('max_game'))
        name = get_accountID(summoner_input, region_input, apikey_input)
        if name == -1:
            flash('That summoner name does not exist!')
            return redirect("/request")

        cursor.execute("SELECT COUNT(matchid) FROM match_account WHERE id = ?;", [name])
        start_input = cursor.fetchall()[0][0]
        end_input = start_input + end_input
        start_input = 0

        cursor.execute("SELECT matchid FROM match_account WHERE id = ?;", [name])
        stored_temp = cursor.fetchall()
        stored = []
        for game in stored_temp:
            stored.append(game[0])

        matches_temp = get_match_history(name, region_input, apikey_input, start_input, end_input, stored)

        if matches_temp == -1:
            flash("Could not find any ranked match history for that summoner!")
            return redirect("/request")

        matches = []
        for match in matches_temp:
            if not match["gameId"] in stored:
                matches.append(match)

        matches_info = get_match_info(matches, region_input, apikey_input)

        input_data(matches, matches_info, name, summoner_input, region_input)

        input_winloss(name)

        return redirect("/request")
    else:
        return redirect("/request")
        
@app.route("/ban", methods=["GET", "POST"])
def ban():
    if request.method == "POST":
        summoner_input = request.form.get('summonername')
        region_input = request.form.get('region')
        get_champ_list()
        return render_template("progress2.html", summoner_input=summoner_input, region_input=region_input)
    else:
        global regions
        return render_template("ban.html", regions=regions)

@app.route("/ban2", methods=["POST"])
def ban2():
    global connection
    global cursor
    connection = sqlite3.connect('history.db', isolation_level=None)
    cursor = connection.cursor()
    if request.method == "POST":
        summoner_input = request.form.get('summonername')
        region_input = request.form.get('region')
        cursor.execute("SELECT id FROM users WHERE summonername=? AND region=?;", (summoner_input, region_input))
        name_temp = cursor.fetchall()
        if not name_temp:
            flash("That summoner does not exist in the database yet!")
            return redirect("/ban")
        name = name_temp[0][0]
        clean_up(name)
        
        suggestion1 = suggest_ban_role(name, get_roles_played(name))

        suggestion2 = suggest_ban_general(name)
        
        version = request_query("https://ddragon.leagueoflegends.com/api/versions.json").json()[0]

        return render_template("suggestion.html", suggestion1=suggestion1, suggestion2=suggestion2, version=version, champnames=champnames)

def assemble_url(query, region, api_key, *argv):
    #Assembles a query url based on inputs
    if not argv:
        url = 'https://' + region + '.api.riotgames.com/lol/' + query + '?queue=420'+ '&api_key=' + api_key
    else:
        url = 'https://' + region + '.api.riotgames.com/lol/' + query + '?queue=420' + argv[0] + '&api_key=' + api_key
    return url

def request_query(url):
    #Returns the results of a url query
    global request_time
    request_time.append(time.time())
    check_request()
    return requests.get(url)

def get_accountID(summoner, region, api_key):
    #Gets the encrypted accountID based on the summoner name and region
    result = request_query(assemble_url('summoner/v4/summoners/by-name/' + summoner, region, api_key))
    if not str(result) == '<Response [200]>':
        return -1
    else:
        id = result.json()["accountId"]
    return id

def get_history(accountID, region, api_key, *argv):
    #Gets the match history of the last 100 games
    if not argv:
        result = request_query(assemble_url('match/v4/matchlists/by-account/' + accountID, region, api_key))
    else:
        result = request_query(assemble_url('match/v4/matchlists/by-account/' + accountID, region, api_key, argv[0]))
    if not str(result) == '<Response [200]>':
        return -1
    else:
        history = result.json()
    return history

def get_match_history(accountID, region, api_key, start, end, stored):
    #Gets the set number of games played by the user
    history_total = []
    if end > 0:
        while start < end:
            if end - start > 100:
                history = get_history(accountID, region, api_key, '&beginIndex=' + str(start))
            elif end - start <= 100:
                history = get_history(accountID, region, api_key, '&beginIndex=' + str(start) + '&endIndex=' + str(end))
            if history == -1:
                return -1
            start = history["endIndex"]
            total = history["totalGames"]
            history_total.extend(history["matches"])
            if start >= total:
                break
    return(history_total)

def get_match_info(matches, region, api_key):
    #Gets the match details of each games
    match_info = []
    for match in matches:
        match_info.append(request_query(assemble_url('match/v4/matches/' + str(match["gameId"]), region, api_key)))
    return match_info
    
def check_request():
    #Checks if too many API requests have been made within Riot's time limit and sleeps for however many seconds necessary
    global request_time
    global request_per_time
    global time_limit
    if len(request_time) >= request_per_time:
        if request_time[len(request_time) - request_per_time] >= time.time() - time_limit:
            sleep_time = request_time[len(request_time) - request_per_time] - (time.time() - time_limit)
            print("Sleeping " + "{:.2f}".format(round(sleep_time, 2)) + " seconds to reset request timer...")
            time.sleep(sleep_time)
            del request_time[0:len(request_time) - request_per_time + 1]
    return True

def input_data(matches, matches_info, accountID, summoner, region):
    #Stores data for multiple tables
    try:
        cursor.execute("INSERT INTO users VALUES (?, ?, ?);", (accountID, summoner, region))
    except:
        #print("Insert failed 1")
        pass
    for match in matches:
        try:
            cursor.execute("INSERT INTO match_account VALUES (?, ?, ?, ?);", (accountID, match["champion"], match["gameId"], match["lane"]))
        except:
            #print("Insert failed 2")
            pass
    for detail in matches_info:
        try:
            for player in detail.json()["participants"]:
                try:
                    cursor.execute("INSERT INTO match_info VALUES (?, ?, ?, ?, ?, ?, ?);", (detail.json()["gameId"], player["championId"], player["stats"]["win"], player["teamId"], player["stats"]["participantId"], player["timeline"]["lane"], detail.json()["gameCreation"]))
                except:
                    #print("Insert failed 3")
                    pass
            for team in detail.json()["teams"]:
                for ban in team["bans"]:
                    try:
                        cursor.execute("INSERT INTO match_ban VALUES (?, ?, ?);", (detail.json()["gameId"], ban["pickTurn"], ban["championId"]))
                    except:
                        #print("Insert failed 4")
                        pass
            for user in detail.json()["participantIdentities"]:
                try:
                    cursor.execute("INSERT INTO player_name VALUES (?, ?, ?);", (detail.json()["gameId"], user["participantId"], user["player"]["summonerName"]))
                except:
                    #print("Insert failed 8")
                    pass
        except:
            #print("Key Error!")
            pass
    return True

def get_roles_played(accountID):
    #Returns the most played roles of the user
    cursor.execute("SELECT lane, COUNT(matchid) FROM match_account WHERE id = ? GROUP BY lane ORDER BY COUNT(matchid) DESC;", [accountID])
    rows = cursor.fetchall()
    for i in range(len(rows)):
        if rows[i][0] == 'NONE':
            del rows[i]
            break
    rows_temp = []
    lanes = ['TOP', 'JUNGLE', 'MID', 'BOTTOM']
    for row in rows:
        rows_temp.append(row[0])
    for lane in lanes:
        if not lane in rows_temp:
            rows.append((lane, 0))    
    return rows

def input_winloss(accountID):
    #If there is data of the user's lane and the lane opponent in a match, store that data and if the user won or not
    cursor.execute("SELECT id, match_account.matchid, match_account.lane, match_account.champid, win, teamid FROM match_account JOIN match_info ON match_account.matchid = match_info.matchid AND match_account.champid = match_info.champid WHERE id = ?;", [accountID])
    mygame = cursor.fetchall()
    for row in mygame:
        cursor.execute("SELECT champid FROM match_info WHERE NOT teamid = ? AND matchid = ?;", (row[5], row[1]))
        eteam = cursor.fetchall()
        for enemy in eteam:
            try:
                cursor.execute("INSERT INTO winloss_team VALUES (?, ?, ?, ?);", (accountID, row[1], enemy[0], row[4]))
            except:
                #print("Insert failed 6")
                pass
        if not row[2] == 'NONE':
            cursor.execute("SELECT matchid, champid, lane FROM match_info WHERE NOT teamid = ? AND matchid = ? AND lane LIKE ?;", (row[5], row[1], row[2] + '%'))
            temp = cursor.fetchall()
            if temp:
                opponent = temp.pop(0)
                try:
                    cursor.execute("INSERT INTO winloss VALUES (?, ?, ?, ?, ?, ?);", (row[0], row[1], row[2], row[3], opponent[1], row[4]))
                except:
                    #print("Insert failed 5")
                    pass
    return True

def suggest_ban_role(accountID, most):
    #Returns a dict where key is role and value is a list of champions (max 3)
    cursor.execute("DELETE FROM loss_ratio;")
    suggestion = {}
    for role in most:
        if role[1] >= 0:
            cursor.execute("SELECT echampid, count(matchid) FROM winloss WHERE lane LIKE ? AND id = ? AND win = 1 GROUP BY echampid, win ORDER BY echampid;", ('%' + role[0] + '%', accountID))
            result_win = cursor.fetchall()
            cursor.execute("SELECT echampid, count(matchid) FROM winloss WHERE lane LIKE ? AND id = ? AND win = 0 GROUP BY echampid, win ORDER BY echampid;", ('%' + role[0] + '%', accountID))
            result_loss = cursor.fetchall()
            for i in range(len(result_win)):
                result_win[i] = list(result_win[i])
                result_win[i][0] = champlist[str(result_win[i][0])]
            for i in range(len(result_loss)):
                result_loss[i] = list(result_loss[i])
                result_loss[i][0] = champlist[str(result_loss[i][0])]
            dict_win = dict(result_win)
            dict_loss = dict(result_loss)
            for champ in dict_loss:
                try:
                    ratio = dict_loss[champ] / dict_win[champ]
                except:
                    ratio = dict_loss[champ] / 0.8
                try:
                    cursor.execute("INSERT INTO loss_ratio VALUES (?, ?, ?, ?);", (accountID, role[0], champ, ratio))
                except:
                    cursor.execute("UPDATE loss_ratio SET ratio = ? WHERE id = ? AND lane = ? AND echamp = ?;", (ratio, accountID, role[0], champ))
            cursor.execute("SELECT echamp FROM loss_ratio WHERE id = ? AND lane LIKE ? ORDER BY ratio DESC LIMIT 3;", (accountID, '%' + role[0] + '%'))
            top3 = cursor.fetchall()
            top3_list = []
            for champ in top3:
                top3_list.append(champ[0])
            suggestion[role[0]] = top3_list
    return suggestion

def suggest_ban_general(accountID):
    #Returns a list of 5 champions that the user should ban
    cursor.execute("DELETE FROM loss_ratio_general;")
    suggestion = []
    cursor.execute("SELECT echampid, count(matchid) FROM winloss_team WHERE id = ? AND win = 1 GROUP BY echampid, win ORDER BY echampid;", [accountID])
    result_win = cursor.fetchall()
    cursor.execute("SELECT echampid, count(matchid) FROM winloss_team WHERE id = ? AND win = 0 GROUP BY echampid, win ORDER BY echampid;", [accountID])
    result_loss = cursor.fetchall()
    for i in range(len(result_win)):
        result_win[i] = list(result_win[i])
        result_win[i][0] = champlist[str(result_win[i][0])]
    for i in range(len(result_loss)):
        result_loss[i] = list(result_loss[i])
        result_loss[i][0] = champlist[str(result_loss[i][0])]
    dict_win = dict(result_win)
    dict_loss = dict(result_loss)
    for champ in dict_loss:
        try:
            ratio = dict_loss[champ] / dict_win[champ]
        except:
            ratio = dict_loss[champ] / 0.8
        try:
            cursor.execute("INSERT INTO loss_ratio_general VALUES (?, ?, ?);", (accountID, champ, ratio))
        except:
            cursor.execute("UPDATE loss_ratio_general SET ratio = ? WHERE id = ? AND echamp = ?;", (ratio, accountID, champ))
    cursor.execute("SELECT echamp FROM loss_ratio_general WHERE id = ? ORDER BY ratio DESC LIMIT 5;", [accountID])
    top5 = cursor.fetchall()
    for champ in top5:
        suggestion.append(champ[0])
    return suggestion

def clean_up(accountID):
    #cleans up low encounter enemy champions form the tables
    cursor.execute("SELECT echampid, COUNT(matchid) FROM winloss WHERE id = ? GROUP BY echampid HAVING COUNT(matchid) < 20;", [accountID])
    result = cursor.fetchall()
    for champ in result:
        cursor.execute("DELETE FROM winloss WHERE id = ? AND echampid = ?;", (accountID, champ[0]))

    cursor.execute("SELECT echampid, COUNT(matchid) FROM winloss_team WHERE id = ? GROUP BY echampid HAVING COUNT(matchid) < 50;", [accountID])
    result = cursor.fetchall()
    for champ in result:
        cursor.execute("DELETE FROM winloss_team WHERE id = ? AND echampid = ?;", (accountID, champ[0])) 
    return True

def get_champ_list():
    #Receive the list of champions and their id code
    global has_champlist
    if not has_champlist:
        champions = request_query('http://ddragon.leagueoflegends.com/cdn/10.19.1/data/en_US/champion.json')
        global champlist
        global champnames
        champnames = {}
        champlist = {}
        for champ in champions.json()['data']:
            champlist[champions.json()['data'][champ]['key']] = champions.json()['data'][champ]['name']
            champnames[champions.json()['data'][champ]['name']] = champ
        has_champlist = True
    return True

def get_player_history(accountID, max_game):
    #Returns the 'max_game' number of games that the user played
    cursor.execute("SELECT match_info.matchid FROM match_info JOIN match_account ON match_account.matchid = match_info.matchid AND match_account.champid = match_info.champid WHERE id=? ORDER BY creation DESC LIMIT ?;", (accountID, max_game))
    matches = cursor.fetchall()
    games = []
    for match in matches:
        cursor.execute("SELECT match_info.matchid, match_info.champid, teamid, win, summonername FROM match_info JOIN match_account ON match_account.matchid = match_info.matchid JOIN player_name ON player_name.matchid = match_info.matchid AND player_name.turn = match_info.turn WHERE id=? AND match_info.matchid=? ORDER BY creation DESC, teamid ASC LIMIT ?;", (accountID, match[0], 10))
        games.append(cursor.fetchall())
    return games