
from Core.Collector import Collector

collector = Collector()
collector.selectCountry("Vietnam")
end_page = collector.getHowManyPages()
df_screener = collector.getStocksBasicInfoByRange(1,1)

df_not_bank, df_bank = collector.crawlingStart(df_screener.iloc[:,:10])

df_not_bank.to_csv("test_not_bank.csv")
df_bank.to_csv("test_bank.csv")