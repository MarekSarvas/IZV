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

C = ['p1', 'p36', 'p37', 'p2a', 'weekday(p2a)', 'p2b-hour', 'p2b-minute', 'p6', 'p7', 'p8', 'p9', 'p10', 'p11', 'p12',
     'p13a', 'p13b',
     'p13c', 'p14', 'p15', 'p16', 'p17', 'p18', 'p19', 'p20', 'p21', 'p22', 'p23', 'p24', 'p27', 'p28', 'p34', 'p35',
     'p39', 'p44', 'p45a', 'p47', 'p48a', 'p49', 'p50a', 'p50b', 'p51', 'p52', 'p53', 'p55a', 'p57', 'p58', 'a', 'b',
     'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'n', 'o', 'p', 'q', 'r', 's', 't', 'p5a']
C_LEN = 65
strings = [0, 3, 63, 60, 59, 56, 55, 52, 53, 57]
floats = [51, 50, 49, 48, 46, 47]
ints = [1,2,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,
        41,42,43,44,45,54,57,58,61,62,63,64]

class DataDownloader:
    def __init__(self, url='https://ehw.fit.vutbr.cz/izv/', folder='dataz', cache_filename='data_{}.pkl.gz',
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

    def parse_region_data(self, region):
        data_list = []
        finale_data = []

        reg_code = self.region_codes.get(region)[0]
        csv_file = self.region_codes.get(region)[1]
        dat2 = []
        rows = 0
        for zip_file in glob.glob(self.folder + '/*.zip'):
            with ZipFile(zip_file) as zf:
                with zf.open(self.region_codes.get(region)[1], "r") as csv_raw:
                    csv_wrap = TextIOWrapper(csv_raw, encoding='ISO-8859-2')
                    csv_r = csv.reader(csv_wrap, delimiter=';', quotechar='"')



 #       for csv_path in glob.glob(self.folder + '/*/*.csv'):
  #          if csv_file == csv_path.split("/")[-1]:
  #              with open(csv_path, "r", encoding='ISO-8859-2') as f:
  #                  csv_r = csv.reader(f, delimiter=';', quotechar='"')

                    rows = len(list(csv_r))
                    csv_raw.seek(0)

                    for r in range(C_LEN):
                        if r in strings:
                            data_list.append(np.empty(rows, dtype='<U32'))
                        elif r in floats:
                            data_list.append(np.empty(rows, dtype=float))
                        else:
                            data_list.append(np.empty(rows, dtype=int))
                    tmp = np.empty(rows, dtype='<U3')
                    tmp[:] = region
                    current_row = 0
                    for row in csv_r:
                        # self.format_line(row, data_list, current_row)
                        self.format_line2(row, data_list, current_row)
                        #dat2.append(row.copy())
                        current_row += 1
                data_list.insert(0, tmp.copy())

                if not finale_data:
                    finale_data = data_list.copy()
                else:
                    for i in range(C_LEN):
                        finale_data[i] = np.concatenate((finale_data[i], data_list[i]))

                data_list = []
        """
        dat2 = np.array(dat2)
        
        for r in range(C_LEN):
            if r in strings:
                a = np.empty(rows, dtype='<U32')
            elif r in floats:
                a = np.empty(rows, dtype=float)
            else:
                a = np.empty(rows, dtype=int)

            a[:] = dat2[:, r]
            data_list.append(a.copy())
        """
        #print(len(data_list))
        #print(data_list[0].shape)
        #return data_list
        print(len(finale_data))
        print(finale_data[0].shape)
        # return col_head, data_list

    def format_line(self, data, data_list, j):
        data.insert(6, self.int_nan)  # placeholder cause time is changed from
        time = data[5]
        for i in range(C_LEN):
            if i == 5:
                data_list[i][j] = (lambda x: x if int(x) < 25 else self.int_nan)(time[:2])
            elif i == 6:
                data_list[i][j] = (lambda x: x if int(x) < 25 else self.int_nan)(time[2:])
            elif i in floats:
                try:
                    data_list[i][j] = data[i].replace(',', '.')
                except ValueError:
                    data_list[i][j] = self.int_nan
            elif i in strings:
                data_list[i][j] = data[i]
            else:
                try:
                    data_list[i][j] = data[i]
                except ValueError:
                    data_list[i][j] = self.int_nan

        return 1

    def format_line2(self, data, data_list, j):
        data.insert(6, self.int_nan)  # placeholder cause time is changed from
        time = data[5]
        data_list[5][j] = (lambda x: x if int(x) < 25 else self.int_nan)(time[:2])
        data_list[6][j] = (lambda x: x if int(x) < 25 else self.int_nan)(time[2:])
        for i in floats:
            try:
                data_list[i][j] = data[i].replace(',', '.')
            except ValueError:
                data_list[i][j] = self.int_nan
        for i in ints:
            #print(i, j)
            try:

                #print(len(data))
                #a = data[i]
               # #print(len(data))
                #print("FUCK")
               # b = [data_list[i][j]]
                data_list[i][j] = data[i]
            except ValueError:
                data_list[i][j] = self.int_nan

        return 1


    def get_list(self, regions=None):
        if not regions:
            for k, v in self.region_codes.items():
                self.parse_region_data(k)
        else:
            self.parse_region_data(regions)

if __name__ == "__main__":
    a = DataDownloader()
    # a.download_data()
    a.get_list()
