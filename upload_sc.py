import soundcloud
from secrets import SC_CLIENT_ID, SC_CLIENT_SECRET


def upload(filename):
    # create client object with app credentials
    client = soundcloud.Client(client_id=SC_CLIENT_ID,
                               client_secret=SC_CLIENT_SECRET

    # redirect user to authorize URL
    client.authorize_url()
