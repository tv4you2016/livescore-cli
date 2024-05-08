#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import requests, time, socket, re
from collections import defaultdict
from .urls import base_url, details


def is_connected(server='www.google.com'):
    try:
        host = socket.gethostbyname(server)
        socket.create_connection((host, 80), 2)
        return True
    except:
        return False


def get_tz_offset():
    offset = time.timezone if (time.localtime().tm_isdst == 0) else time.altzone
    return offset / 60 / 60 * -1


def get_livescores_url(name, type):
    tz_offset = get_tz_offset()
    url = details.get(type).get(name).get('url') + f'/?tz={tz_offset}'
    return url


def get_soup(name='bpl', event_type='competition'):
    url = get_livescores_url(name, event_type)
    html = requests.get(url).text
    soup = BeautifulSoup(html, 'html.parser')
    return soup


def get_match_id(url):
    res = 0
    for e in url.split('/'):
        if e.isdigit():
            res = int(e.strip())
    return res


def get_match_details(match_details_url):
    url = base_url + match_details_url
    #print(url)
    html = requests.get(url).text
    soup = BeautifulSoup(html, 'html.parser')
    return soup


'''
    returns a dict of games;
    key: date, value: list of match


    games = {
        'December 30, 2022':
        [
            {
                'match_status': 'FT',
                'home_team': 'Chelsea',
                'away_team': 'Liverpool',
                'home_score': '0',
                'away_score': '0',
            }
        ]
    }
'''

def parse_games(soup):
    
    #sp = soup.find('div', attrs={'data-testid': 'match_rows-root'}).find_all('div', recursive=False)
    matches_container = soup.find('div', {'class': 'db'})
    #print(matches_container)
    matches = matches_container.find_all('div', {'class': 'yf Cf'}, recursive=False)
    #sp = soup.find('div', {'class': 'yf Cf'})
    #print(matches)
    games = defaultdict(list)
    
    
    for i in range(0, len(matches)):
        line = matches[i]
        match = {}
        #date_html = line.find('span', attrs={'data-testid': re.compile('category_header-date.*')})
        #if date_html:
        #    date = date_html.text
        #else:
        match_details_url = line.find('a', href=True).get('href')
        match_details = get_match_details(match_details_url)
             

        if match_details_url and match_details:

            date = ""
            #match_status
            mst = match_details.find('div', {'id': '__livescore'}).find('div',  {'class': 'ae de'}).find('span',  {'class': 'be'}).text
           
            if (mst == 'FT' or mst == 'AP' ): 
                
                match_infos = match_details.find('div', {'id': '__livescore'}).find_all('div',  {'class': 'ec'})
                if (len(match_infos) >= 2):
                    match_info = match_infos[1].find_all('span')
                    if (len(match_info) >= 2):
                        date = match_info[1].text
     



                # penalty shoot-out:
                match_result = match_details.find('div', {'id': '__livescore'}).find_all('div',  {'class': 'ae'})
                if (len(match_result) > 0):
                    # check aggregate score:
                    if (len(match_result) == 2): # AGG
                        match_score = match_result[1].find('div',{'class': 'he'}).find_all('span')
                        if (len(match_score) == 3):
                            #home_score
                            hts = match_score[0].text
                            #away_score
                            ats = match_score[2].text
                        
                        aggScoreImage = ''
                        aggScoreImage = match_result[0].find('span',{'class': 'aggScoreImage'})
                        if aggScoreImage: 
                           ht = match_result[0].find('span',  {'class': 'fe'}).text  + " (AGG)"
                           at = match_result[0].find('span',  {'class': 'ge'}).text
                        else:
                           ht = match_result[0].find('span',  {'class': 'fe'}).text         
                           at = match_result[0].find('span',  {'class': 'ge'}).text + " (AGG)"
                        

                    elif (len(match_result) == 3): # AGG + PEN
                        match_score = match_result[2].find_all('div',{'class': 'he'}) 
                        if (len(match_score) == 3):
                            #home_score
                            hts = match_score[0].text
                            #away_score
                            ats = match_score[2].text
                else:
                    #home_team
                    ht = match_details.find('div', {'id': '__livescore'}).find('div',  {'class': 'ae de'}).find('span',  {'class': 'fe'}).text
                    #away_team
                    at = match_details.find('div', {'id': '__livescore'}).find('div',  {'class': 'ae de'}).find('span',  {'class': 'ge'}).text

                    # not penalty or aggregate               
                    match_result= match_details.find('div', {'id': '__livescore'}).find('div',  {'class': 'ae de'}).find('div',  {'class': 'he'}).find_all('span')
                    if (len(match_result) == 3):
                        #home_score
                        hts = match_result[0].text
                        #away_score
                        ats = match_result[2].text

            elif  mst == 'AET':
                break
            else : # hours 

                match_info = match_details.find('div', {'id': '__livescore'}).find('div',  {'class': 'ec'}).find_all('span')

                if (len(match_info) == 2):
                    date = match_info[1].text

                #home_team
                ht = match_details.find('div', {'id': '__livescore'}).find('div',  {'class': 'ae de'}).find('span',  {'class': 'fe'}).text
                
                #home_score
                hts = ''
                #away_team
                at = match_details.find('div', {'id': '__livescore'}).find('div',  {'class': 'ae de'}).find('span',  {'class': 'ge'}).text
                #away_score
                ats = ''

    
            match = {
                'match_status': mst,
                'home_team': ht,
                'home_score': int(hts) if hts.isdigit() else hts,
                'away_team': at,
                'away_score': int(ats) if ats.isdigit() else ats,
                'match_details_url': base_url + match_details_url
            }

        games[date].append(match) if (date and match) else None

    return games


def get_games(name='bpl', event_type='competition'):
    soup = get_soup(name, event_type)
    games = parse_games(soup)
    return games


'''
    returns a list of rows, which is a list of table elements;

    table = [['LP', '', 'Team Name', 'GP', 'W', 'D', 'L', 'GF', 'GA', 'GD', 'Pts']
    ['1', 'Champions League', 'Arsenal', '19', '16', '2', '1', '45', '16', '29', '50']
    ['2', 'Champions League', 'Manchester City', '20', '14', '3', '3', '53', '20', '33', '45']
    ['3', 'Champions League', 'Newcastle United', '20', '10', '9', '1', '33', '11', '22', '39']
    ...]

'''
def parse_table(soup):
    #lt = soup.find('div', attrs={'data-testid': 'league_table-container'})
    lt = soup.find('div', {'class': 'Ld'})
    body = lt.find('tbody')
    
    header = ['LP', '', 'Team Name', 'GP', 'W', 'D', 'L', 'GF', 'GA', 'GD', 'Pts']
    table = []
    table.append(header)
    for l in body.find_all('tr'):
        temp = l.find_all(text=True)
        if not l.find('span', attrs={'class': 'tj'}):
            temp.insert(1, '')
        table.append(temp)
    
    return table


def get_table(name, event_type='competition'):
    soup = get_soup(name, event_type)
    table = parse_table(soup)
    return table