# This is the original PolarAnalysis file from the Scrambled Oracle project.

# PolarAnalysis, at this point, was an attempt to build a simple Sentiment Analysis

import operator
import string
from collections import Counter
from collections import namedtuple
import codecs
import configparser
import os.path
import time
from twython import Twython
from twython.exceptions import TwythonError
from twython.exceptions import TwythonRateLimitError

# only one part of the Oracle module was used. I'll just rebuild that piece.
# from Oracle import Oracle
import TextIOUtility



hash_tag = 'Hillary Clinton'
# select_date = '11/8/2017'
sample_size = 3000

# Problems to solve
# download a set of available tweets using a criteria
config_file = 'Oracle.ini'
TwitterOptions = namedtuple('TwitterOptions', 'app_key,app_secret,acct_key,acct_secret')

TweetInfo = namedtuple('TweetInfo', 'account,id,datetime,text')

status_by_id = {}
count_by_original_id = Counter()


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


def get_status(id, twitter:Twython=None):
    if int(id) in status_by_id:
        return status_by_id[int(id)]
    if twitter is None:
        twitter = configure_client()
    try:
        status = twitter.show_status(id=id, tweet_mode='extended')
        rate_limit = tw.get_lastfunction_header('x-rate-limit-limit')
        remaining_limit = tw.get_lastfunction_header('x-rate-limit-remaining')
        reset_raw = tw.get_lastfunction_header('x-rate-limit-reset')
        if remaining_limit is not None and int(remaining_limit) < 2:
            if reset_raw is None:
                reset_raw = time.time() + 900
            else:
                reset_raw = int(reset_raw)
            reset_struct = time.localtime(reset_raw)
            reset_time = time.asctime(reset_struct)
            print(remaining_limit, '/', rate_limit)
            print('resets:', reset_time)
            diff = 60 * (reset_struct.tm_hour - time.localtime().tm_hour) + (reset_struct.tm_min - time.localtime().tm_min) + 2
            max(diff, 2)
            while diff > 0:
                print('Wait:', diff, 'minutes')
                time.sleep(60)
                diff -= 1
        if status['id'] not in status_by_id:
            status_by_id[status['id']] = status
        while 'retweeted_status' in status:
            rstat = status['retweeted_status']
            status = get_status(rstat['id'], twitter)
    except TwythonRateLimitError as rlex:
        if rlex.retry_after is None:
            retry_after = time.time() + 900
        else:
            retry_after = int(rlex.retry_after)
        print('Rate limit exceeded, retry after', time.localtime(rlex.retry_after))

    return status


# next we add the ability to narrow to a date or other thing like it.
def search_term(search_text:str, count=100, date_start=None, twitter=None):
    result = []
    if twitter is None:
        twitter = configure_client()
    srch = twitter.search(q=search_text, count=count)  #, tweet_mode='extended'
    rate_limit = twitter.get_lastfunction_header('x-rate-limit-limit')
    remaining_limit = twitter.get_lastfunction_header('x-rate-limit-remaining')
    print(remaining_limit, '/', rate_limit)
    tweets = srch['statuses']
    min_id = min([t['id'] for t in tweets])
    result = tweets[:]
    while len(tweets) >= min([100, count]) and len(result) < count:
        srch = twitter.search(q=search_text, count=count, max_id=min_id-1)
        rate_limit = twitter.get_lastfunction_header('x-rate-limit-limit')
        remaining_limit = twitter.get_lastfunction_header('x-rate-limit-remaining')
        tweets = srch['statuses']
        min_id = min(min_id, min([t['id'] for t in tweets]))
        result.extend(tweets)
        print(remaining_limit, '/', rate_limit)
        if remaining_limit is not None and int(remaining_limit) < 2:
            diff = 15
            while diff > 0:
                print('Wait:', diff, 'minutes')
                time.sleep(60)
                diff -= 1
    return result

tw = configure_client()
tweets = search_term(hash_tag, sample_size, tw)
print('Processing', len(tweets), 'downloaded tweets')
results = []
for twt in tweets:
    try:
        if 'retweeted_status' in twt or twt['truncated']:
            if 'retweeted_status' in twt:
                status = get_status(twt['retweeted_status']['id'], tw)
            else:
                status = get_status(twt['id'], tw)
            text_key = 'full_text'
        else:
            status = twt
            if status['id'] not in status_by_id:
                status_by_id[status['id']] = status
            text_key = 'text'
        results.append(TweetInfo(status['user']['screen_name'], status['id_str'], status['created_at'],
                                 status[text_key].replace('\n', ' \ ')))
        count_by_original_id[status['id']] += 1
    except TwythonError as twex:
        print('Error processing status', twt['id'], twt)
        print(twex)
    # twt['from_user']
    #print(twt)
    # print(results[-1])
    last_twt = status

print(len(status_by_id), 'distinct original ids')
for tw_id in [item[0] for item in sorted(count_by_original_id.items(), key=(operator.itemgetter(1)))]:
    if count_by_original_id[tw_id] > 9:
        print(count_by_original_id[tw_id], status_by_id[tw_id])
# store tweets in an easily retrievable data format



# load the positive word list and the negative word list
pos_path = os.path.join(os.path.join('data', 'model'), 'positive.txt')
neg_path = os.path.join(os.path.join('data', 'model'), 'negative.txt')
pos_terms = TextIOUtility.load_dictionary(pos_path)
neg_terms = TextIOUtility.load_dictionary(neg_path)
pos_path = os.path.join(os.path.join('data','extra'), 'positive.txt')
neg_path = os.path.join(os.path.join('data','extra'), 'negative.txt')
pos_terms = TextIOUtility.load_dictionary(pos_path, False, pos_terms)
neg_terms = TextIOUtility.load_dictionary(neg_path, False, neg_terms)

# score each stored tweet and output the results
def score_text(text, positive_terms, negative_terms, unknown:Counter=None):
    result = 0
    words = [w.lower().strip(string.punctuation) for w in text.split()]
    for w in words:
        word = w[1:] if w.startswith('#') and len(w) > 1 else w
        if word in pos_terms:
            result += 1
        elif word in neg_terms:
            result -= 1
        elif unknown is not None:
            unknown[word] += 1

    return result

pos_results = []
other_results = []
neg_results = []

other_terms = Counter()
other_neg = Counter()
other_positive = Counter()

for t in results:
    current_other = Counter()
    score = score_text(t.text, pos_terms, neg_terms, current_other)
    for term in current_other:
        other_terms[term] += current_other[term]
        if score > 0:
            other_positive[term] += current_other[term]
        elif score < 0:
            other_neg[term] += current_other[term]
    element = (score, t, )
    if score > 0:
        pos_results.append(element)
    elif score < 0:
        neg_results.append(element)
    else:
        other_results.append(element)

print('Negative sent.:', len(neg_results))
for t in neg_results:
    print(t[0], t[1])
print('Other sent.:', len(other_results))
for t in other_results:
    print(t[0], t[1])
print('Positive sent.:', len(pos_results))
for t in pos_results:
    print(t[0], t[1])


filepath = 'Unrec ' + hash_tag.replace('#','Hash-') + '.txt'
output_terms  = {}
for term in other_terms:
    output_terms[term] = (other_terms[term], other_positive[term], other_neg[term], )
print('Storing',len(other_terms),'Unrecognized terms as', filepath)
TextIOUtility.dictionary_dump(filepath, output_terms)

print('FULL RESULTS')
print('Positive:', len(pos_results))
print('Neutral:', len(other_results))
print('Negative:', len(neg_results))

