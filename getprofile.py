import praw
import sqlite3

# Connecting to the database file with two columns, one for the Subreddit Thread, the other for the profile
conn = sqlite3.connect('Subreddit_Profiles.db')
c = conn.cursor()
c.execute('''CREATE TABLE Subreddit_Profiles
     (SubReddit text, Profile text)''')
subreddits = ['mentalhealth', 'bipolar', 'offmychest','SFTS', 'anxiety', 'depression', 'gaming', 'needadvice', 'offmychest']
r = praw.Reddit('demo')
#Iterates through subreddit to pull profile using the praw package, stores value into database
for sub in subreddits:
	profile = r.get_subreddit(sub).description
	c.execute("Insert into Subreddit_Profiles values (?,?)", (sub,profile))
	#Committing changes 
	conn.commit()

#closing the connection to the database file
conn.close()
