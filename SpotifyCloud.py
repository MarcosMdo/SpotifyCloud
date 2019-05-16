import sys
import os
import spotipy
import spotipy.util as util
import urllib.request
import time
import requests
from bs4 import BeautifulSoup
import re
from wordcloud import WordCloud, ImageColorGenerator
import numpy as np
from PIL import Image
from os import path
import random
from config import spotifyconfig, geniusconfig
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import argparse

FILE = os.path.dirname(__file__)
STOPWORDS = set(map(str.strip, open(os.path.join(FILE, 'stopwords')).readlines()))

class SpotifyCloud():
    
    def __init__(self, number_songs=25, time_range='long_term', offset=0,
        lyric=True, height=1792, width=828, max_words=200, mask=None,
        max_font_size=350):

        self.number_songs = number_songs
        self.time_range = time_range
        self.offset = offset
        self.lyric = lyric
        self.width = width
        self.height = height
        self.max_words = max_words
        self.mask = mask
        self.max_font_size = max_font_size
        self.mask = mask

    def scrap_song_url(self, url):
        print("Scrapping song")
        page = requests.get(url)
        html = BeautifulSoup(page.text, 'html.parser')
        lyrics = html.find('div', class_='lyrics').get_text()
        lyrics = self.cleanLyrics(lyrics.split())
        return lyrics

    def request_song_info(self, song_title, artist_name):
        search_url = geniusconfig['BASE_URL'] + '/search'
        headers = {'Authorization': 'Bearer ' + geniusconfig['GENIUS_SECRET']}
        data = {'q': song_title + ' ' + artist_name}
        response = requests.get(search_url, data=data, headers=headers)
        return response

    def grey_color_func(self, word, font_size, position, orientation, random_state=None, **kwargs):
        return "hsl(0, 0%%, %d%%)" % random.randint(60, 100)

    def createWordCloud(self, textFile):
        d = path.dirname(__file__) if "__file__" in locals() else os.getcwd()
        jamiexx = np.array(Image.open(path.join(d, "incolorphone.png")))
        spotify_mask = None

        if self.mask is None:
            spotify_mask = None
        else:
            spotify_mask = np.array(Image.open(path.join(d, self.mask)))
        
        text = open(path.join(d, textFile)).read()
        my_stopwords = set(STOPWORDS)

        wc = WordCloud(max_words=self.max_words, mask=jamiexx, stopwords=my_stopwords, margin=10,
            random_state=1, collocations=True, width=self.width, height=self.height,
            max_font_size=self.max_font_size).generate(text)

        # create coloring from image
        image_colors = ImageColorGenerator(jamiexx)

        default_colors = wc.to_array()

        # recolor wordcloud and show
        # we could also give color_func=image_colors directly in the constructor
        plt.imshow(wc.recolor(color_func=image_colors), interpolation="bilinear")
        # plt.title("Default colors")
        # plt.imshow(image_colors, interpolation="bilinear")
        # plt.axis("off")
        plt.show()
        wc.to_file("cloud.png")

    def cleanLyrics(self, lyrics):
        unwanted = [False] * len(lyrics)
        final = []

        for i in lyrics:
            if i[0] == '[':
                unwanted[lyrics.index(i)] = True

        final = [i for (i, n) in zip(lyrics, unwanted) if n is False]
        return ' '.join(final)


def main():
    sc = SpotifyCloud()

    # Spotify Token. USER specifies who is being asked for authorization,
    # å so will need to be a passed in value that is stored once the user is validated.    
    token = util.prompt_for_user_token(spotifyconfig['USER'], spotifyconfig['SCOPE'],
        client_id=spotifyconfig['CLIENT_ID'], client_secret=spotifyconfig['CLIENT_SECRET'],
        redirect_uri=spotifyconfig['REDIRECT_URI'])
    
    if token:

        sp = spotipy.Spotify(auth=token)
    
        tracks = sp.current_user_top_tracks(limit=sc.number_songs, offset=sc.offset, time_range=sc.time_range)['items']
        
        all_lyrics = []
        all_artists = []

        for t in tracks:

            artist_name = t['album']['artists'][0]['name']
            track_name = t['name']
            
            response = sc.request_song_info(track_name, artist_name)
            json = response.json()
            remote_song_info = None

            # Check to see if Genius can find a song with matching artist name and track name.
            for hit in json['response']['hits']: 
                if artist_name.lower() in hit['result']['primary_artist']['name'].lower():
                    remote_song_info = hit
                    break
            
            if sc.lyric:
                # if song info found, collect data.
                if remote_song_info:
                        song_url = remote_song_info['result']['url']
                        lyrics = sc.scrap_song_url(song_url)
                        all_lyrics.append(lyrics)
            else:
                all_artists.append(artist_name)
    
        temp_list = []
        if sc.lyric:
            for i in all_lyrics:
                temp_list.append(''.join(i))
            with open("Lyrics.txt", "w") as text_file:
                text_file.write(' '.join(temp_list))
            sc.createWordCloud("Lyrics.txt")
        else:
            for i in all_artists:
                temp_list.append(''.join(i))
            with open("Artists.txt", "w") as artist_file:
                artist_file.write(' '.join(temp_list))
            sc.createWordCloud("Artists.txt")

if __name__ == "__main__":
    main()