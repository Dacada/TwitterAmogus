#!/usr/bin/env python3

import datetime
import time
import logging
import os
import twython


def main(app_key, app_secret, oauth_token, oauth_token_secret):
    logger = logging.getLogger('amogus')
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    logger.addHandler(handler)

    logger.info("Bot starting.")
    twitter = twython.Twython(app_key, app_secret,
                              oauth_token, oauth_token_secret)

    try:
        results = twitter.cursor(
            twitter.search,
            q='among us', tweet_mode='extended'
        )

        for result in results:
            if 'full_text' in result.keys() and\
               'among' in result['full_text'] and\
               'us' in result['full_text']:
                try:
                    logger.info("Retweeting tweet " + result['id_str'])
                    twitter.retweet(id=result['id'])
                    sleep(60)
                except twython.exceptions.TwythonError as e:
                    if 'You have already retweeted this Tweet' in e.msg:
                        logger.warning("Tweet had already been retweeted.")
                        continue
                    else:
                        raise
    except twython.exceptions.TwythonRateLimitError as e:
        goal = datetime.datetime.fromtimestamp(int(e.retry_after))
        now = datetime.datetime.now()
        logger.warning("Hit rate limit.")
        while goal > now:
            t = (goal-now).seconds
            logger.info("Sleeping for: " + str(t))
            time.sleep(t)
            now = datetime.datetime.now()


if __name__ == '__main__':
    main(os.environ['APP_KEY'], os.environ['APP_SECRET'],
         os.environ['OAUTH_TOKEN'], os.environ['OAUTH_TOKEN_SECRET'])
