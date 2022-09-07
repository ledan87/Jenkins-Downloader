import requests
from lxml import html
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

import pickle

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

browser = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=chrome_options)

#get the innerhtml from the rendered page

#Now use lxml to parse the page


# response = requests.get('https://plugins.jenkins.io/pipeline-model-definition/#dependencies')
# tree = html.fromstring(response.content)

cache = {}

class JenkinsDependency: 
    def __init__(self, name, minVersion, link, driver, depth=0):
        self.name = name
        self.minVersion = minVersion
        self.link = link
        self.depth = depth
        self.dependencies = []
        self.retrieve_dependencies(driver)
        self.retrieve_downloadLink(driver)
        cache[self.name] = self
    
    def retrieve_dependencies(self, driver):
        print(f"parsing {self.link}#dependencies")
        driver.get(self.link + "#dependencies")
        delay = 3 # seconds
        innerHTML = browser.page_source
        tree = html.fromstring(innerHTML)
        for e in tree.xpath('//*[@class="implied"]/a'):
            name = e.text.split("≥")[0].strip()
            minVersion = e.text.split("≥")[1].strip()
            link = "https://plugins.jenkins.io" + e.attrib['href']
            self.dependencies.append(JenkinsDependency(name, minVersion, link, driver, self.depth + 1))

    def retrieve_downloadLink(self, driver):
        print(f"parsing {self.link}#releases")
        driver.get(self.link+"#releases")
        delay = 3 # seconds
        innerHTML = browser.page_source
        tree = html.fromstring(innerHTML)
        for e in tree.xpath('//*[@class="item card"]'):
            self.version = e.xpath('div[@class="card-header"]/h5/div/a')[0].text
            self.downloadLink = e.xpath('div[@class="card-body"]/div/ul/li/a')[0].attrib['href']
            break
        

    def __str__(self):
        id = self.depth * "    " + f"{self.name} ≥ {self.minVersion} [{self.link}]"
        if(len(self.dependencies) > 0):
            return id +"\n" +"\n".join(map(str, self.dependencies))
        else:
            return id

def loadFromeWeb():

    initial = JenkinsDependency("Pipeline: Declarative", "2.2114.v2654ca_721309", "https://plugins.jenkins.io/pipeline-model-definition/", browser)

    with open("results.pickle","wb") as file:
        pickle.dump(initial, file)

    print(initial)

def loadFromPickle():
    obj = None
    with open('results.pickle', "rb") as f:
        obj = pickle.load(f)
    print(obj)

loadFromPickle()

