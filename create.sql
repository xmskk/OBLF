-- SQLite
CREATE TABLE users (id TEXT PRIMARY KEY NOT NULL, summonername TEXT NOT NULL, region TEXT NOT NULL);
CREATE TABLE match_account (id TEXT NOT NULL, champid INTEGER NOT NULL, matchid INTEGER NOT NULL, lane TEXT NOT NULL, UNIQUE(id, matchid));
CREATE TABLE match_info (matchid INTEGER NOT NULL, champid INTEGER NOT NULL, win INTEGER NOT NULL, teamid INTEGER NOT NULL, turn INTEGER NOT NULL, lane TEXT NOT NULL, creation NUMERIC NOT NULL, UNIQUE(matchid, champid));
CREATE TABLE match_ban (matchid INTEGER NOT NULL, turn INTEGER NOT NULL, ban INTEGER NOT NULL, UNIQUE(matchid, turn));
CREATE TABLE winloss (id TEXT NOT NULL, matchid INTEGER NOT NULL, lane TEXT NOT NULL, champid INTEGER NOT NULL, echampid INTEGER NOT NULL, win INTEGER NOT NULL, UNIQUE(id, matchid));
CREATE TABLE loss_ratio (id TEXT NOT NULL, lane TEXT NOT NULL, echamp TEXT NOT NULL, ratio NUMERIC NOT NULL, UNIQUE(id, lane, echamp));
CREATE TABLE winloss_team (id TEXT NOT NULL, matchid INTEGER NOT NULL, echampid INTEGER NOT NULL, win INTEGER NOT NULL, UNIQUE(id, matchid, echampid));
CREATE TABLE loss_ratio_general (id TEXT NOT NULL, echamp TEXT NOT NULL, ratio NUMERIC NOT NULL, UNIQUE(id, echamp));
CREATE TABLE player_name (matchid INTEGER NOT NULL, turn INTEGER NOT NULL, summonername TEXT NOT NULL, UNIQUE(matchid, turn));

