import json
import logging
import time

from utils import oauth_req
from utils import get_conn
from utils import TWITTER_HANDLE

logger = logging.getLogger(__name__)

def get_user_info(handle_ids):
    url = 'https://api.twitter.com/1.1/users/lookup.json?user_id=%s'

    handle_ids = ','.join([str(x) for x in handle_ids])
    print '%r' % handle_ids
    print type(handle_ids)

    params = {}
    url = url % handle_ids
    info, response = oauth_req(url, params)
    
    if info['status'] != '200':   
        logger.error(info)
        logger.error(response)
        logger.error('get a %s error trying to get user info for %s',
                     info['status'], handle_ids)
        return

    print response
    people = json.loads(response)
    for peep in people:
        id = peep.get('id')
        name = peep.get('screen_name')
        yield name, id

def create_tweet(tweet):
    url = 'http://api.twitter.com/1.1/statuses/update.json'
    params = {
        'status': tweet
    }
    info, response = oauth_req(url, params, 'POST')
    
    if info['status'] != '200':   
        logger.error(info)
        logger.error(response)
        logger.error('get a %s error trying to tweet %r',
                     info['status'], tweet)
        


def get_followers(handle_name):
    url = 'https://api.twitter.com/1.1/followers/ids.json'
    cursor = -1
    users = []
    ids = True  

    while cursor:
        params = {'screen_name': handle_name, 'cursor': str(cursor)}
        #get_url = url + '&screen_name=%s&cursor=%s' % (handle_name, str(cursor))

        info, response = oauth_req(url, params)

        if info['status'] != '200':   
            logger.error(info)
            logger.error(response)
            logger.error('get a %s error trying to get followers %s',
                         info['status'], handle_name)
            return []

        loaded = json.loads(response)
        ids = loaded.get('ids')
        users.extend(ids)
        cursor = info.get('next_cursor_str')

    return users

def follow_id(handle_id):
    url = 'https://api.twitter.com/1.1/friendships/create.json'
    params = {'user_id': str(handle_id), 'follow': True}

    info, response = oauth_req(url, params, 'POST')
        
    if info['status'] != '200':   
        logger.error(info)
        logger.error(response)
        logger.error('get a %s error trying to get user info for %s',
                     info['status'], handle_id)
        return False

    return True

def create_sql_tables():
    conn = get_conn()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS
                followers
             (handle_name text, handle_id text)''')

def store_followers(followers):
    #followers is a tuple list of handle_names, handle_ids
    conn = get_conn()
    c = conn.cursor()
    c.executemany("INSERT INTO followers VALUES (?, ?)", followers)

def update_follower_db(all_followers):
    conn = get_conn()
    new = []
    c = conn.cursor()
    for handle_id in all_followers:
        c.execute("""SELECT handle_name, handle_id
                     FROM followers 
                     WHERE handle_id = ?
                  """, (handle_id, ))
        results = c.fetchone()
        if results:
            continue
        else:
            new.append(handle_id)

    return get_user_info(new)

def follow_new(new_followers):
    for _, handle_id in new_followers:
        follow_id(handle_id)

def main(username=TWITTER_HANDLE):
    create_sql_tables()
    while True:
        try:
            all_followers = get_followers(username)
            new_followers = update_follower_db(all_followers)
            new_followers = list(new_followers)
            store_followers(new_followers)
            follow_new(new_followers)

        except Exception, e:
            logger.error("caught excepion, %r", e)
        
        time.sleep(60)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
