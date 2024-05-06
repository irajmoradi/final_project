#!/bin/sh

#files=$(find data/*)
files='/data/tweets/geoTwitter21-04-02.zip'
#/data/tweets/geoTwitter21-04-02.zip
#/data/tweets/geoTwitter21-04-03.zip
#/data/tweets/geoTwitter21-04-04.zip
#/data/tweets/geoTwitter21-04-05.zip
#/data/tweets/geoTwitter21-04-06.zip
#/data/tweets/geoTwitter21-04-07.zip
#/data/tweets/geoTwitter21-04-08.zip
#/data/tweets/geoTwitter21-04-09.zip
#/data/tweets/geoTwitter21-04-10.zip'
for file in $files; do
python3 load_tweets_batch.py --db  'postgresql://hello_flask:hello_flask@localhost:1471/hello_flask_dev' --input $file
done
