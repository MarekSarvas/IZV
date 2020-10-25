import re
import sys
from io import BytesIO, TextIOWrapper
import glob
import requests
from zipfile import ZipFile
import requests
from bs4 import BeautifulSoup
import numpy as np
import os
import csv

HEADER = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:82.0) Gecko/20100101 Firefox/82.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Referer': 'https://ehw.fit.vutbr.cz/izv/',
    'Upgrade-Insecure-Requests': '1',
}

COLUMN_HEADER = ['p1', 'p36', 'p37', 'p2a', 'weekday(p2a)', 'p2b-hour', 'p2b-minute', 'p6',
                 'p7', 'p8', '9', 'p10', 'p11', 'p12', 'p13a', 'p13b', 'p13c', 'p14', 'p15', 'p16', 'p17', 'p18', 'p19',
                 'p20', 'p21', 'p22', 'p23', 'p24', 'p27', 'p28', 'p34', 'p35', 'p39', 'p44', 'p45a', 'p47', 'p48a',
                 'p49', 'p50a', 'p50b', 'p51', 'p52', 'p53', 'p55a', 'p57', 'p58', 'd', 'e', 'p5a']


class DataDownloader:
    def __init__(self, url='https://ehw.fit.vutbr.cz/izv/', folder='data', cache_filename='data_{}.pkl.gz',
                 header=None):
        if header is None:
            self.header = HEADER
        self.url = url
        self.folder = f"./{folder}"
        self.cache_file = cache_filename
        self.region_codes = {'PHA': ('00', '00.csv'), 'STC': ('01', '01.csv'), 'JHC': ('02', '02.csv'),
                             'PLK': ('03', '03.csv'), 'ULK': ('04', '04.csv'), 'HKK': ('05', '05.csv'),
                             'JHM': ('06', '06.csv'), 'MSK': ('07', '07.csv'), 'OLK': ('14', '14.csv'),
                             'ZLK': ('15', '15.csv'), 'VYS': ('16', '16.csv'), 'PAK': ('17', '17.csv'),
                             'LBK': ('18', '18.csv'), 'KVK': ('19', '19.csv')}

        self.int_nan = -99999
        self.cache = dict()

    def download_data(self):
        if not os.path.exists(self.folder):
            os.mkdir(self.folder)
        s = requests.session()
        doc = s.get('https://ehw.fit.vutbr.cz/izv/', headers=self.header).text
        soup = BeautifulSoup(doc, 'html.parser')
        zip_names = [item.get('href') for item in soup.find_all("a", {"class": "btn btn-sm btn-primary"})]
        for name in zip_names:
            r = s.get(f'https://ehw.fit.vutbr.cz/izv/{name}', headers=self.header)
            with ZipFile(BytesIO(r.content)) as zfile:
                zfile.extractall(f'{self.folder}/{name.split("/")[-1].split(".")[0]}')

            # with open(f'{self.folder}/{name.split("/")[-1]}', "wb") as f:
        #     f.write(r.content)

    def parse_region_data(self, region):
        data_matrix = []
        col_head = COLUMN_HEADER.copy()
        col_head.insert(0, region)

        reg_code = self.region_codes.get(region)[0]
        csv_file = self.region_codes.get(region)[1]


        for csv_path in glob.glob(self.folder + '/*/*.csv'):
            if csv_file == csv_path.split("/")[-1]:
                with open(csv_path, "r", encoding='ISO-8859-2') as f:
                    csv_r = csv.reader(f, delimiter=';', quotechar='"')
                    for row in csv_r:
                        data = row[0:45] + row[47:49] + [row[-1].replace("\n", "")]

                        data = [self.int_nan if x == '' else x for x in data]  # set empty values to nan
                        data = self.format_line(data, reg_code)
                        #data = np.array(data)

                        data_matrix.append(data)
                    #    print(f'{region}:{csv_file.replace(".csv", "")}'
        data = np.vstack(data_matrix).T
        # XX year of manufacture set to my 'nan'
        i = col_head.index('p47')
        data[i][data[i] == 'XX'] = self.int_nan



        # format hours
        i = col_head.index('p2b-hour')
        data[i][data[i] == '25'] = self.int_nan
       # data[i] = data[i].astype(int)

        # format minutes
        i = col_head.index('p2b-minute')
        data[i][data[i] == '60'] = self.int_nan
        #data[i] = data[i].astype(int)


        """
        i = col_head.index('p2a')


        data[:i] = data[:i].astype(int)
        data[i+1:d] = data[i+1:d].astype(int)
        # change gps coordinates to floats
        d = col_head.index('d')
        data[d] = data[d].astype(float)
        data[d+1] = data[d+1].astype(float)

        data[-1] = data[-1].astype(int)
        """
        data_list = []

        for i in range(data.shape[0]):
            try:
                data_list.append(data[i].astype(int))
            except ValueError:
                pass



        #print(data.shape)
        #print(len(data_list))



        """
        for zip_file in glob.glob(self.folder + '/*.zip'):
            with ZipFile(zip_file) as zf:
                with zf.open(self.region_codes.get(region)[1], "r") as csv_raw:
                    csv_wrap = TextIOWrapper(csv_raw, encoding='ISO-8859-2')
                    csv_r = csv.reader(csv_wrap, delimiter=';', quotechar='"')
                    for row in csv_r:
                        # get rid of redundant data: p1-p58 + [d,e] + p5a
                        data = row[0:45] + row[47:49] + [row[-1].replace("\n", "")]

                        data = [self.int_nan if x == '' else x for x in data]  # set empty values to nan
                        data = self.format_line(data, reg_code)
                        data_matrix.append(data)

        data = np.vstack(data_matrix).T
        data_list = []
        for i in range(data.shape[0]):
            data_list.append(data[i])
        """
        return col_head, data_list



    def format_line(self, data, region_number):
        # time formatting
        time = data[5]
        del data[5]  # delete old time
        #data.insert(5, (lambda x: x if int(x) < 25 else self.int_nan)(time[:2]))  # hours if
        #data.insert(6, (lambda x: x if int(x) < 60 else self.int_nan)(time[2:]))  # minutes
        data.insert(5, int(time[:2]))  # hours if
        data.insert(6, (time[2:]))  # minutes
        #print(data[5])
        # gps change for float dtype
        if data[-3] != self.int_nan:
            data[-3] = data[-3].replace(',', '.')
        if data[-2] != self.int_nan:
            data[-2] = data[-2].replace(',', '.')
        data[-2] = float(data[-2])
        data[-3] = float(data[-3])
        """
        # GPS formatting
        # if gps coordinates are not known they are set to -99999
        if data[-3] == self.int_nan:
            d = [self.int_nan, self.int_nan]
        # if gps coordinates does not include ',' therefore split produces only 1 number add '0' as number after ','
        else:
            d = data[-3].split(",")
            d = d if len(d) == 2 else [*d, 0]

        if data[-2] == self.int_nan:
            e = [self.int_nan, self.int_nan]
        else:
            e = data[-2].split(",")
            e = e if len(e) == 2 else [*e, 0]

        # delete both old gps coordinates
        del data[-2]
        del data[-2]
        # insert spliced gps back
        data = data[:-1] + d + e + list(data[-1])

        # date formatting
        date = data[3].split("-")  # split date into [year, month, day]
        del data[3]
        # insert date back into list
        data = data[:3]+date+data[3:]

        
        # XX year of manufacture set to my 'nan'
        if data[-16] == 'XX':
            data[-16] = self.int_nan
        """
        data.insert(0, int(region_number))
        return np.array(data)

    def get_list(self, regions=None):
        pass


if __name__ == "__main__":
    a = DataDownloader()
    # a.download_data()
    a.parse_region_data('PHA')
