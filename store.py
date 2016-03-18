import praw
import pprint
import sqlite3

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
                (ID TEXT, userID TEXT, title TEXT, 
                    content TEXT, time DATETIME, type TEXT, 
                    parentID TEXT, level INT);
                '''.format(topic_name))
            subreddit = self.reddit.get_subreddit(topic_name)
            submissions = subreddit.get_controversial(limit = limit)
            for submission in submissions:
                self.store_submission(submission, topic_name)
        except praw.errors.APIException as a:
            print('Error: {}'.format(a.ERROR_TYPE))
            self.db.execute('DROP TABLE {}'.format(topic_name))

        self.connection.commit()

    def store_comment(self, comment, table_name, level, parent_id = None):
        #Create table row contents.
        comment_id = comment.fullname
        userID = comment.author.name
        comment_text = comment.body
        comment_title = None
        comment_time = None #comment.created_utc
        comment_type = 'C'
        contents = (comment_id, userID, comment_title, 
            comment_text, comment_time, comment_type, parent_id, level)
        #Insert into database of title TABLE_NAME
        self.db.execute('''INSERT INTO {}
            (ID, userID, title, content, time, type, parentID, level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            '''.format(table_name), contents)
        print('Stored a comment!');
        #Fill in table for comment replies
        for reply in comment.replies:
            self.store_comment(reply, table_name, level + 1, comment_id)

    def store_submission(self, submission, table_name):
        submission_id = submission.fullname
        userID = submission.author.name
        submission_title = submission.title
        #print(submission_title)
        submission_text = submission.selftext
        submission_time = None #submission.created_utc
        submission_type = 'S'
        parent_id = None
        level = 0

        contents = (submission_id, userID, submission_title, submission_text,
            submission_time, submission_type, parent_id, level)
        self.db.execute('''INSERT INTO {}
            (ID, userID, title, content, time, type, parentID, level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            '''.format(table_name), contents)
        #curs = self.db.execute("SELECT * FROM {}".format(table_name))
        #print(self.db.fetchone())
        print('stored a submission!')
        submission.replace_more_comments()
        comments = submission.comments
        for comment in comments:
            self.store_comment(comment, table_name, level + 1, submission_id)

    def close_connection(self):
        self.connection.close()


user_agent = 'Comment Generator v4 /u/healthobserver'
db_name = 'test.db'
reddit_store = RedditStore(user_agent, db_name)
reddit_store.store_subreddit('mentalhealth', 20)
reddit_store.store_subreddit('bipolar', 20)
reddit_store.close_connection()
# fetchAndPrint(user_agent, 'mentalhealth', 5)