import smtplib
import urllib
import bs4
import re
import json
import schedule
import time
import pdb

def format_discount_html(discounts):
    res = "<h2>Games found</h2>\n<ul>"
    for d in discounts:
        res += "<li>" + d["name"] + "<a href=\"" + d["url"] + "\">"
        res += "[" + d["vendor"] + "]" + "(" + d["discount"] + ")"
        res += "</a><br>" + "</li>\n"
    res += "</ul>"
    return res


def send_email(creds_path, discounts):
    data = open(creds_path, 'r').read()
    data = json.loads(data)
    fromAddress = data['fromAddress']
    password = data['password']
    toAddress = data['toAddress']

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(fromAddress, password)
    msg = "From:{}\nTO:{}\nContent-type: text/html\nSubject:Free game detected\n\n{}".format(fromAddress, toAddress, format_discount_html(discounts))
    print(msg)

    server.sendmail(toAddress, toAddress, msg)
    server.quit()


def parse_steamdb():
    url = "https://steamdb.info"
    vendor = "steam"
    req = urllib.request.Request(url+"/sales", headers={'User-Agent' : "Magic Browser"}) 
    page = urllib.request.urlopen(req)

    soup = bs4.BeautifulSoup(page, "lxml")
    table = soup.find_all("tr")
    free_games = []
    for row in table:
        cols = row.find_all("td")
        try:
            game_name = cols[2].a.text.lower()
            discount = cols[3].text.lower()
            game_url = url + cols[2].a.attrs["href"]
            if "-100" in discount:
                free_games.append(
                        {
                            "vendor": vendor,
                            "name": game_name,
                            "discount": discount,
                            "url": game_url,
                        })
        except:
            continue
    return free_games


def parse_reddit_gamedeal():
    url = "https://old.reddit.com/r/GameDeals/"
    req = urllib.request.Request(url, headers={'User-Agent' : "Magic Browser"}) 
    page = urllib.request.urlopen(req)

    soup = bs4.BeautifulSoup(page, "lxml")

    table = soup.find_all('p', {"class":"title"})
    free_games = []
    for t in table:
        try:
            text = t.a.text
            reg = re.search('.*?\[(.*?)\](.*?)\((.*?)\)',text)
            vendor = reg.group(1).lower()
            game_name = reg.group(2).lower()
            discount = reg.group(3).lower()
            game_url = t.a.get('href')
            if "100" in discount or "free" in discount:
                free_games.append(
                        {
                            "vendor": vendor,
                            "name": game_name,
                            "discount": discount,
                            "url": game_url,
                        })
        except Exception as e:
            print(e)
            continue
    return free_games

game_list = []
def job():
    global game_list
    deals = parse_reddit_gamedeal() + parse_steamdb()
    new_games = []
    # Add new games
    for g in deals:
        if g not in game_list:
            new_games.append(g)
    game_list = deals
    deals = new_games

    if len(deals) != 0:
        print(deals)
        send_email("creds.json", deals)

schedule.every(4).hours.do(job)
#schedule.every(10).seconds.do(job)
#schedule.every(1).minutes.do(job)
#schedule.every().day.at("22:57").do(job)
while True:
    schedule.run_pending()
    time.sleep(1)
