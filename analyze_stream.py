import logging
import time
from secrets import *
import json
import multiprocessing


from utils import stream, TWITTER_HANDLE
#from utils import get_conn

logger = logging.getLogger(__name__)

PROCESS_NUM = 5

class SingTweetProcess(multiprocessing.Process):
    def __init__(self, queue, pid):
        multiprocessing.Process.__init__(self)
        self.pid2 = pid
        self.queue = queue

    def sing(self, text):
        #mock singing
        #upload to soundcloud
        pass

    def run(self):
        items = 0
        while True:
            items += 1
            tweet = self.queue.get()

            try:
                self.sing(tweet)
            except Exception, e:
                logger.error("singing failed %s %s: \n\t%s", time.ctime(), self.pid2, e)
            
            self.queue.task_done()

def check_stream():
    queue = multiprocessing.JoinableQueue(10000)

    processes = []
    for i in range(PROCESS_NUM):
        process = FixMetadataNullsProcess(queue, i, do_it)
        process.start()
        processes.append(process)

    for i in stream():
        try:
            tweet = json.loads(i)
            if tweet.get('user', {}).get('screen_name', None) == TWITTER_HANDLE:
                #skip my own shit
                continue
            tweet_text = tweet.get('text', None)
            if tweet_text:
                queue.put(tweet_text)

        except Exception, e:
            logger.error("unable to decode %r", i)
            logger.error("exception %r", e)

    queue.join()

def chill_brah():
    time.sleep(1)

def main():
    check_stream()
    chill_brah()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
