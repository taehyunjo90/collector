from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common import exceptions

import pandas as pd
import time

import CONFIG

WAIT_SECS = 5
MAX_TRY = 5

class Collector(object):
    def __init__(self):
        # Variables
        self.bool_popup_cleared = False

        self.driver = webdriver.Chrome(executable_path="../Driver/chromedriver.exe")
        self.accessInitPage()

    def clickPopUpQuit(self, wait_secs):

        if self.bool_popup_cleared:
            return

        # Wait until pop-up and click exit button.
        try:
            popup_quit_button = WebDriverWait(self.driver, wait_secs) \
                .until(EC.element_to_be_clickable((By.CLASS_NAME, "popupCloseIcon")))
            popup_quit_button.click()
        except:
            return

        print("Popup cleared.")
        self.bool_popup_cleared = True

    def accessInitPage(self):
        self.basic_url = CONFIG.URL['BASIC']
        self.driver.get(self.basic_url)
        self.clickPopUpQuit(WAIT_SECS)

    def selectCountry(self, country):
        country_button = \
            self.driver.find_elements_by_xpath\
                ("//i[@class='bottunImageDoubleArrow buttonWhiteImageDownArrow']")[1]
        country_button.click()

        # click the country to select
        ele_countries = self.driver.find_element_by_id("countriesUL").find_elements_by_tag_name("li")

        for ele in ele_countries:
            if ele.text == country:
                ele.click()
                break

    def getStocksBasicInfoByOnePage(self, page):
        self.driver.get(self.page_url + str(page))

        time.sleep(WAIT_SECS) # fix it to wait dynamic style.

        pagesource = self.driver.page_source
        souped_ps = BeautifulSoup(pagesource, 'lxml')

        stocks = souped_ps.find("table", {"id": "resultsTable"}).find("tbody").find_all("tr")

        result = []
        for stock in stocks:
            list_stock_info = []
            for idx, td in enumerate(stock.find_all("td")):
                if idx == 0:
                    pass
                elif idx == 1:
                    list_stock_info.append(td.text)
                    list_stock_info.append(stock.find_all("td")[1].find("a", href=True)['href'])
                elif idx <= 9:
                    list_stock_info.append(td.text)
                else:
                    break
            result.append(list_stock_info)

        df_result = pd.DataFrame(result)
        return df_result

    def getStocksBasicInfoByRange(self, start, end):
        for idx, page in enumerate(range(start, end+1)):
            if idx == 0:
                df_total_stock_info = self.getStocksBasicInfoByOnePage(page)
            else:
                df_total_stock_info = pd.concat([df_total_stock_info, self.getStocksBasicInfoByOnePage(page)])

        df_total_stock_info.reset_index(inplace=True, drop=True)
        return df_total_stock_info

    def getHowManyPages(self):

        time.sleep(WAIT_SECS) # fix it to wait dynamic style.

        pagesource = self.driver.page_source
        souped_ps = BeautifulSoup(pagesource, 'lxml')
        last_num = souped_ps.find_all("a", {"class" : "pagination"})[-1].text
        last_num = int(last_num)

        # sresultet Page Url
        self.setPageURL()

        return last_num

    def setPageURL(self):
        self.page_url = self.driver.current_url
        self.page_url = self.page_url[:-1]

    def getWholeStockInfoByCountry(self, country):
        self.selectCountry(country)
        end_page = self.getHowManyPages()
        df_total_stock_info = self.getStocksBasicInfoByRange(1, end_page)
        df_total_stock_info.to_csv("test.csv")


if __name__ == "__main__":
    collector = Collector()
    collector.getWholeStockInfoByCountry("Vietnam")



