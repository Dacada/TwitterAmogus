#!/usr/bin/env python3

import datetime
import time
import logging
import os
import subprocess
import twython
import sd_notify


MAX_INTERNET_UP_ATTEMPTS = 5


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


def is_internet_up():
    return subprocess.call(['ping', '-c', '1', '8.8.8.8']) == 0


def main(app_key, app_secret, oauth_token, oauth_token_secret):
    notify = sd_notify.Notifier()
    if not notify.enabled():
        raise Exception("Watchdog not enabled! "
                        "Is this running through systemd?")

    logger = logging.getLogger('amogus')
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    logger.addHandler(handler)

    logger.info("Checking for internet connection...")
    attempts = 0
    while not is_internet_up():
        attempts += 1
        if attempts >= MAX_INTERNET_UP_ATTEMPTS:
            raise Exception("Could not get internet access in {} attempts."
                            .format(MAX_INTERNET_UP_ATTEMPTS))

        logger.error("Internet is not up!! Sleeping 5 minutes before retry...")
        notify._send("EXTEND_TIMEOUT_USEC={}\n".format(5*60*1000000))
        time.sleep(5*60)

    logger.info("Bot starting.")
    twitter = twython.Twython(app_key, app_secret,
                              oauth_token, oauth_token_secret)
    notify.ready()

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
                    except twython.exceptions.TwythonAuthError as e:
                        if 'You have been blocked' in e.msg:
                            logger.warning("Tweet cannot be retweeted "
                                           "because user has us blocked.")
                            continue
                        else:
                            raise
                    notify.notify()
                    time.sleep(60)
        except twython.exceptions.TwythonRateLimitError as e:
            wait_for_rate_limit(logger, int(e.retry_after))


if __name__ == '__main__':
    main(os.environ['APP_KEY'], os.environ['APP_SECRET'],
         os.environ['OAUTH_TOKEN'], os.environ['OAUTH_TOKEN_SECRET'])
