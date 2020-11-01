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

HEADER = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:82.0) Gecko/20100101 Firefox/82.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Referer': 'https://ehw.fit.vutbr.cz/izv/',
    'Upgrade-Insecure-Requests': '1',
}

COLUMNS = ['p1', 'p36', 'p37', 'p2a-year', 'p2a-m-d', 'weekday(p2a)', 'p2b-hour', 'p2b-minute', 'p6', 'p7', 'p8', 'p9',
           'p10', 'p11', 'p12', 'p13a', 'p13b', 'p13c', 'p14', 'p15', 'p16', 'p17', 'p18', 'p19', 'p20', 'p21', 'p22',
           'p23', 'p24', 'p27', 'p28', 'p34', 'p35', 'p39', 'p44', 'p45a', 'p47', 'p48a', 'p49', 'p50a', 'p50b', 'p51',
           'p52', 'p53', 'p55a', 'p57', 'p58', 'a', 'b', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'n', 'o', 'p',
           'q', 'r', 's', 't', 'p5a']
C_LEN = len(COLUMNS)

strings = [0, 4, 61, 60, 57, 56, 53, 54, 58]  # indexes of columns with value type string
floats = [52, 51, 50, 49, 48, 47]  # indexes of columns with value type float
ints = [1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19,
        20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35,
        36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 55, 59, 62, 63, 64, 65]  # indexes of columns with value type int


class DataDownloader:
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
                    for i in range(C_LEN):
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
