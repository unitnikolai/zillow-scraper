import json
from typing import List
import httpx
from bs4 import BeautifulSoup
from curl_cffi import requests, Curl, CurlOpt
import re
from curl_cffi.requests import AsyncSession
import asyncio

def zipcodeUrls():
    zipCodesOhio = []
    urls = []
    low = int(input("Lower bound Zipcode: "))
    high = int(input("Higher bound Zipcode: "))
    for n in range (low, high):
        code = str(n)
        zipCodesOhio.append(code)
    for code in zipCodesOhio:
        URL = "https:/zillow.com/homes/" + code
        urls.append(URL)
    return urls


async def main():
    queryZip = zipcodeUrls()
    urls = await getEstates(queryZip)
    print(urls)
    print("Scraper started...")
    data = await scrape_prop(urls)
    print(data)


#Collect links of postings on each homelisting page

async def getEstates(zipLinks):
    url_results = []
    scrape = []
    linksSite = []
    links = []
    zillowPattern = r'href="[^"]*"'
    link_pattern = r'href="([^"]+)"'    
    async with AsyncSession() as client:
        scrape = [client.get(z, impersonate = "safari_ios") for z in zipLinks]
        responses = await asyncio.gather(*scrape)
        for response in responses:
            if response.status_code != 200:
                print("Error")
            else:
                txt = response.text
                parse = BeautifulSoup(txt, "html.parser")
                urls = parse.find_all('a')
                linksSite.append(urls)
                for i in linksSite:
                    for x in i:
                        elmnt = str(x)
                        tags = re.findall(zillowPattern, elmnt)
                        for a in tags:
                            hrefUrl = str(a)
                            if hrefUrl.startswith('href="https://www.zillow.com/homedetails'):
                                hrefUrl = re.search(r'href="([^"]+)"', hrefUrl).group(1)
                                links.append(hrefUrl)
            return links

async def scrape_prop(urls):
    results = []
    scrapeSites = []
    async with AsyncSession() as client:
        for url in urls:
            site = client.get(url, impersonate = "safari_ios")
            scrapeSites.append(site)
        responses = await asyncio.gather(*scrapeSites)
        print("Fetching data...")
        for response in responses:
            print(response)
            if response.status_code != 200:
                print("ERROR: ", response.status_code, "request has been blocked")
            else:
                txt = response.text
                parse = BeautifulSoup(txt, "html.parser")
                prop = []

                jsonScript = parse.find('script', {'id': '__NEXT_DATA__', 'type': 'application/json'})
                if jsonScript:
                    jsonScript = jsonScript.get_text()
                    jsonData = json.loads(jsonScript)
                    homeData = json.loads(jsonData["props"]["pageProps"]["componentProps"]["gdpClientCache"])
                    key = next(iter(homeData))
                    propertyData = homeData[key]['property']
                    address = []
                    details = []

                    streetAddress = propertyData['address']['streetAddress']
                    city = propertyData['address']['city']
                    state = propertyData['address']['state']
                    zipcode = propertyData['address']['zipcode']

                    address.append(streetAddress)
                    address.append(city)
                    address.append(state)
                    address.append(zipcode)

                    bedrooms = propertyData['bedrooms']
                    bathrooms = propertyData['bathrooms']
                    price = propertyData['price']
                    yearBuilt = propertyData['yearBuilt']

                    details.append(bedrooms)
                    details.append(bathrooms)
                    details.append(price)
                    details.append(yearBuilt)

                    salesHistory = []
                    price_history = propertyData['priceHistory']
                    for entry in price_history:
                        date = entry['date']
                        price = entry['price']
                        salesHistory.append(date)
                        salesHistory.append(price)

                else:

                    price = parse.find_all('span', attrs={'data-testid': 'price'})
                    bedBath = parse.find_all('span', attrs={"data-testid": "bed-bath-item"})
                    #price = parse.find('span', class_='Text-c11n-8-99-3__sc-aiai24-0 dFhjAe')
                    print(price)
                    td_element = parse.find_all('td', {'data-testid': True})
                    salesHistory = []
                    house = []
                    #house.append(address)
                    house.append(price)
                    for n in bedBath:
                        stats = n.text
                        house.append(stats)

                    results.append(house)
                    results.append(salesHistory)

            prop.append(address)
            prop.append(details)
            prop.append(salesHistory)
            results.append(prop)

    return results


asyncio.run(main())
