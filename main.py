
from Core.Collector import Collector

def getScreener(country):
    collector = Collector()
    collector.selectCountry(country)
    end_page = collector.getHowManyPages()
    collector.getStocksBasicInfoByRange(1,end_page,country)

def startCrawling(country):
    collector = Collector()
    done = False
    while done == False:
        done = collector.crawlingStart(country)


startCrawling("Japan")