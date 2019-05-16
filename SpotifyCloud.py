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
import PIL
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
MAX_FONT_SIZE_DESKTOP = 400
MAX_WORDS_DESKTOP = 500
MAX_FONT_SIZE_MOBILE = 400
MAX_WORDS_MOBILE = 300

class SpotifyCloud():
    
    def __init__(self, number_songs=50, time_range='short_term', offset=0,
        lyric=True, height=100, width=1000, max_words=200,
        max_font_size=350, theme='random', viewport='custom', min_font_size=4):

        self.number_songs = number_songs
        self.time_range = time_range
        self.offset = offset
        self.lyric = lyric
        self.theme = theme
        self.viewport = viewport
        
        if not lyric:
            self.number_songs = 50

        if self.viewport == 'desktop':
            self.width = 1920
            self.height = 1080
            self.max_font_size = MAX_FONT_SIZE_DESKTOP
            self.max_words = MAX_WORDS_DESKTOP
        elif self.viewport == 'mobile':
            self.width = 720
            self.height = 1280
            self.max_font_size = MAX_FONT_SIZE_MOBILE
            self.max_words = MAX_WORDS_MOBILE
        else:
            self.width = width
            self.height = height
            self.max_font_size = max_font_size
            self.max_words = max_words
            self.min_font_size = min_font_size


    def scrap_song_url(self, url):
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

    def resizeImage(self):
        path_to_image = 'themes/' + self.theme + '-desktop.png'
        img = Image.open(path_to_image)
        img = img.resize((self.width, self.height), PIL.Image.ANTIALIAS)
        new_file = 'themes/' + self.theme + '-custom.png'
        img.save(new_file)
        return new_file
        

    def createWordCloud(self, textFile):
        d = path.dirname(__file__) if "__file__" in locals() else os.getcwd()
        
        text = open(path.join(d, textFile)).read()
        my_stopwords = set(STOPWORDS)

        wc = WordCloud(max_words=self.max_words, stopwords=my_stopwords, margin=10,
            random_state=1, collocations=True, width=self.width, height=self.height,
            max_font_size=self.max_font_size).generate(text)
        
        if self.viewport == 'custom':
            if self.theme != 'random':
                path_to_theme = self.resizeImage()
                theme_mask = np.array(Image.open(path.join(d, path_to_theme)))
                image_colors = ImageColorGenerator(theme_mask)
                plt.imshow(wc.recolor(color_func=image_colors), interpolation="bilinear")
                wc.to_file("cloud.png")
                os.remove(path_to_theme)
            else:
                default_colors = wc.to_array()
                plt.title("Default colors")
                plt.imshow(default_colors, interpolation="bilinear")
                wc.to_file("cloud.png")
        elif self.theme == 'random':
            default_colors = wc.to_array()
            plt.title("Default colors")
            plt.imshow(default_colors, interpolation="bilinear")
            wc.to_file("cloud.png")
        else:
            path_to_theme = 'themes/' + self.theme + '-' + self.viewport + '.png'
            theme_mask = np.array(Image.open(path.join(d, path_to_theme)))
            image_colors = ImageColorGenerator(theme_mask)
            plt.imshow(wc.recolor(color_func=image_colors), interpolation="bilinear")
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