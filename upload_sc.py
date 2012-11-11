import soundcloud
from secrets import SC_CLIENT_ID, SC_CLIENT_SECRET, SC_ACCESS_TOKEN
from utils import oauth_req

code = '1b2ce8bafaac48b2e2b21a6ab0681e49'

def upload(filename, title):
    # create client object with app credentials

    oauth_req

    client = soundcloud.Client(access_token=SC_ACCESS_TOKEN)

    track = client.post('/tracks', track={
        'title': title,
        'sharing': 'public',
        'asset_data': open(filename, 'rb')
    })
    return track.permalink_url

def register():
    client = soundcloud.Client(client_id=SC_CLIENT_ID,
                               client_secret=SC_CLIENT_SECRET, 
                               redirect_uri='http://singmytweet.info:8000/')

    #print client.authorize_url()
    #raw_input()
    access_token = client.exchange_token(code)
    print access_token.fields()
    print access_token.keys()

def test():
    #register()
    upload("/tmp/test.wav", 'test')

    client = soundcloud.Client(client_id=SC_CLIENT_ID,
                               client_secret=SC_CLIENT_SECRET, 
                               access_token=SC_ACCESS_TOKEN)

#print test()