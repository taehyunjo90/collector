import CONFIG
from multiprocessing import Process
from Core.Collector import Collector

def getScreener(country):
    collector = Collector()
    collector.selectCountry(country)
    end_page = collector.getHowManyPages()
    collector.getStocksBasicInfoByRange(1,end_page,country)
    collector.driver.quit()

def divideScreener(country, process_num = CONFIG.NUM_MULTIPROCESSING):
    df_screener = Collector.readFile(country, "Screener")
    unit_size = int(len(df_screener) / process_num)
    for i in range(process_num):
        start_num = i * unit_size
        end_num = (i+1) * unit_size
        if i != process_num - 1:
            df = df_screener.iloc[start_num:end_num, :]
        else:
            df = df_screener.iloc[start_num:, :]
        Collector.saveFile(country, df, "Screener_" + str(i+1))

def startCrawling(country, process_num):
    collector = Collector()
    done = False
    while done == False:
        done = collector.crawlingStart(country, process_num)

def multiprocessCrwaling(country, process_num = CONFIG.NUM_MULTIPROCESSING):
    list_process = []
    for i in range(process_num):
        proc = Process(target=startCrawling, args=(country, i + 1))
        list_process.append(proc)
        proc.start()
    for proc in list_process:
        proc.join()
