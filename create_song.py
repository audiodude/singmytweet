import re
import tempfile
import time
import subprocess

import curses
from curses.ascii import isdigit
import nltk
from nltk.corpus import cmudict

from beatmaps import BEATMAPS

cmu = cmudict.dict()
BREAK = re.compile('[a-zA-Z@#]+')
XML_HEADER = '''<?xml version="1.0"?>
<!DOCTYPE SINGING PUBLIC "-//SINGING//DTD SINGING mark up//EN" 
      "Singing.v0_1.dtd"
[]>
<SINGING>
'''
XML_FOOTER = '</SINGING>\n'

def nsyl(word):
    pronounce = cmu.get(word.lower())
    if pronounce:
        pronounce = pronounce[0]
        return len(list(y for y in pronounce if isdigit(y[-1])))
    else:
        return 3

def clean_tweet(text):
    return text.replace('@SingThatTweet', '')

def text_to_song_file(tweet_text, tweet_id=None):
    if tweet_id is None:
        tweet_id = time.time()

    tweet_text = clean_tweet(tweet_text)

    words = BREAK.findall(tweet_text)
    print words
    words_syls = [(word, nsyl(word)) for word in words if word]

    # TODO randomize this, or decide on a beatmap based on the phrasing (would be nice)
    beatmap = BEATMAPS[0]

    with tempfile.NamedTemporaryFile() as xml_file:
        xml_file.write(XML_HEADER)
        bm_iter = iter(beatmap)
        for word, syl in words_syls:
            durs = []
            notes = []
            for _ in range(syl):
                next_bm = bm_iter.next()
                if next_bm is None:
                    # TODO handle the case where we are out of notes
                    break
                durs.append(next_bm[0])
                notes.append(next_bm[1])

            cleaned_word = word.replace('@', '').replace('#', '')
            xml_file.write('<DURATION BEATS="%s"><PITCH NOTE="%s">%s</PITCH></DURATION>\n' %
                           (','.join([str(x) for x in durs]), ','.join(notes), cleaned_word))
        xml_file.write(XML_FOOTER)
        xml_file.flush()

        with open(xml_file.name) as f:
            print f.read()

        outfile_name = '/tmp/%s.wav' % tweet_id
        subprocess.call(['/home/tweetsong/festival/bin/text2wave', '-mode', 'singing', xml_file.name, '-o', outfile_name])

    return outfile_name
