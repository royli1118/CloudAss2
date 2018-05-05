#!/usr/bin/env python3

import logging
import pika
import json
import tweepy
import os
import time
from tweepy import OAuthHandler

#logs for debegging
logging.basicConfig(level=logging.DEBUG)

# RabbitMQ server setup
ruser = os.environ['RABBITMQ_USER']
rpass = os.environ['RABBITMQ_PASS']
credentials = pika.PlainCredentials(ruser, rpass)
parameters = pika.ConnectionParameters(host='rabbitmq', credentials=credentials)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()
NEW_TWEET_QUEUE = 'new_tweets'
channel.queue_declare(queue=NEW_TWEET_QUEUE)

logging.info(os.environ)


#Variables that contains the user credentials to access Twitter API
access_token = os.environ['ACCESS_TOKEN']
access_token_secret = os.environ['ACCESS_TOKEN_SECRET']
consumer_key = os.environ['CONSUMER_KEY']
consumer_secret = os.environ['CONSUMER_SECRET']

auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

api = tweepy.API(auth, parser=tweepy.parsers.JSONParser())
next_search_id = 0

while True:
    status = api.search(geocode = os.environ['SEARCH_RANGE'], since_id = next_search_id, rpp = 100)

    for item in status.get('statuses'):

        itemStr = json.dumps(item)
        channel.basic_publish(
                exchange='',
                routing_key=NEW_TWEET_QUEUE,
                body=itemStr)

    # get the next search id in "search_metadata"
    try:
        next_results =status.get("search_metadata").get("next_results")
        next_search_id = next_results.replace('&','=').split('=')[1]  #replace '&' with '=' and split string by '='
    except:
        # no more next page
        print('Break at: ',status.get("search_metadata"))
        continue
    time.sleep(5.05)

# Disconnect RabbitMQ
connection.close()