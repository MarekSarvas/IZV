"""
Author: Marek Sarvas
School: VUT FIT
Project: IZV
Description: Script for downloading, parsing and storing car crashes data in czech republic for given years and regions.
"""

import gzip
import pickle
from io import TextIOWrapper
import glob
import requests
from zipfile import ZipFile
import requests
from bs4 import BeautifulSoup
import numpy as np
import os
import csv
import re

# header for requests on https://ehw.fit.vutbr.cz/izv/
HEADER = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:82.0) Gecko/20100101 Firefox/82.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Referer': 'https://ehw.fit.vutbr.cz/izv/',
    'Upgrade-Insecure-Requests': '1',
}

# column headers for formatted data, later on region code is inserted into index 0
COLUMNS = ['ID', 'druh pozemnej komunikacie', 'cislo pozemnej komunikacie', 'rok', 'mesiac-den', 'den v tyzdni', 'hodina',
           'minuta', 'druh nehody', 'druh zrazky iducich vozidiel', 'druh pevnej prekazky', 'charakter nehody',
           'zavinenie nehody', 'alkohol u vinnika nehody pritomny', 'hlavne priciny nehody', 'usmrtenych osob',
           'tazko zranenych osob', 'lahko zranenych osob', 'celkova hmotna skoda', 'druh povrchu vozovky',
           'stav povrchu vozovky v dobe nehody', 'stav komunikacie', 'poveternostne podmienky v dobe nehody', 'viditelnost',
           'rozhladove pomery', 'delenie komunikacie', 'situovanie nehody na komunikacii', 'riadenie premavky v dobe nehody',
           'miestna uprava prednosti v jazde', 'specificke miesta a objekty v mieste nehody', 'smerove pomery',
           'pocet zucastnenych vozidiel', 'miesto dopravnej nehody', 'druh krizujucej komunikacie', 'druh vozidla',
           'vyrobna znacka motoroveho vozidla', 'rok vyroby vozidla', 'charakteristika vozidla', 'smyk', 'vozidlo po nehode',
           'unik provoznych, prepravovanych hmot', 'zposob vyslobodenia osob z vozidla', 'smer jazdy alebo postavenia vozidla',
           'skoda na vozidle', 'kategoria sofera', 'stav sofera', 'vonkajsie ovplyvnenie sofera', 'a', 'b', 'gps_x', 'gps_y',
           'f', 'g', 'h', 'i', 'j', 'k', 'l', 'n', 'o', 'p', 'q', 'r', 's', 't', 'lokalita nehody']
C_LEN = len(COLUMNS)

strings = [0, 4, 61, 60, 57, 56, 53, 54, 58]  # indexes of columns with value type string
floats = [52, 51, 50, 49, 48, 47]  # indexes of columns with value type float
ints = [1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19,
        20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35,
        36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 55, 59, 62, 63, 64, 65]  # indexes of columns with value type int


