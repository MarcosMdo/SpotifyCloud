import sys
import os
import spotipy
import spotipy.util as util
import urllib.request
import time
import requests
from bs4 import BeautifulSoup
import re
from wordcloud import WordCloud
import numpy as np
from PIL import Image
from os import path
import random
from config import spotifyconfig, geniusconfig
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

FILE = os.path.dirname(__file__)
STOPWORDS = set(map(str.strip, open(os.path.join(FILE, 'stopwords')).readlines()))

def scrap_song_url(url):
    print("Scrapping song")
    page = requests.get(url)
    html = BeautifulSoup(page.text, 'html.parser')
    lyrics = html.find('div', class_='lyrics').get_text()
    lyrics = cleanLyrics(lyrics.split())
    return lyrics

def request_song_info(song_title, artist_name):
    search_url = geniusconfig['BASE_URL'] + '/search'
    headers = {'Authorization': 'Bearer ' + geniusconfig['GENIUS_SECRET']}
    data = {'q': song_title + ' ' + artist_name}
    response = requests.get(search_url, data=data, headers=headers)

    return response


def createWordCloud(textFile):
    d = path.dirname(__file__) if "__file__" in locals() else os.getcwd()
    spotify_mask = np.array(Image.open(path.join(d, "masks/spotify-mask-2.png")))
    text = open(path.join(d, textFile)).read()
    my_stopwords = set(STOPWORDS)

    wc = WordCloud(max_words=10000, mask=None, stopwords=my_stopwords, margin=10,
           random_state=1, collocations=True).generate(text)

    default_colors = wc.to_array()
    wc.to_file("cloud.png")
    plt.title("Default colors")
    plt.imshow(default_colors, interpolation="bilinear")
    plt.axis("off")
    plt.show()

def cleanLyrics(lyrics):
    unwanted = [False] * len(lyrics)
    final = []

    for i in lyrics:
        if i[0] == '[':
            unwanted[lyrics.index(i)] = True

    final = [i for (i, n) in zip(lyrics, unwanted) if n is False]
    return ' '.join(final)


def main():

    lyricCloud = True
    artistCloud = True
    # Spotify Token. USER specifies who is being asked for authorization, so will need to be a passed in value that is stored once the user is validated.    
    token = util.prompt_for_user_token(spotifyconfig['USER'], spotifyconfig['SCOPE'], client_id=spotifyconfig['CLIENT_ID'],
         client_secret=spotifyconfig['CLIENT_SECRET'], redirect_uri=spotifyconfig['REDIRECT_URI'])
    
    if token:
        
        sp = spotipy.Spotify(auth=token)
        
        time_range = 'long_term' # mid_term, short_term, long_term
        num_songs = 1 # number of songs to scrape
        offset = 0 # first index of songs to scrape

        tracks = sp.current_user_top_tracks(limit=num_songs, offset=offset, time_range=time_range)['items']
        
        all_lyrics = []
        all_artists = []

        for t in tracks:

                artist_name = t['album']['artists'][0]['name']
                track_name = t['name']
                
                response = request_song_info(track_name, artist_name)
                json = response.json()
                remote_song_info = None

                # Check to see if Genius can find a song with matching artist name and track name.
                for hit in json['response']['hits']: 
                    if artist_name.lower() in hit['result']['primary_artist']['name'].lower():
                        remote_song_info = hit
                        break
                
                if lyricCloud:
                        # if song info found, collect data.
                        
                        if remote_song_info:
                                song_url = remote_song_info['result']['url']
                                lyrics = scrap_song_url(song_url)
                                all_lyrics.append(lyrics)
                if artistCloud:
                        all_artists.append(artist_name)
        
        temp_list = []
        for i in all_lyrics:
            temp_list.append(''.join(i))

        if lyricCloud:
            with open("Lyrics.txt", "w") as text_file:
                text_file.write(' '.join(temp_list))
            createWordCloud("Lyrics.txt")
        
        if artistCloud:
            with open("Artists.txt", "w") as artist_file:
                artist_file.write(' '.join(all_artists))
            createWordCloud("Artists.txt")

if __name__ == "__main__":
        main()