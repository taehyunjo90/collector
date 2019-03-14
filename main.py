import sys

from Core.MultiWork import *


def run(country, option, num_processer = 4):
    if option == "screener":
        # 스크리너 가져오기
        getScreener(country)

    elif option == "divide":
        # 나누기
        divideScreener(country, num_processer)

    elif option == "crawling":
        multiprocessCrwaling(country, num_processer)

    elif option == "merge":
        Collector.mergeFiles(country, "Financial", num_processer)
        Collector.mergeFiles(country, "NonFinancial", num_processer)

    else:
        print("please type :: python main.py 'country' 'option[screener, divide, crawling, merge]' 'num_processor'")

if __name__ == "__main__":
    country = sys.argv[1]
    option = sys.argv[2]
    num_processor = int(sys.argv[3])

    run(country, option, num_processor)