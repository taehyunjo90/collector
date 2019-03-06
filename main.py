
from Core.Collector import Collector


country = "Japan"
collector = Collector()
# collector.selectCountry(country)
# end_page = collector.getHowManyPages()
# collector.getStocksBasicInfoByRange(1,end_page,country)
collector.crawlingStart(country)