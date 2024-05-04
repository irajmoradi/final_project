#!/bin/sh

files=$(find data/*)

for file in $files; do
python3 load_tweets_batch.py --db  'postgresql://hello_flask:hello_flask@localhost:1471/hello_flask_dev' --input $file
done
