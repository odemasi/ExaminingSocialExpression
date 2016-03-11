import praw
import pprint
import sqlite3
def createDB(fileName):
    #Currently in progress
    db = sqlite3.connect(fileName)
    print 'Opened database successfully'


def fetchAndPrint(user_agent, topic, limit):
    '''
    Prints the first tree of comments in list format
    from the most popular post in the subreddit TOPIC.
    '''
    r = praw.Reddit(user_agent = user_agent)
    subreddit = r.get_subreddit(topic)
    top = subreddit.get_top(limit = limit)
    for submission in top:
        comments = submission.comments
        flat_comments = praw.helpers.flatten_tree(comments)
        # for comment in flat_comments:
        #     if 'bipolar' in comment.body:
        #         print(comment.body)
        #print([comment.body for comment in flat_comments])
        print(flat_comments[0])

def create
user_agent = 'Comment Generator v1 /u/healthobserver'
fetchAndPrint(user_agent, 'mentalhealth', 5)