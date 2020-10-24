from io import BytesIO

import requests
from zipfile import ZipFile
import requests
from bs4 import BeautifulSoup

HEADER = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:82.0) Gecko/20100101 Firefox/82.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Referer': 'https://ehw.fit.vutbr.cz/izv/',
    'Upgrade-Insecure-Requests': '1',
}


class DataDownloader:
    def __init__(self, url='https://ehw.fit.vutbr.cz/izv/', folder='data', cache_filename='data_{}.pkl.gz',
                 header=None):
        if header is None:
            self.header = HEADER
        self.url = url
        self.folder = folder
        self.cache_file = cache_filename

    def download_data(self):
        s = requests.session()
        doc = s.get('https://ehw.fit.vutbr.cz/izv/', headers=self.header).text
        soup = BeautifulSoup(doc, 'html.parser')
        zip_names = [item.get('href') for item in soup.find_all("a", {"class": "btn btn-sm btn-primary"})]
        for name in zip_names:
            r = s.get(f'https://ehw.fit.vutbr.cz/izv/{name}', headers=self.header)
            with ZipFile(BytesIO(r.content)) as zfile:
                zfile.extractall(f'./{self.folder}/{name.split("/")[-1].split(".")[0]}')

    def parse_region_data(self, region):
        pass

    def get_list(self, regions=None):
        pass

    def read(self):
        with open('./00.csv', "r", encoding="ISO-8859-1") as f:
            print(f.read())

if __name__ == "__main__":
    print('hello world')
    a = DataDownloader()
    a.download_data()
    a.read()
    print(a.cache_file)
