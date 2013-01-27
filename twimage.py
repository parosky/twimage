#!/usr/bin/env python
# -*- coding: utf-8 -*-

# TODO: refactoring

import urllib2
import BeautifulSoup
import settings
import tweepy
import datetime
import codecs
import sys
import os
import json
import datetime
import glob
import wordpress_xmlrpc

self_path = os.path.dirname(os.path.abspath( __file__ ))
save_path = self_path + '/data'

def get_yahoo_trends():
    """ get trend words from Yahoo Realtime Search """
    
    # set user-agent
    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.19 (KHTML, like Gecko) Ubuntu/11.10 Chromium/18.0.1025.168 Chrome/18.0.1025.168 Safari/535.19')]
    urllib2.install_opener(opener)
    
    # get trend words
    html = urllib2.urlopen('http://search.yahoo.co.jp/realtime').read()
    soup = BeautifulSoup.BeautifulSoup(html)
    soup = soup(attrs={'class': 'dtl cf'})[0]('a')
    return [s.text for s in soup]

def get_twitter_images(keyword, min_images=0):
    key = settings.apikey_twitter
    auth = tweepy.OAuthHandler(key['consumer_key'], key['consumer_secret'])
    auth.set_access_token(key['access_token'], key['access_token_secret'])
    api = tweepy.API(auth)
    
    keyword_pic = 'pic.twitter.com'
    return [status for status in api.search('%s %s' % (keyword, keyword_pic), lang='ja', rpp=100)]

def save_status(keyword, status):
    embed_tweet = '<blockquote class="twitter-tweet"><p>%s</p><a href="%s" data-datetime=""></a></blockquote>\n'
    date = datetime.datetime.now().strftime('%Y%m%d')
    f = codecs.open('%s/%s_%s.html' % (save_path, date, keyword), 'w', 'utf-8')
    tweet_url = []
    for s in status:
        if 'RT' in s.text:
            continue
        text = s.text.replace('\n', '')
        url = u'http://twitter.com/%s/status/%s' % (s.from_user, s.id)
        f.write(embed_tweet % (text, url))
        tweet_url.append(url)
    f.close()

def post_to_wordpress():
    today = datetime.datetime.now().strftime('%Y%m%d')
    yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y%m%d')

    title_template = codecs.open('%s/title.txt' % self_path, 'r', 'utf-8').read()
    if not glob.glob('%s/%s_post.html' % (save_path, yesterday)):
        titles = []
        for filename in glob.glob('%s/%s*' % (save_path, yesterday)):
            filename = filename.decode('utf-8')
            lines = open(filename).readlines()
            if not lines:
                continue
            title = title_template % filename.split('/')[-1][(8+1):(-5)]
            content1 = lines[0]
            content2 = ''.join(lines[1:])
            wpurl = settings.wordpress['url']
            client = wordpress_xmlrpc.Client(wpurl, settings.wordpress['user'], settings.wordpress['password'])
            post = wordpress_xmlrpc.methods.posts.WordPressPost()
            post.title = title
            post.description = content1
            post.extended_text = content2
            client.call(wordpress_xmlrpc.methods.posts.NewPost(post,True))
            titles.append(title)
        f = codecs.open('%s/%s_post.html' % (save_path, yesterday), 'w', 'utf-8')
        f.writelines(titles)
        f.close()
        
if __name__ == '__main__':
    if len(sys.argv) == 1:
        words = get_yahoo_trends()
        for word in words:
            status = get_twitter_images(word)
            save_status(word, status)
    else:
        word = sys.argv[1]
        status = get_twitter_images(word)
        save_status(word, status)
    post_to_wordpress()
