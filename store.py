import praw
import pprint
import sqlite3
from datetime import datetime

class RedditStore():
    topics = []
    def __init__(self, user_agent, fileName):
        self.connection = sqlite3.connect(fileName)
        self.db = self.connection.cursor()
        print('Opened database successfully')
        self.reddit = praw.Reddit(user_agent = user_agent)

    def store_subreddit(self, topic_name, limit):
        try:
            if topic_name in self.topics:
                print('Already stored this subreddit.')
                return
            self.topics.append(topic_name)
            self.db.execute('''CREATE TABLE {}
                (id TEXT, user_id TEXT, type TEXT, level INT,
                    parent_id TEXT, datetime DATETIME, title TEXT, 
                    content TEXT);
                '''.format(topic_name))
            subreddit = self.reddit.get_subreddit(topic_name)
            submissions = subreddit.get_top(limit = limit)
            for submission in submissions:
                self.store_submission(submission, topic_name)
        except praw.errors.APIException as a:
            print('Error: {}'.format(a.ERROR_TYPE))
            self.db.execute('DROP TABLE {}'.format(topic_name))
        self.connection.commit()

    def store_comment(self, comment, table_name, level, parent_id = None):
        #Create table row contents.
        comment_id = comment.fullname
        userID = author_name(comment.author)
        comment_text = comment.body
        comment_title = None
        comment_time = create_datetime(comment.created_utc)
        comment_type = 'C'
        contents = (comment_id, userID, comment_title, 
            comment_text, comment_time, comment_type, parent_id, level)
        #Insert into database of title TABLE_NAME
        col_names = ('id', 'user_id', 'title', 'content', 'datetime', 'type', 'parent_id', 'level')

        self.insert_row(table_name, col_names, contents)

        print('Stored a comment!');
        #Fill in table for comment replies
        for reply in comment.replies:
            self.store_comment(reply, table_name, level + 1, comment_id)

    def store_submission(self, submission, table_name):
        submission_id = submission.fullname
        userID = author_name(submission.author)
        submission_title = submission.title
        #print(submission_title)
        submission_text = submission.selftext
        submission_time = create_datetime(submission.created_utc)
        submission_type = 'S'
        parent_id = None
        level = 0

        col_names = ('id', 'user_id', 'title', 'content', 'datetime', 'type', 'parent_id', 'level')
        contents = (submission_id, userID, submission_title, submission_text,
            submission_time, submission_type, parent_id, level)

        self.insert_row(table_name, col_names, contents)

        print('stored a submission!')
        submission.replace_more_comments()
        comments = submission.comments
        for comment in comments:
            self.store_comment(comment, table_name, level + 1, submission_id)

    def insert_row(self, table_name, col_names, values):
        self.db.execute('''INSERT INTO {}
            {} VALUES ({}?)
            '''.format(table_name,
                self.tuple_to_string(col_names),'?,'*(len(values) - 1)
                ), values)

    def tuple_to_string(self, tpl):
        new_str = str(tpl).replace("'","")
        print(new_str)
        return new_str

    def close_connection(self):
        self.connection.close()

def author_name(author):
    if author == None:
        return None
    return author.name
def create_datetime(utc):
    return datetime.utcfromtimestamp(utc)
user_agent = 'Comment Generator v5 /u/healthobserver'
db_name = 'test3.db'
reddit_store = RedditStore(user_agent, db_name)
#reddit_store.store_subreddit('mentalhealth', 100)
reddit_store.store_subreddit('lol', 10)
reddit_store.close_connection()
# fetchAndPrint(user_agent, 'mentalhealth', 5)