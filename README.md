Welcome to OBLF (Optimal Ban List Finder)
This is my final project for the course CS50 on edX
For any questions or comments please contact: xmskk24@gmail.com

--------------------------------------------------

In order for this application to work, it requires a Riot Games API key.

Please input your API key at app.py on line 12 if you want to use this application.

--------------------------------------------------

This web application has two major functions:
1. Display match history for a specific player in the game League of Legends.
2. Based on match history, suggest ban lists for a specific player in the game League of Legends.

--------------------------------------------------

In order to understand this applicaiton, one only needs to know the following:
1. League of Legends is an online competitive game played by 2 teams (5 players on each team with a total of 10 players).
2. Before a game of League of Legends, each player picks a single champion (from a list of 150+) to play for that game.
3. No one champion can be picked by more than one player.
4. Before the players pick a chmpion, each player bans a single champion
5. If a champion is banned, no player can pick that champion
6. Once in game, each player plays in a certain lane (similar to positions in a game of soccer)

If interested, detailed information on the game League of Legends can be found at: https://en.wikipedia.org/wiki/League_of_Legends or https://na.leagueoflegends.com/en-us/

--------------------------------------------------

Index ("/"):

This page consists of three buttons that will take the user to the other 3 pages of this application.

However, the 'Match History' and 'Ban Suggestion' functions can not be used before storing data at 'Store Data'

--------------------------------------------------

Match History ("/history"):

This page receives input of the summoner name (=player name), the region (=server) that summoner is in, and the number of games that the user wants displayed. The maximum input for the number of games is 20 and the minimum input is 1.

The output will show a list of tables where each table represents a single game. Each row of the table displays one player for team 1 and another player for team 2. Each item in the table displays the portrait and the name of the champion that a player played above the player's summoner name. The team that won is displayed in blue blocks, whereas the team that lost is displayed in red blocks.

Again, this page can only display games that are already stored in the 'Store Data' page.

--------------------------------------------------

Ban Suggestions ("/ban"):

This page receives input of the Summoner Name (=player name), and the region (=server) that summoner is in. Based on the previous games and the winrates per enemy champion, this page returns several lists of champions the user should consider banning in order for a higher winrate. 

The lists are categorized into 5 categories that are displayed in 5 different cards. The first 4 cards represent a certain lane (=position) and the last card represents non lane specific. The first 4 cards show the top 3 champions (in oder) that the user should consider banning while the 5th card shows the top 5 champions (in order). If the user does not have enough data for a category to make a meaningful output, it will print "Not enough game data!".

Again, the user can only get ban suggestions for a player that already has data stored in the 'Store Data' page.

--------------------------------------------------

Store Data ("/request"):

This page receives input of the summoner name (=player name), the region (=server) that summoner is in, and the number of games that the user wants stored. The page then requests and stores the data from the Riot Games API for the application to use.

If there are any new games played by the user since the last update, the application will store the data of the newest games first.

Note that Riot Games limits the number of API requests to 100 per 2 minutes. Which means that in order to save data for 2000 games, the application will require ~45 minutes.

The table at the bottom depicts the data that is already stored.

--------------------------------------------------