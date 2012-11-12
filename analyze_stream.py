import logging
import time
from secrets import *
import json
import multiprocessing
import random
from create_song import text_to_song_file
import upload_sc
import datetime

from utils import stream, TWITTER_HANDLE
#from utils import get_conn
from follow_back import create_tweet

logger = logging.getLogger(__name__)

PROCESS_NUM = 5

def tweet_song(username, title, url):
    tweet_text = '@%s I sang your song! %s' % (username, url)
    create_tweet(tweet_text)

class SingTweetProcess(multiprocessing.Process):
    def __init__(self, queue, pid):
        multiprocessing.Process.__init__(self)
        self.pid2 = pid
        self.queue = queue

    def sing(self, text, tweet_id, username):
        #mock singing
        #upload to soundcloud
        
        song_file = text_to_song_file(text, tweet_id)
        #song_file = '/tmp/test.wav'
        dt = datetime.datetime.now().strftime('%M-%d-%Y')
        title = '%s - %s - %s' % (username, dt, tweet_id)
        song_url = upload_sc.upload(song_file, title)
        tweet_song(username, title, song_url)

    def run(self):
        items = 0
        while True:
            items += 1
            try:
                text, tweet_id, user = self.queue.get()
                self.sing(text, tweet_id, user)
            except Exception, e:
                logger.error("singing failed %s %s: \n\t%s", time.ctime(), self.pid2, e)
            
            self.queue.task_done()

def check_stream():
    queue = multiprocessing.JoinableQueue(10000)

    processes = []
    for i in range(PROCESS_NUM):
        process = SingTweetProcess(queue, i)
        process.start()
        processes.append(process)

    for i in stream():
        try:
            tweet = json.loads(i)
            username = tweet.get('user', {}).get('screen_name', None)
            if username.lower() == TWITTER_HANDLE:
                #skip my own shit
                continue
            else:
                tweet_text = tweet.get('text', None)
                if tweet_text:
                    tweet_id = tweet.get('id_str', str(random.random() * 10000))
                    data =(tweet_text, tweet_id, username)
                    logger.info('queueing %r', data)
                    queue.put(data)

        except Exception, e:
            logger.error("unable to decode %r", i)
            logger.error("exception %r", e)

    queue.join()

def main():
    check_stream()
    
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
