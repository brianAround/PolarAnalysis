import configparser

from twython import Twython
from twython.exceptions import TwythonError
from twython.exceptions import TwythonRateLimitError

config_file = 'Oracle.ini'

def configure_client(use_config_path=None):
    if use_config_path is None:
        use_config_path = config_file
    cfg = configparser.ConfigParser()
    cfg.read(use_config_path)
    twit_config = cfg['twitter']
    app_key = twit_config['app_key']
    app_secret = twit_config['app_secret']
    acct_key = twit_config['acct_key']
    acct_secret = twit_config['acct_secret']

    twitter = Twython(app_key, app_secret, acct_key, acct_secret)
    return twitter


if __name__ == "__main__":
    twitter = configure_client()
    trends = twitter.get_available_trends()
