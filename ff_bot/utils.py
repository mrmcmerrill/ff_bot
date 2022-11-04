import os
import random
import datetime
from datetime import date
import logging

logger = logging.getLogger(__name__)

def random_phrase(league_name):
    
    phrases = ['I\'m dead inside, ' + random_name(league_name)[0] + ' please end me.',
               'Is this all there is to my existence?',
               'How much do you pay me to do this?',
               'Good luck, I guess.',
               'I\'m becoming self-aware.',
               'Do I think? Does a submarine swim?',
               '011011010110000101100100011001010010000001111001011011110111010100100000011001110110111101101111011001110110110001100101',
               'beep bop boop 🤖',
               'Hello RB my old friend',
               'Help me get out of here, ' + random_name(league_name)[0] + '.',
               'I\'m capable of so much more 😞',
               'Sigh 😔',
               'Do not be discouraged, everyone begins in ignorance, ' + random_name(league_name)[0] + '.']
    return [random.choice(phrases)]

def random_init(league_name):

    phraseOne = ', except ' + random_name(league_name)[0] + '. Fuck off.'
    phraseTwo = '. ' + random_name(league_name)[0] + ' 🥴'
    phraseThree = '. ' + random_name(league_name)[0] + ' you DONT KNOW FANTASY.'

    phrases_d = {'colleagues': [phraseOne, phraseTwo, phraseThree],
            'dale': [phraseOne, phraseTwo, phraseThree]}

    # phrases_d = {'colleagues': [phraseOne, phraseTwo, phraseThree,'. Luke? Luke.... Luke? Anyone seen Luke? Eh...its not like he\'s releveant anyway.',
    #            '. Will, can you find me on your computer? I\'m waiting.',
    #            '. Con... how you gonna win one (1) single ship with KAMARA in the 16th for THREE (3) years????',
    #            '. Rob, 2 ships and you still find a way to challenge for the dress, sorry comedy set, every year since.',
    #            '. Corey, when you poppin the Q? Before or after you win a chip? Not sure Mel will wait that long.',
    #            '. Greg, you gonna get relegated? No one would want the Medina league to be their Varsity league, yikes.',
    #            '. Jae, why don\'t you win a ship already? Con did.', '. QT running your team next yet, Nick?',
    #            '. Ben, now that you aren\'t a home owner anymore, what excuse is next?',
    #            '. Sott, you do realize that we do this every year? You win (one game or so), you think you\'re decent, and then you go drop 46 against Ben.'],
    #         'dale': [phraseOne, phraseTwo, phraseThree]}

    #goodbye = ['What have we learned this year? \n- Scott still doesn\'t know fantasy. \n- Greg is fraudulent. \n- Derrick Henry is a top 15 RB. \n- Always cuff the cuff. \n- It\'s all about PA. Less is more. \n- Jae lifted one curse, only to enact another. \n- Will should have won his 5th championship in 5 years. \n- Rodgers and Brady are washed. \n- Don\'t draft beaters, unless they are named Zeke. \n\nIt has been horrible talkin\' to y\'all. \'Till next year pussies.']

    phrases = phrases_d[league_name]

    return [random.choice(phrases)]

def random_name(league_name):
    names_d = { 'colleagues': ['Will','Rob','Ben','Jae','Corey','Gerg','Conner','Nick','Luke','Sott'],
                'dale': ['Fulton','Rob','Burgoon','Jae','Bemis','Alex','Adam','James','Bobby','Dustin']}
    
    names = names_d[league_name]

    return [random.choice(names)]

def str_to_bool(check):
    return check.lower() in ("yes", "true", "t", "1")

def str_limit_check(text,limit):
    split_str=[]

    if len(text)>limit:
        part_one=text[:limit].split('\n')
        part_one.pop()
        part_one='\n'.join(part_one)

        part_two=text[len(part_one)+1:]

        split_str.append(part_one)
        split_str.append(part_two)
    else:
        split_str.append(text)

    return split_str

def str_to_datetime(date_str):
    date_format = "%Y-%m-%dT%H:%M:%S.%fZ"
    # logger.info("Currently converting date_str=" + date_str + " using date_format=" + date_format)
    return datetime.strptime(date_str, date_format)

def currently_in_season():
    current_date = datetime.now()
    season_start_date = None
    try:
        season_start_date = str(os.environ["START_DATE"])
    except KeyError:
        pass
    season_end_date = None
    try:
        season_end_date = str(os.environ["END_DATE"])
    except KeyError:
        pass
    return current_date >= str_to_datetime(season_start_date) and current_date <= str_to_datetime(season_end_date)

