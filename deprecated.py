import praw
import pprint
import sqlite3
from datetime import datetime

class RedditStore():
    place_holders = {}
    def __init__(self, user_agent):
        # self.connection = sqlite3.connect(fileName)
        # self.db = self.connection.cursor()
        # print('Opened database successfully')
        self.connection = None
        self.db = None
        self.reddit = praw.Reddit(user_agent = user_agent)
    def store_subreddit(self, topic_name, limit = None):
        try:
            self.connection = sqlite3.connect(topic_name+'.db')
            self.db = self.connection.cursor()
            print('Opened database successfully')
            name = self.db.execute("SELECT name FROM sqlite_master WHERE type= 'table' AND name= ?;", (topic_name,)).fetchall()
            if len(name) == 0:
                self.db.execute('''CREATE TABLE {}
                    (id TEXT, type TEXT, level INT, submission_id TEXT,
                        parent_id TEXT, pull_id INT);
                    '''.format(topic_name))

                self.db.execute('''CREATE TABLE {}
                    (id TEXT, user_id TEXT, datetime DATETIME, score INT, 
                        self_text TEXT);
                    '''.format(topic_name + '_comment_data'))

                #TODO: Add content type; link, video, etc.
                self.db.execute('''CREATE TABLE {}
                    (id TEXT, user_id TEXT, datetime DATETIME, score INT, title TEXT,
                        num_comments INT, article BOOLEAN, video BOOLEAN, picture BOOLEAN, self_text TEXT); 
                    '''.format(topic_name + '_submission_data'))

                self.db.execute('''CREATE TABLE {}
                    (pull_id INT, datetime DATETIME)'''.format(topic_name + '_pull_times'))
                pull_id = 0 
            else:
                pull_id = self.db.execute("SELECT MAX(pull_id) FROM {};".format(topic_name + '_pull_times')).fetchone()[0] + 1
            curr_time = datetime.now()
            self.insert_row(topic_name + '_pull_times', ('pull_id', 'datetime'), (pull_id, curr_time))
            self.connection.commit()
            subreddit = self.reddit.get_subreddit(topic_name)
            submissions = subreddit.get_top_from_month(limit = limit)
            for submission in submissions:
                self.store_submission(submission, topic_name, pull_id)
        except praw.errors.APIException as a:
            print('Error: {}'.format(a.ERROR_TYPE))

            #self.db.execute('DROP TABLE {}'.format(topic_name))
        self.connection.commit()
        self.connection.close()

    def store_new(self, topic_name, limit = None):
        try:
            self.connection = sqlite3.connect(topic_name+'.db')
            self.db = self.connection.cursor()
            print('Opened database successfully')
            name = self.db.execute("SELECT name FROM sqlite_master WHERE type= 'table' AND name= ?;", (topic_name,)).fetchall()
            if len(name) == 0:
                self.db.execute('''CREATE TABLE {}
                    (id TEXT, type TEXT, level INT, submission_id TEXT,
                        parent_id TEXT, pull_id INT);
                    '''.format(topic_name))

                self.db.execute('''CREATE TABLE {}
                    (id TEXT, user_id TEXT, datetime DATETIME, score INT, 
                        self_text TEXT);
                    '''.format(topic_name + '_comment_data'))

                #TODO: Add content type; link, video, etc.
                self.db.execute('''CREATE TABLE {}
                    (id TEXT, user_id TEXT, datetime DATETIME, score INT, title TEXT,
                        num_comments INT, article BOOLEAN, video BOOLEAN, picture BOOLEAN, self_text TEXT); 
                    '''.format(topic_name + '_submission_data'))

                self.db.execute('''CREATE TABLE {}
                    (pull_id INT, datetime DATETIME)'''.format(topic_name + '_pull_times'))
                pull_id = 0 
            else:
                pull_id = self.db.execute("SELECT MAX(pull_id) FROM {};".format(topic_name + '_pull_times')).fetchone()[0] + 1
            curr_time = datetime.now()
            self.insert_row(topic_name + '_pull_times', ('pull_id', 'datetime'), (pull_id, curr_time))
            self.connection.commit()
            subreddit = self.reddit.get_subreddit(topic_name)
            submissions = subreddit.get_top_from_month(limit = limit)
            for submission in submissions:
                self.store_submission(submission, topic_name, pull_id)
        except praw.errors.APIException as a:
            print('Error: {}'.format(a.ERROR_TYPE))

            #self.db.execute('DROP TABLE {}'.format(topic_name))
        self.connection.commit()
        self.connection.close()

    def store_comment(self, comment, table_name, level, submission_id, pull_id, parent_id = None): 
        #Create table row contents.
        comment_id = comment.fullname
        user_id = author_name(comment.author)
        comment_text = comment.body
        comment_time = create_datetime(comment.created_utc)
        comment_type = 'C'
        score = comment.score

        main_table_cols = ('id', 'type', 'level', 'submission_id', 'parent_id', 'pull_id')
        main_table_contents = (comment_id, comment_type, level, submission_id, parent_id, pull_id)
        data_table_cols = ('id', 'user_id', 'datetime', 'score','self_text')
        data_table_contents = (comment_id, user_id, comment_time, score, comment_text)

        self.insert_row(table_name, main_table_cols, main_table_contents)
        self.insert_row(table_name+'_comment_data', data_table_cols, data_table_contents)

        # self.insert_row(table_name, col_names, contents)
        print('Stored a comment!');
        #Fill in table for comment replies
        for reply in comment.replies:
            self.store_comment(reply, table_name, level + 1, submission_id, pull_id, comment_id)

    def determine_media(self, submission):
        picture = False
        article = False
        video = False
        post_id = submission.id
        url = submission.url
        if post_id in url:
            article = False
        elif 'imgur' in url:
            picture = True
        elif 'youtube' in url:
            video = True
        else:
            article = True
        return picture, article, video

    def store_submission(self, submission, table_name, pull_id):
        submission_id = submission.fullname
        user_id = author_name(submission.author)
        submission_title = submission.title
        submission_text = submission.selftext
        submission_time = create_datetime(submission.created_utc)
        score = submission.score
        submission_type = 'S'
        parent_id = None
        level = 0
        comment_count = submission.num_comments
        picture, article, video = self.determine_media(submission)

        main_table_cols = ('id', 'type', 'level', 'submission_id', 'parent_id', 'pull_id')
        main_table_contents = (submission_id, submission_type, level, submission_id, parent_id, pull_id)
        data_table_cols = ('id', 'user_id', 'datetime', 'score', 'title', 'num_comments', 'self_text', 'picture', 'article', 'video')
        data_table_contents = (submission_id, user_id, submission_time, score, submission_title, comment_count, submission_text, picture, article, video)
        self.insert_row(table_name, main_table_cols, main_table_contents)
        self.insert_row(table_name+'_submission_data', data_table_cols, data_table_contents)

        print('stored a submission!')
        submission.replace_more_comments()
        comments = submission.comments
        for comment in comments:
            self.store_comment(comment, table_name, level + 1,
                submission_id, pull_id, submission_id)


    def insert_row(self, table_name, col_names, values):
        self.db.execute('''INSERT INTO {}
            {} VALUES ({}?)
            '''.format(table_name,
                tuple_to_string(col_names),'?,'*(len(values) - 1)
                ), values)
        self.connection.commit()

    def table_contains(self, table_name, id):
        num_times = self.db.execute('select count(*) from {} where id = ?'.format(table_name), (id,)).fetchone()[0]
        return num_times != 0

    # def close_connection(self):
    #     self.connection.close()


def author_name(author):
    if author == None:
        return None
    return author.name

def create_datetime(utc):
    return datetime.utcfromtimestamp(utc)

def tuple_to_string(tpl):
    return str(tpl).replace("'","")


user_agent = 'Comment Generator v12 /u/healthobserver'
subreddits = ['mentalhealth', 'bipolar', ]
#db_name = 'test5.db'
reddit_store = RedditStore(user_agent)
for sub in subreddits:
    reddit_store.store_subreddit(sub, limit = 10)
#reddit_store.store_subreddit('mentalhealth', 100)
#reddit_store.store_subreddit('gaming')
#reddit_store.close_connection()
# fetchAndPrint(user_agent, 'mentalhealth', 5)
while True:
