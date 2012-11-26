import json
import logging
import time

from utils import oauth_req
from utils import follower_cursor
from utils import TWITTER_HANDLE

logger = logging.getLogger(__name__)
INIT_SLEEP_TIME = 120
SLEEP_TIME = INIT_SLEEP_TIME

def get_user_info(handle_ids):
    url = 'https://api.twitter.com/1.1/users/lookup.json?user_id=%s'

    orig_handle_ids = handle_ids
    handle_ids = ','.join([str(x) for x in handle_ids])
    params = {}
    url = url % handle_ids
    info, response = oauth_req(url, params)

    if info['status'] == '404':
        # 404 for suspended accounts
        for id_ in orig_handle_ids:
            yield 'SUSPENDED', id_
        return
    elif info['status'] != '200':   
        logger.error(info)
        logger.error(response)
        logger.error('get a %s error trying to get user info for %s',
                     info['status'], handle_ids)
        return

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

    while True:
        info, response = oauth_req(url, params, 'POST')

        if info['status'] == '429':
            sleep_til = float(info.get('x-rate-limit-reset', time.time() + 120))
            time_to_sleep = sleep_til - time.time()
            logger.error('Hit rate limit while tweeting, sleeping for %s until %s', SLEEP_TIME, sleep_til)
            time.sleep(time_to_sleep)
            logger.error('Trying to tweet again...')
        elif info['status'] != '200':
            logger.error(info)
            logger.error(response)
            logger.error('got a %s error trying to tweet %r',
                         info['status'], tweet)
        else:
            logger.info('Successfully tweeted: %s', tweet)
            break

def get_followers(handle_name):
    global SLEEP_TIME
    url = 'https://api.twitter.com/1.1/followers/ids.json'
    cursor = -1
    users = []
    ids = True  

    while cursor:
        params = {'screen_name': handle_name, 'cursor': str(cursor)}
        info, response = oauth_req(url, params)

        if info['status'] == '429':
            sleep_til = float(info.get('x-rate-limit-reset', time.time() + 120))
            SLEEP_TIME = sleep_til - time.time()
            if SLEEP_TIME < 10:
                SLEEP_TIME = 10
            logger.error('Hit rate limit, sleeping for %s until %s', SLEEP_TIME, sleep_til)
            return []
        elif info['status'] != '200':   
            logger.error('got a %s error trying to get followers %s',
                         info['status'], handle_name)
            logger.error(info)
            logger.error(response)

            return []

        loaded = json.loads(response)
        ids = loaded.get('ids')
        users.extend(ids)
        cursor = info.get('next_cursor_str')

    return users

def follow_id(handle_id):
    url = 'https://api.twitter.com/1.1/friendships/create.json'
    params = {'user_id': str(handle_id), 'follow': True}

    logger.debug('Following user_id: %s', handle_id)
    info, response = oauth_req(url, params, 'POST')

    if info['status'] != '200':   
        logger.error('get a %s error trying to follow %s',
                     info['status'], handle_id)
        logger.error(info)
        logger.error(response)
        return False

    return True

def create_sql_tables():
    with follower_cursor() as cur:
        cur.execute('''CREATE TABLE IF NOT EXISTS
                       followers
                       (handle_name text, handle_id text)''')

def store_followers(followers):
    #followers is a tuple list of handle_names, handle_ids
    if followers:
        logger.debug('Inserting into follower db: %r', followers)
    else:
        logger.debug('No new followers to insert into db')
    with follower_cursor() as cur:
        cur.executemany("INSERT INTO followers (`handle_name`, `handle_id`) VALUES (?, ?)", followers)

def update_follower_db(all_followers):
    new = []
    with follower_cursor() as cur:
        for handle_id in all_followers:
            cur.execute('''
              SELECT 1
              FROM followers 
              WHERE handle_id = ?
            ''', (handle_id,))
            results = cur.fetchone()
            if results:
                continue
            else:
                logger.debug("Found new follower: %s", handle_id)
                new.append(handle_id)

    if new:
        return get_user_info(new)
    else:
        return []

def follow_new(new_followers):
    for _, handle_id in new_followers:
        follow_id(handle_id)

def main(username=TWITTER_HANDLE):
    global SLEEP_TIME
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
        
        time.sleep(SLEEP_TIME)
        if SLEEP_TIME != INIT_SLEEP_TIME:
            SLEEP_TIME = INIT_SLEEP_TIME

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
