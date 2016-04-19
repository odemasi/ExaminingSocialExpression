import praw
import pprint
import sqlite3
import os
import time
import sys
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
            if topic_name not in self.place_holders:
                self.place_holders[topic_name] = None
            comments = self.reddit.get_comments(topic_name, place_holder = self.place_holders[topic_name])
            first_comment = next(comments)
            self.place_holders[topic_name] = first_comment.fullname
            for comment in comments:
                self.store_comment(comment, topic_name, pull_id)
        except praw.errors.APIException as a:
            print('Error: {}'.format(a.ERROR_TYPE))

            #self.db.execute('DROP TABLE {}'.format(topic_name))
        self.connection.commit()
        self.connection.close()

    def store_comment(self,comment, table_name, pull_id):
        comment_id = comment.fullname
        submission = comment.submission
        if self.table_contains(table_name, comment_id):
            return self.get_level(table_name, comment_id)

        if comment.is_root:
            parent_id = submission.fullname
            level = self.store_submission(submission, table_name, pull_id) + 1
        else:
            parent_id = comment.parent_id
            parent = self.reddit.get_info(thing_id = parent_id)
            level = self.store_comment(parent, table_name, pull_id) + 1

        submission_id = comment.submission.fullname
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
        print('Stored a comment!')
        self.update_comment_count(table_name, submission)
        return level

    def store_submission(self, submission, table_name, pull_id):
        submission_id = submission.fullname
        if self.table_contains(table_name+'_submission_data', submission_id):
            return 0
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
        return 0
        

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

    def update_comment_count(self, table_name, submission):
        submission_id = submission.fullname
        self.db.execute("update {} set num_comments = ? where id = ?".format(table_name + '_submission_data'),
            (submission.num_comments, submission_id,)
            )
        self.connection.commit()

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

    def get_level(self, table_name, id):
        level = self.db.execute('select level from {} where id = ?'.format(table_name), (id,)).fetchone()[0]
        return level


def author_name(author):
    if author == None:
        return None
    return author.name

def create_datetime(utc):
    return datetime.utcfromtimestamp(utc)

def tuple_to_string(tpl):
    return str(tpl).replace("'","")


user_agent = 'Comment Generator v12 /u/healthobserver'
subreddits = ['mentalhealth', 'bipolar', 'offmychest','']
#db_name = 'test5.db'
reddit_store = RedditStore(user_agent)
# for sub in subreddits:
#     reddit_store.store_new(sub, limit = 20)
#reddit_store.store_subreddit('mentalhealth', 100)
#reddit_store.store_subreddit('gaming')
#reddit_store.close_connection()
# fetchAndPrint(user_agent, 'mentalhealth', 5)


time_start = time.time()
seconds = 0
minutes = 0

while True:
    try:
        sys.stdout.write("\r{minutes} Minutes {seconds} Seconds".format(minutes=minutes, seconds=seconds)) # From stackoverflow
        sys.stdout.flush()
        for sub in subreddits:
            reddit_store.store_new(sub)
        time.sleep(1000)
        seconds = int(time.time() - time_start) - minutes * 60
        if seconds >= 60:
            minutes += 1
            seconds = 0
    except KeyboardInterrupt, e:
        break