class DataDownloader:
    """ Class for downloading data, formatting them and storing into memory/cache. """

    def __init__(self, url='https://ehw.fit.vutbr.cz/izv/', folder='data', cache_filename='data_{}.pkl.gz',
                 header=None):

        if header is None:
            self.header = HEADER
        self.url = url
        self.folder = f"./{folder}"
        self.cache_file = cache_filename
        # regions with theirs string code, number code and csv filename
        self.region_codes = {'PHA': ('00', '00.csv'), 'STC': ('01', '01.csv'), 'JHC': ('02', '02.csv'),
                             'PLK': ('03', '03.csv'), 'ULK': ('04', '04.csv'), 'HKK': ('05', '05.csv'),
                             'JHM': ('06', '06.csv'), 'MSK': ('07', '07.csv'), 'OLK': ('14', '14.csv'),
                             'ZLK': ('15', '15.csv'), 'VYS': ('16', '16.csv'), 'PAK': ('17', '17.csv'),
                             'LBK': ('18', '18.csv'), 'KVK': ('19', '19.csv')}

        self.int_nan = -99999  # NaN for integers
        self.cache = {}
        self.download_regex = re.compile('data/datagis([0-9]{4}|-rok-[0-9]{4})\\.zip')  # only files with year data

    def download_data(self):
        """Downloads data from url.

        Create directory where to store the data and download last zip of every year into it. Using BeautifoulSoup and
        regex to find correct zips in html.
        :return: None
        """
        if not os.path.exists(self.folder):
            os.mkdir(self.folder)

        # find names of zip files to download
        s = requests.session()
        doc = s.get('https://ehw.fit.vutbr.cz/izv/', headers=self.header).text
        soup = BeautifulSoup(doc, 'html.parser')
        zip_names = [item.get('href') for item in soup.find_all("a", {"class": "btn btn-sm btn-primary"})]

        # download zips when matching regex for year data zip file
        for name in zip_names:
            if self.download_regex.match(name) and not os.path.exists(f'{self.folder}/{name.split("/")[-1]}'):
                r = s.get(f'https://ehw.fit.vutbr.cz/izv/{name}', headers=self.header)
                with open(f'{self.folder}/{name.split("/")[-1]}', 'wb') as f:
                    f.write(r.content)

        # download last month available if it is not already downloaded
        if not os.path.exists(f'{self.folder}/{zip_names[-1].split("/")[-1]}'):
            r = s.get(f'https://ehw.fit.vutbr.cz/izv/{zip_names[-1]}', headers=self.header)
            with open(f'{self.folder}/{zip_names[-1].split("/")[-1]}', 'wb') as f:
                f.write(r.content)

    def parse_region_data(self, region):
        """ Format downloaded data into correct values and data types.

        Downloads missing zip files, format data from every year for every region in 'region' variable and stores them
        into numpy arrays. Every numpy array represents column in csv file.

        :param region: list of regions to parse from zips
        :return: tuple of list of column headers for data and list of numpy arrays where every array is one column
        """
        self.download_data()
        data_list = []
        final_data = []

        csv_file = self.region_codes.get(region)[1]  # get csv filename based on given region

        data_header = COLUMNS.copy()
        data_header.insert(0, 'region')

        # open all zips with year data and read csv files for given region
        for zip_file in glob.glob(self.folder + '/*.zip'):
            with ZipFile(zip_file) as zf:
                with zf.open(csv_file, "r") as csv_raw:
                    csv_wrap = TextIOWrapper(csv_raw, encoding='ISO-8859-2')
                    csv_r = csv.reader(csv_wrap, delimiter=';', quotechar='"')

                    rows = len(list(csv_r))  # number of crashes in file
                    csv_raw.seek(0)

                    # premake numpy arrays with corresponding data types
                    for r in range(C_LEN):
                        if r in strings:
                            data_list.append(np.empty(rows, dtype='<U32'))
                        elif r in floats:
                            data_list.append(np.empty(rows, dtype=float))
                        else:
                            data_list.append(np.empty(rows, dtype=int))

                    # region array
                    tmp = np.empty(rows, dtype='<U3')
                    tmp[:] = region

                    current_row = 0
                    for row in csv_r:
                        self.format_line2(row, data_list, current_row)
                        current_row += 1

                data_list.insert(0, tmp.copy())

                # concat data from all files
                if not final_data:
                    final_data = data_list.copy()
                else:
                    for i in range(len(data_header)):
                        final_data[i] = np.concatenate((final_data[i], data_list[i]))

                data_list = []

        return (data_header, final_data)

    def format_line2(self, data, data_list, j):
        """ Format one line of data from read file.

        Format time and date separately, than store data into pre-made numpy arrays when converting values with invalid
        data type store "my NaN number".
        :param data: one row of data from file
        :param data_list: list of numpy arrays
        :param j: current row for indexing into numpy arrays
        :return: None
        """
        # time formatting
        data.insert(6, self.int_nan)  # placeholder because time is divided into hours, minutes
        time = data[5]
        data[5] = (lambda x: x if int(x) < 25 else self.int_nan)(time[:2])  # 25 is unknown time  for hours
        data[6] = (lambda x: x if int(x) < 60 else self.int_nan)(time[2:])  # 60 is unknown time for minutes

        # date formatting
        year, m_d = data[3].split('-', 1)

        data.insert(3, year)  # insert year as new column
        data[4] = m_d  # change date to only month-day value

        for i in floats:
            try:
                data_list[i][j] = data[i].replace(',', '.')
            except ValueError:
                data_list[i][j] = self.int_nan
        for i in ints:
            try:
                data_list[i][j] = data[i]
            except ValueError:
                data_list[i][j] = self.int_nan
        for i in strings:
            data_list[i][j] = data[i]

        return None

    def get_list(self, regions=None):
        """ Concatenate formatted data for every given region, stores them into memory and cache(compressed on disk).

        If regions are not specified it gets data of every region (region codes stored in instance attribute). Every
        regions data concatenates into numpy arrays representing columns. It takes data from memory if available, if not
        from disk cache if disk cache is not created it calls parser, formatted data stores into disk cache, memory.
        :param regions: list of regions to create list of
        :return:  tuple of list of column headers for data and list of numpy arrays where every array is one column
        """
        full_data = []
        full_header = []

        if not regions:
            regions = self.region_codes.keys()

        for reg in regions:
            print(f'Parsing... ({reg})')
            # saved in memory
            if reg in self.cache:
                reg_data = self.cache.get(reg)
            # saved in cache on disk
            elif os.path.exists(f'{self.folder}/{self.cache_file.format(reg)}'):
                with gzip.open(f'{self.folder}/{self.cache_file.format(reg)}', 'rb') as f:
                    reg_data = pickle.load(f)
            # unprocessed
            else:
                reg_data = self.parse_region_data(reg)  # parse data
                with gzip.open(f'{self.folder}/{self.cache_file.format(reg)}', 'w+b') as f:  # save to cache on disk
                    pickle.dump(reg_data, f)
                self.cache[reg] = reg_data  # save to memory

            # concatenate data from all regions
            if not full_data:
                full_data = reg_data[1].copy()
                full_header = reg_data[0].copy()
            else:
                for i in range(len(reg_data[0])):
                    full_data[i] = np.concatenate((full_data[i], reg_data[1][i]))

        return full_header, full_data


if __name__ == "__main__":
    dd = DataDownloader()
    regions = ['PHA', 'ULK', 'JHM']
    data = dd.get_list(regions)
    print(f'Regions: {regions}')
    print(f'Columns: {data[0]}')
    print(f'Number of records: {data[1][0].shape[0]}')
