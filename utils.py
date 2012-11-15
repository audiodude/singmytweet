import oauth2 as oauth
import sqlite3
import urllib
import time
import md5
import random
import urllib2
from contextlib import contextmanager

from secrets import *

DATABASE = 'followers.db'
TWITTER_HANDLE ='singthattweet'

STREAM_URL = "https://userstream.twitter.com/2/user.json"

def _generate_nonce():
    random_number = ''.join(str(random.randint(0, 9)) for i in range(40))
    m = md5.new(str(time.time()) + str(random_number))
    return m.hexdigest()

def stream(stream_url=STREAM_URL):
    access_token = oauth.Token(ACCESS_TOKEN, ACCESS_SECRET)
    consumer = oauth.Token(CONSUMER_KEY, CONSUMER_SECRET)

    parameters = {
        'oauth_consumer_key': CONSUMER_KEY,
        'oauth_token': access_token.key,
        'oauth_signature_method': 'HMAC-SHA1',
        'oauth_timestamp': str(int(time.time())),
        'oauth_nonce': _generate_nonce(),
        'oauth_version': '1.0',
        'track': TWITTER_HANDLE
    }

    oauth_request = oauth.Request.from_token_and_callback(access_token,
                    http_url=stream_url, 
                    parameters=parameters)
    signature_method = oauth.SignatureMethod_HMAC_SHA1()
    signature = signature_method.sign(oauth_request, consumer, access_token)

    parameters['oauth_signature'] = signature

    data = urllib.urlencode(parameters)

    req = urllib2.urlopen("%s?%s" % (stream_url, data))
    buffer = ''

    # We're using urllib2 to avoid external dependencies
    # even though pyCurl actually handles the callbacks
    # much more gracefully than this clumsy method.
    # We read a byte at a time until we find a newline
    # which indicates the end of a chunk.

    while True:

        chunk = req.read(1)
        if not chunk:
            yield buffer
            break

        chunk = unicode(chunk)
        buffer += chunk

        tweets = buffer.split("\n", 1)
        if len(tweets) > 1:
            if tweets[0] != '\r':
                yield tweets[0]
            buffer = tweets[1]

def oauth_req(url, params={}, http_method="GET", consumer_key=CONSUMER_KEY, 
              consumer_secret=CONSUMER_SECRET, access_token=ACCESS_TOKEN, 
              access_secret=ACCESS_SECRET):
    consumer = oauth.Consumer(key=consumer_key, secret=consumer_secret)
    token = oauth.Token(key=access_token, secret=access_secret)
    client = oauth.Client(consumer, token=token)
    
    body=urllib.urlencode(params)
    
    request = client.request(url, method=http_method, body=body)
    #this is a tuple of a response header and the response we care about
    return request

@contextmanager
def follower_cursor():

    try:
        conn = sqlite3.connect(DATABASE)
        cur = conn.cursor()
        yield cur
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
