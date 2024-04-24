import requests
from bs4 import BeautifulSoup
import re
import pandas as pd


def get_estate_urls():
    response = requests.get('https://eauction.ge/Home/Search/W3sia2V5IjoiQ2F0ZWdvcnlJRCIsInZhbHVlIjoiOTkifSx7ImtleSI6Ik9yZ2FuaXNhdGlvbklEIiwidmFsdWUiOiIzIn0seyJrZXkiOiJTdG9yZUlkIiwidmFsdWUiOiItMSJ9LHsia2V5IjoiU2VhcmNoQWxsIiwidmFsdWUiOiJmYWxzZSJ9LHsia2V5IjoiU29ydEZpbGQiLCJ2YWx1ZSI6IjMifSx7ImtleSI6ImNieFllYXJzIi/widmFsdWUiOiItMSJ9LHsia2V5IjoiY2J4UGFnZUNvdW50IiwidmFsdWUiOiIxMDAifV0=/1')
    soup = BeautifulSoup(response.text, 'html.parser')

    links = soup.find_all('a')
    estate_urls = []
    for link in links:
        href = link.get('href')
        if isinstance(href, str) and "EntityView" in href:
            estate_urls.append("https://eauction.ge" + href)
    return estate_urls


def get_estate_info(estate_url):
    response = requests.get(estate_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    st_element = soup.find('td', id='tdPriceStart').text
    start_price = float(re.findall(r'\b\d+\b', st_element)[0])

    bid_element = soup.find('span', id='dvPriceStep').text
    bid = float(re.findall(r'\b\d+\b', bid_element)[0])

    value_element = soup.find_all('td', attrs={'name': 'evaluation-fee'})[1].text
    value = float(re.findall(r'\b\d+\b', value_element)[0])
    deal = start_price/value*100
    
    try:
        area = soup.find_all('td', attrs={'name': 'Land-area-in-square'})[1].text
    except IndexError:
        area = soup.find_all('td', attrs={'name': 'building-area'})[1].text

    address = soup.find_all('td', attrs={'name': 'Place-of-Publication'})[1].text
    cadastre = soup.find_all('td', attrs={'name': 'Cadastre-code'})[1].text

    try:
        sqrp = float(start_price)/float(area)
    except ZeroDivisionError:
        sqrp = 'nan'

    start_end = soup.find('tr', id='StartEnd').text
    start_date, end_date = extract_dates(start_end)
    description = soup.find_all('td', attrs={'name': 'Description'})[1].text.split('-----')[0]

    estate_info = {'საწყისი ფასი': start_price, 'შეფასების ფასი': value, 'სხვაობა': str(deal)+'%', 'ბიჯი': bid, 'მისამართი': address, 'ფართობი': area, 
                   'დაწყების თარიღი': start_date, 'დასრულების თარიღი': end_date, 'კვადრატულის ფასი': sqrp, 'საკადასტრო': cadastre,'ლინკი': estate_url, 'აღწერა': description}
    return estate_info


def extract_dates(text):
    date_time_pattern = re.compile(r'\d{2}/\d{2}/\d{4} \d{2}:\d{2}')
    matches = date_time_pattern.findall(text)

    if matches:
        start_date = matches[0]
        end_date = matches[1]
        return [start_date, end_date]
    else:
        return ['nan', 'nan']


def main():
    dont_df = pd.read_excel('donts.xlsx')
    dont_urls = dont_df['url'].tolist()

    urls = get_estate_urls()
    estates_list = []
    i = 1
    for url in urls:
        if url not in dont_urls:
            estate = get_estate_info(url)
            if float(estate['სხვაობა'].rstrip('%')) < 7 and 'წილი' not in estate['აღწერა']:
                estates_list.append(estate)
            print(f"Scraped {i}/{len(urls)}")
            i += 1
    
    df = pd.DataFrame(estates_list)
    df = df.drop(columns=['სხვაობა', 'დაწყების თარიღი', 'კვადრატულის ფასი', 'ფართობი'], axis=1)
    df.to_excel("database.xlsx", index=False)


if __name__ == "__main__":
    main()