
from Core.Collector import Collector

country = "Japan"
collector = Collector()
collector.selectCountry(country)
end_page = collector.getHowManyPages()
# df_screener = collector.getStocksBasicInfoByRange(1,end_page)
df_screener = collector.getStocksBasicInfoByRange(1,1)
df_not_bank, df_bank = collector.crawlingStart(df_screener)
collector.saveFiles(country,df_not_bank, "NonFinancial")
collector.saveFiles(country,df_bank, "Financial")