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
import datetime

import CONFIG
from Util.Logger import myLogger

WAIT_SECS = 5
SHORT_WAIT_SECS = 1


NON_BANK_FIANANCIAL_REPORTS_LENGTH = 753
MAX_NOELEMENT_COUNT = 5

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
            try:
                popup_quit_button = WebDriverWait(self.driver, wait_secs).until\
                    (EC.element_to_be_clickable((By.CSS_SELECTOR, "i[class='popupCloseIcon largeBannerCloser']")))
                popup_quit_button.click()
            except:
                return

        logger.logger.info("Popup cleared.")
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

        isClicked = False
        for ele in ele_countries:
            if ele.text == country:
                ele.click()
                isClicked = True
                break

        if isClicked:
            logger.logger.info("Click the country successfully :: " + country)
        else:
            raise Exception("Not proper country entered. Recheck country name.")

    def getStocksBasicInfoByOnePage(self, page):
        self.driver.get(self.page_url + str(page))

        time.sleep(WAIT_SECS) # FIX :: fix it to wait dynamic style.

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

    def getStocksBasicInfoByRange(self, start, end, country):
        for idx, page in enumerate(range(start, end+1)):
            logger.logger.info("Get screener pages :: Doing " + str(page) + " / " + str(end) + " page...")
            self.clickPopUpQuit(SHORT_WAIT_SECS)
            if idx == 0:
                df_total_stock_info = self.getStocksBasicInfoByOnePage(page)
            else:
                df_total_stock_info = pd.concat([df_total_stock_info, self.getStocksBasicInfoByOnePage(page)])
        df_total_stock_info.reset_index(inplace=True, drop=True)

        # Screener Columns
        cols = ['Company Name', 'URL', 'Code', 'Market', 'Industry',\
                'Sub-Industry', 'Price', 'Chg', 'Cap', 'Vol', 'Done']
        list_multiindex = []
        for col in cols:
            list_multiindex.append(("Screener", col))
        columns = pd.MultiIndex.from_tuples(list_multiindex)
        df_total_stock_info.loc[:,'Done'] = False
        df_total_stock_info.columns = columns
        self.saveFile(country, df_total_stock_info, "Screener")

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

    def getFinancialReports(self, option, FR_type):
        table_info = self.driver.find_element_by_id("rrtable").text.split("\n")

        if option == "Year":
            tag = FR_type + "/Y"
        elif option == "Quater":
            tag = FR_type + "/Q"

        index = []
        columns = []
        contents = []

        count = 0
        for i, ele in enumerate(table_info):
            if i == 0:
                list_year_quater = []
                year = ele.split(":")[-1]
            elif i < 8:
                if i % 2 == 1:
                    count += 1
                    columns.append(tag + "-" + str(count))
                    year_quater = year + "/" + ele
                    list_year_quater.append(year_quater)
                    if i == 7:
                        contents.append(list_year_quater)
                        index = index + ["YYYY/DD/MM"]
            else:
                eles = ele.split(" ")
                contents.append(eles[-4:])
                index.append(" ".join(eles[:-4]))

        df = pd.DataFrame(contents, index=index, columns=columns)

        if FR_type == "CFS":
            df = pd.concat([df.iloc[:1,:], df.iloc[2:,:]])
        else:
            pass

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

    def checkBadGateway(self):
        if self.driver.find_element_by_tag_name("h1").text == "502 Bad Gateway":
            self.driver.quit()
            return True
        else:
            return False



    def getEachStockOneArrayDF(self, initURL):

        self.goEachStockInitPage(initURL)
        df = self.getEachStockInitPageGetInfoTable()

        self.goToFinancialReports("BS")

        df = pd.concat([df, self.getFinancialReports("Quater", "BS")], axis=1)
        self.clickAnnualButton()
        df = pd.concat([df, self.getFinancialReports("Year", "BS")], axis=1)

        self.clickAnotherFinancialReport("IS")

        df = pd.concat([df, self.getFinancialReports("Quater", "IS")], axis=1)
        self.clickAnnualButton()
        df = pd.concat([df, self.getFinancialReports("Year", "IS")], axis=1)

        self.clickAnotherFinancialReport("CFS")

        df = pd.concat([df, self.getFinancialReports("Quater","CFS")], axis=1)
        self.clickAnnualButton()
        df = pd.concat([df, self.getFinancialReports("Year","CFS")], axis=1)

        return df

    def crawlingStart(self, country, process_num):

        # read screener
        df_screener = self.readFile(country, "Screener_" + str(process_num))

        # Screener Columns
        cols = ['Company Name', 'URL', 'Code', 'Market', 'Industry', \
                'Sub-Industry', 'Price', 'Chg', 'Cap', 'Vol']
        list_multiindex = []
        for col in cols:
            list_multiindex.append(("Screener", col))
        columns = pd.MultiIndex.from_tuples(list_multiindex)

        len_df_screener = len(df_screener.index)

        df_total_not_bank = self.readFile(country, "NonFinancial_" + str(process_num))
        df_total_bank = self.readFile(country, "Financial_" + str(process_num))

        i = 0
        count_noelement = 0
        while True:

            ### already craweld passing and check badgateway error.
            r = df_screener.iloc[i, :]
            if r[-1] == True:
                i += 1
                continue
            elif self.checkBadGateway(): #True -> badgatewayError
                return False # whole process is not executed, but have to re-start the process

            logger.logger.info( "Doing Crawling :: "+ str(i+1) + " / " + str(len_df_screener))

            # 팝업창이 등장하면 팝업창을 클릭해주는 예외처리
            try:
                tmp_result = self.getEachStockOneArrayDF(r[1]) # Financial Reports -> One lined dataframe
            except exceptions.NoSuchElementException:
                count_noelement += 1
                logger.logger.info("There is no elements. Count :: {}".format(str(count_noelement)))
                if count_noelement == MAX_NOELEMENT_COUNT:
                    i += 1
                    count_noelement = 0
                    continue
                else:
                    continue
            except exceptions.WebDriverException:
                logger.logger.info("Pop-up Error occured :: Try to click Pop-up." )
                self.clickPopUpQuit(WAIT_SECS)
                logger.logger.info("Retry started...")
                continue
            # 에러 발생시 다시 진행
            except:
                continue

            df_tmp = pd.DataFrame(r[:-1]).T # make screener data to one line
            df_tmp.columns = columns
            df_tmp.index = [0]
            df = pd.concat([df_tmp, tmp_result], axis=1) # concat screener data and financial reports data

            length_df = len(df.columns)
            # print(length_df)
            if length_df > NON_BANK_FIANANCIAL_REPORTS_LENGTH: # Not a bank
                if df_total_not_bank is None:
                    df_total_not_bank = df
                else:
                    df_total_not_bank = self.mergeDFs(df_total_not_bank, df)
            else:
                if df_total_bank is None:
                    df_total_bank = df
                else:
                    df_total_bank = self.mergeDFs(df_total_bank, df)


            i += 1
            count_noelement = 0
            # df길이에 i가 도달하면 break (전체 완료 하였음)


            if i % CONFIG.SAVE_LENGTH == 0 or i == len_df_screener:
                df_screener.iloc[:i, -1] = True
                self.saveFile(country, df_screener, "Screener_" + str(process_num))

                if df_total_not_bank is not None:
                    df_total_not_bank.reset_index(drop=True, inplace=True)
                    self.saveFile(country, df_total_not_bank, "NonFinancial_" + str(process_num))

                if df_total_bank is not None:
                    df_total_bank.reset_index(drop=True, inplace=True)
                    self.saveFile(country, df_total_bank, "Financial_" + str(process_num))

            if i == len_df_screener:
                return True

    @classmethod
    def saveFile(cls, country, df, type):
        # date = datetime.datetime.today().strftime('%Y-%m-%d')
        if df is not None:
            df.to_csv(CONFIG.PATH['SAVE'] + country + "_" + type + ".csv")
            logger.logger.info("Save :: " + country + " " + type + " is successfully saved.")
        elif df is None:
            return

    @classmethod
    def readFile(cls, country, type):
        # date = datetime.datetime.today().strftime('%Y-%m-%d')

        try:
            df = pd.read_csv(CONFIG.PATH['SAVE'] + country + "_" + type + ".csv", \
                             header=[0,1], index_col=0, encoding='cp949')
            logger.logger.info("Read :: " + country + " " + type + " is successfully readed.")
        except FileNotFoundError:
            logger.logger.info("Read :: There is no " + country + " " + type)
            df = None
        except:
            logger.logger.info("Read :: " + country + " " + type + " failed")
            raise Exception("Reading a file error.")

        return df

    def mergeDFs(self, df_total, df_new):
        # total_df은 index에 계정이 들어가 있음
        len_total_df = len(df_total.columns)
        len_new_df = len(df_new.columns)
        if len_total_df >= len_new_df:
            ret = pd.merge(df_total.T, df_new.T, left_index=True, right_index=True, how='left')
        else:
            ret = pd.merge(df_new.T, df_total.T, left_index=True, right_index=True, how='left')
        return ret.T


