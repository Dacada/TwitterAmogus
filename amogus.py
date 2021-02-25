#!/usr/bin/env python3

import datetime
import time
import logging
import os
import twython


def wait_for_rate_limit(logger, timestamp):
    goal = datetime.datetime.fromtimestamp(timestamp)
    now = datetime.datetime.now()
    logger.warning("Hit rate limit.")
    while goal > now:
        t = (goal-now).seconds
        if (t <= 0):
            break
        logger.info("Sleeping for: " + str(t))
        time.sleep(t)
        now = datetime.datetime.now()


def main(app_key, app_secret, oauth_token, oauth_token_secret):
    logger = logging.getLogger('amogus')
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    logger.addHandler(handler)

    logger.info("Bot starting.")
    twitter = twython.Twython(app_key, app_secret,
                              oauth_token, oauth_token_secret)

    while True:
        try:
            results = twitter.cursor(
                twitter.search,
                q='among us', tweet_mode='extended'
            )

            for result in results:
                if 'full_text' in result.keys() and\
                   'among' in result['full_text'] and\
                   'us' in result['full_text']:
                    logger.info("Retweeting tweet " + result['id_str'])
                    try:
                        twitter.retweet(id=result['id'])
                    except twython.exceptions.TwythonRateLimitError as e:
                        wait_for_rate_limit(logger, int(e.retry_after))
                    except twython.exceptions.TwythonError as e:
                        if 'You have already retweeted this Tweet' in e.msg:
                            logger.warning("Tweet had already been retweeted.")
                            continue
                        else:
                            raise
                    time.sleep(60)
        except twython.exceptions.TwythonRateLimitError as e:
            wait_for_rate_limit(logger, int(e.retry_after))


if __name__ == '__main__':
    main(os.environ['APP_KEY'], os.environ['APP_SECRET'],
         os.environ['OAUTH_TOKEN'], os.environ['OAUTH_TOKEN_SECRET'])
