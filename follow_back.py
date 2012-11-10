import oauth2 as oauth
import json
import logging
import sqlite3
import time

CONSUMER_KEY = 'ixi9mvjKiq26fxGuAWfn6Q'
CONSUMER_SECRET = 'IXhg2h77QqZPNzqct2wgoDQYKypRIEsB9eNvyy5UsA'

ACCESS_TOKEN = '17712723-xcKmCtA4BxBEPL4ZOm9ld6UGs0y8jEJwbP8PXYhjg'
ACCESS_SECRET = 'yKUidByMLI1H570ZnEQFN3gSPs4jVib6benpeXlwR4'

DATABASE = 'followers.db'
TWITTER_HANDLE = 'owenphen' #'singthattweet'

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def oauth_req(url, params={}, http_method="GET"):
    consumer = oauth.Consumer(key=CONSUMER_KEY, secret=CONSUMER_SECRET)
    token = oauth.Token(key=ACCESS_TOKEN, secret=ACCESS_SECRET)
    client = oauth.Client(consumer, token=token)

    request = client.request(url, headers=params)
    #this is a tuple of a response header and the response we care about
    return request

def get_user_info(handle_id):
    url = 'https://api.twitter.com/1.1/users/lookup.json?user_id=%s' % handle_id
    print url
    info, response = oauth_req(url)
    
    if info['status'] != '200':   
        logger.error(info)
        logger.error(response)
        logger.error('get a %s error trying to get user info for %s',
                     info['status'], handle_id)
        return []

    users = []
    peoples = json.loads(response)
    for peep in peoples:
        screen_name = peep.get('screen_name')
        users.append(screen_name)
    return users


def get_followers(handle_name):
    url = 'https://api.twitter.com/1.1/followers/ids.json&screen_name=%s&cursor=%s'
    cursor = -1
    users = []
    ids = True  

    while ids:
        params = {'screen_name': handle_name, 'cursor': str(cursor)}
        get_url = url % (handle_name, str(cursor))
        info, response = oauth_req(get_url, {})
        
        if info['status'] != '200':   
            logger.error(info)
            logger.error(response)
            logger.error('get a %s error trying to get followers %s',
                         info['status'], handle_name)
            return []

        loaded = json.loads(response)
        ids = loaded.get('ids')
        users.extend(ids)
        cursor += 1

        print loaded
        print params
        time.sleep(1)

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
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS
                followers
             (handle_name text, handle_id text)''')

def store_followers(followers):
    #followers is a tuple list of handle_names, handle_ids
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.executemany("INSERT INTO followers VALUES (?, ?)", followers)

def update_follower_db(all_followers):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    for handle_id in all_followers:
        c.execute("""SELECT handle_name, handle_id
                     FROM followers 
                     WHERE handle_id = ?
                  """, handle_id)
        results = c.fetchone()
        if results:
            continue
        else:
            yield get_



def follow_new(new_followers):
    for _, handle_id in new_followers:
        follow_id(handle_id)

def main():
    create_sql_tables()
    all_followers = get_followers(TWITTER_HANDLE)
    new_followers = update_follower_db(all_followers)
    follow_new(new_followers)


if __name__ == "__main__":
    main()
