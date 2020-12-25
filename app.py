import requests
from database import Database
from flask import Flask, render_template, session, redirect, request, url_for, g
from user import User

from twitter_utils import get_request_token, get_oauth_verifier_url, get_access_token

app = Flask(__name__)
app.secret_key = '1234'

Database.initialize(user='postgres', password='se4Mn&Lj',
                    database='learning',host='localhost')

@app.before_request
def load_user():
    if 'screen_name' in session:
        g.user  = User.load_from_db_by_screen_name(session['screen_name'])

@app.route('/')
def homepage():
    return render_template('home.html')

@app.route('/login/twitter')
def twitter_login():
    if 'screen_name' in session:
        return redirect(url_for('profile'))
    else:
        request_token = get_request_token()
        session['request_token'] = request_token
        return redirect(get_oauth_verifier_url(request_token))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('homepage'))

@app.route('/auth/twitter')
def twitter_auth():
    oauth_verifier = request.args.get('oauth_verifier')
    access_token = get_access_token(session['request_token'],oauth_verifier)
    user = User.load_from_db_by_screen_name(access_token['screen_name'])
    if not user:
        user = User(access_token['screen_name'],access_token['oauth_token'],access_token['oauth_token_secret'],None)
        user.save_to_db()
    session['screen_name'] = user.screen_name
    return redirect(url_for('profile'))

@app.route('/profile')
def profile():
    return render_template('profile.html', user=g.user)

@app.route('/search')
def search():
    verb = 'GET'
    q = request.args.get('q')
    ##url = 'https://api.twitter.com/1.1/search/tweets.json?q=computers+filter:images'
    url = 'https://api.twitter.com/1.1/search/tweets.json?q=' + q

    tweets = g.user.twitter_request(url,verb)
    tweet_texts = [{'label':'neutral','tweet':tweet['text']} for tweet in tweets['statuses']]
    for tweet in tweet_texts:
        r = requests.post('http://text-processing.com/api/sentiment/',data={'text':tweet['tweet']})
        json_response = r.json()
        label = json_response['label']
        tweet['label'] = label
        print(tweet)
    ##if tweets:
     ##   for s in tweets['statuses']:
      ##      print(s['text'])
    return render_template('mysearch.html',myresult=tweet_texts)

app.run(port=4995,debug=True)

