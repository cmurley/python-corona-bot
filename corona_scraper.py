# Scrape the CDC and Texas DPHS for Coronavirus Updates
# Format CDC Update and Post to Slack Channel
# Format TX Update and Post Counties I'm Interested In to Slack Channel

import re
import requests
import json
from bs4 import BeautifulSoup
from datetime import datetime

now = datetime.now()
dt_string = now.strftime("%d/%m/%Y %H:00")

data = dict()
data[dt_string] = dict()
data[dt_string]['us'] = dict()
data[dt_string]['tx'] = dict()

# Scrapes data from the CDC Website
def getCDC():
    CDC = 'https://www.cdc.gov/coronavirus/2019-ncov/cases-updates/cases-in-us.html'
    cdcPage = requests.get(CDC, verify=False)

    soup = BeautifulSoup(cdcPage.content, 'html.parser')
    results = soup.find(
        'table', attrs={'class': 'table table-bordered nein-scroll'})

    # Get Totals for US
    for result in results.find_all('tr'):
        cols = result.find_all('td')
        if (len(cols) > 0):
            #data['us'].append({cols[0].text: cols[1].text})
            data[dt_string]['us'][cols[0].text] = cols[1].text

    # Get total Deaths
    death_count = soup.find('li', text=re.compile('Total deaths:(.*)'))
    data[dt_string]['us']['Total Deaths'] = death_count.text


# Scrapes data from Texas DSHS Website
def getTX():
    dshs = 'https://www.dshs.state.tx.us/news/updates.shtm'
    dshsPage = requests.get(dshs, verify=False)

    soup = BeautifulSoup(dshsPage.content, 'html.parser')

    # County Results
    results = soup.find(
        'table', attrs={
            'class': 'zebraBorder',
            'summary': 'COVID-19 Cases in Texas Counties'
        })
    for result in results.find_all('tr'):
        cols = result.find_all('td')
        if (len(cols) > 0):
            #data['tx'].append({cols[0].text: cols[1].text})
            data[dt_string]['tx'][cols[0].text] = cols[1].text

    # State Total
    tx_total = soup.find_all(
        'table', attrs={
            'class': 'zebraBorder',
            'summary': 'Statewide COVID-19 Cases'
        })
    print(tx_total)
    #.find('th', text='Total Statewide Cases')
    #total = tx_total.find_next('td')
    if (len(total) > 0):
        data[dt_string]['tx']['state total'] = total[0].text

# Takes the data from 'us' key and formats it and returns the formatted data - Calls getCDC()
def formatCDC():
    text = ''
    getCDC()
    # Adding Death Count
    text += '- ' + ''.join(data[dt_string]['us']['Total Deaths']) + '\n'
    for key in data[dt_string]['us'].keys():
        if (key != 'Total Deaths'):
            row = (key, ': ', data[dt_string]['us'][key])
            text += '- ' + ''.join(row) + '\n'
    return text

# Configure CDC Notification - Calls formatCDC()
def post2CDC():
    cdcText = formatCDC()
    block = '*COVID-19 Cases in the US*\n {}'.format(
        cdcText
    )
    send_message_to_slack(block)

# Takes the data from 'tx' key and formats it and returns the formatted data - Calls getTX()
def formatTX():
    text = ''
    getTX()
    harris = ('Harris County: ', data[dt_string]['tx']['Harris'])
    dallas = ('Harris County: ', data[dt_string]['tx']['Dallas'])
    travis = ('Travis County: ', data[dt_string]['tx']['Travis'])
    total = ('Total Statewide Cases: ', data[dt_string]['tx']['state total'])
    text += '- ' + ''.join(dallas) + '\n- ' + ''.join(harris) + \
        '\n- ' + ''.join(travis) + '\n- ' + ''.join(total)
    return text

# Configure TX Notification - Calls formatTX()
def post2TX():
    txText = formatTX()
    block = '*COVID-19 Cases Nearby*\n {}'.format(
        txText
    )
    #send_message_to_slack(block)

# Posting to a Slack channel
def send_message_to_slack(text):
    from urllib import request, parse
    import json

    post = {"text": "{0}".format(text)}

    try:
        json_data = json.dumps(post)
        req = request.Request("yourSlackWebhook",
                              data=json_data.encode('ascii'),
                              headers={'Content-Type': 'application/json'})
        resp = request.urlopen(req)
    except Exception as em:
        print("EXCEPTION: " + str(em))


post2CDC()
post2TX()