from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common import exceptions
from selenium.webdriver.common.action_chains import ActionChains

import pandas as pd
import numpy as np
import time

import CONFIG
from Util.Logger import myLogger

WAIT_SECS = 5
MAX_TRY = 5
SHORT_WAIT_SECS = 1

logger = myLogger("Collector")

class Collector(object):
    def __init__(self):
        # Variables
        self.bool_popup_cleared = False
        self.driver = webdriver.Chrome(executable_path="Driver/chromedriver.exe")
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

        logger.logger.debug("Access to initial page successfully!")

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

        logger.logger.info("Click the country successfully :: " + country)

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
        logger.logger.debug("Get " + str(page) + " successfully.")
        return df_result

    def getStocksBasicInfoByRange(self, start, end):
        for idx, page in enumerate(range(start, end+1)):
            logger.logger.info("Get basic info of stocks :: Doing " + str(page) + " / " + str(end) + " ...")
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

        # Page Url
        self.setPageURL()

        logger.logger.debug("Get basic page url & last page number.")

        return last_num

    def setPageURL(self):
        self.page_url = self.driver.current_url
        self.page_url = self.page_url[:-1]

    def getWholeStockInfoByCountry(self, country):
        self.selectCountry(country)
        end_page = self.getHowManyPages()
        df_total_stock_info = self.getStocksBasicInfoByRange(1, end_page)
        # df_total_stock_info.to_csv("test.csv")
        return df_total_stock_info

    def goEachStockInitPage(self, url):
        self.driver.get(CONFIG.URL['EQUITY'] + url)
        try:
            stockName = WebDriverWait(self.driver, WAIT_SECS) \
                .until(EC.presence_of_element_located((By.CLASS_NAME, "instrumentHead")))
            stockName = self.driver.find_element_by_class_name("instrumentHead").text.split("\n")[0]
            logger.logger.info("Access to " + stockName + " successfully.")
        except:
            logger.logger.info("Access to " + stockName + " failed.")
            logger.logger.debug("Fail access url :: " + url)

    def getEachStockInitPageGetInfoTable(self):
        table_info = self.driver.find_element_by_class_name("overviewDataTable").text.split("\n")

        columns = []
        contents = []
        for i, ele in enumerate(table_info):
            if i % 2 == 0:
                columns.append(ele)
            else:
                contents.append(ele)

        list_multi = []
        for col in columns:
            list_multi.append(("Basic", col))

        index = pd.MultiIndex.from_tuples(list_multi)

        df_basic_info = pd.DataFrame(contents, index=index)
        df_basic_info = df_basic_info.T

        logger.logger.debug("Get initial info succesfully.")

        return df_basic_info

    def goToFinancialReports(self, option):
        notToClickButtion = self.driver.find_element_by_link_text("Financials")
        ActionChains(self.driver).move_to_element(notToClickButtion).perform()

        if option == "BS":
            toClickBS = self.driver.find_element_by_link_text("Balance Sheet")
        elif option == "IS":
            toClickBS = self.driver.find_element_by_link_text("Income Statement")
        elif option == "CFS":
            toClickBS = self.driver.find_element_by_link_text("Cash Flow")

        toClickBS.click()

        try:
            table = WebDriverWait(self.driver, WAIT_SECS) \
                .until(EC.presence_of_element_located((By.ID, "rrtable")))
            logger.logger.debug("Get " + option + " page successfully.")
        except:
            logger.logger.debug("Get " + option + " page Failed.")

    def getFinancialReports(self, option):
        table_info = self.driver.find_element_by_id("rrtable").text.split("\n")

        if option == "Year":
            tag = "Y"
        elif option == "Quater":
            tag = "Q"

        index = []
        columns = []
        contents = []

        count = 0
        for i, ele in enumerate(table_info):
            if i == 0:
                pass
                # year = ele.split(" ")[-1]
            elif i < 8:
                if i % 2 == 1:
                    count += 1
                    columns.append(tag + "-" + str(count))
            else:
                eles = ele.split(" ")
                contents.append(eles[-4:])
                index.append(" ".join(eles[:-4]))

        df = pd.DataFrame(contents, index=index, columns=columns)
        df = self.toOneArrayDF(df)

        logger.logger.debug("Get " + option + " dataframe succesfully.")

        return df

    def clickAnnualButton(self):
        self.driver.find_element_by_xpath(
            "//div[@class='float_lang_base_1']/a[@class='newBtn toggleButton LightGray']").click()

        try:
            table = WebDriverWait(self.driver, WAIT_SECS) \
                .until(EC.presence_of_element_located((By.ID, "rrtable")))
            logger.logger.debug("Get annual page successfully.")
        except:
            logger.logger.debug("Get annual page failed.")

        time.sleep(SHORT_WAIT_SECS)

    def toOneArrayDF(self, df):
        list_multi = []

        for i, col in enumerate(df.columns):
            if i == 0:
                data = df.loc[:, col].values
            else:
                data = np.append(data, df.loc[:, col].values)
            for idx in df.index:
                list_multi.append((col, idx))

        multi_index = pd.MultiIndex.from_tuples(list_multi)
        df_one_arrayed = pd.DataFrame(index=multi_index)
        df_one_arrayed.loc[:, 0] = data
        df_one_arrayed = df_one_arrayed.T
        return df_one_arrayed

    def clickAnotherFinancialReport(self, option):
        if option == "BS":
            select = "Balance Sheet"
        elif option == "IS":
            select = "Income Statement"
        elif option == "CFS":
            select = "Cash Flow"
        self.driver.find_element_by_link_text(select).click()

        try:
            table = WebDriverWait(self.driver, WAIT_SECS) \
                .until(EC.presence_of_element_located((By.ID, "rrtable")))
            logger.logger.debug("Move to " + option + " successfully.")
        except:
            logger.logger.debug("Move to " + option + " failed.")

    def getEachStockOneArrayDF(self, initURL):

        self.goEachStockInitPage(initURL)
        df = self.getEachStockInitPageGetInfoTable()

        self.goToFinancialReports("BS")

        df = pd.concat([df, self.getFinancialReports("Quater")], axis=1)
        self.clickAnnualButton()
        df = pd.concat([df, self.getFinancialReports("Year")], axis=1)

        self.clickAnotherFinancialReport("IS")

        df = pd.concat([df, self.getFinancialReports("Quater")], axis=1)
        self.clickAnnualButton()
        df = pd.concat([df, self.getFinancialReports("Year")], axis=1)

        self.clickAnotherFinancialReport("CFS")

        df = pd.concat([df, self.getFinancialReports("Quater")], axis=1)
        self.clickAnnualButton()
        df = pd.concat([df, self.getFinancialReports("Year")], axis=1)

        return df


