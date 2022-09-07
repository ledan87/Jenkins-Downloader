import requests
from lxml import html
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

import pickle

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')


#get the innerhtml from the rendered page

#Now use lxml to parse the page


# response = requests.get('https://plugins.jenkins.io/pipeline-model-definition/#dependencies')
# tree = html.fromstring(response.content)

cache = {}

class JenkinsDependency: 
    def __init__(self, name, minVersion, link, driver, depth=0, depNames=[]):
        self.name = name
        self.minVersion = minVersion
        self.link = link
        self.depth = depth
        self.depNames = depNames
        self.dependencies = []
        if name in cache:
            print(self.depth * "  " +  f"cache {name}")
            cached = cache[name]
            self.version = cached.version
            self.dependencies = cached.dependencies
        else:
                self.version, self.dependencies = self.retrieve_dependencies(driver)
                cache[self.name] = self
    
    def retrieve_dependencies(self, driver):
        print(self.depth * "  " +  f"parsing {self.link}#dependencies")
        driver.get(self.link + "#dependencies")
        import time 
        time.sleep(2)
        innerHTML = driver.page_source
        tree = html.fromstring(innerHTML)
        self.version = tree.xpath('//*[@class="col-md-3 sidebar"]/h5')[0].text.split("Version: ")[1]
        for e in tree.xpath('//*[@class="implied"]/a'):
            name = e.text.split("≥")[0].strip()
            minVersion = e.text.split("≥")[1].strip()
            link = "https://plugins.jenkins.io" + e.attrib['href']
            deps = self.depNames.copy()
            deps.append(self.name)
            if(name not in self.depNames):
                self.dependencies.append(JenkinsDependency(name, minVersion, link, driver, self.depth + 1, deps))
        return (self.version, self.dependencies)

    def retrieve_downloadLink(self, driver):
        print(f"parsing {self.link}#releases")
        driver.get(self.link+"#dependencies")
        import time 
        time.sleep(2)

        innerHTML = driver.page_source
        tree = html.fromstring(innerHTML)
        self.version = tree.xpath('//*[@class="col-md-3 sidebar"]/h5')[0].text.split("Version: ")[1]
        print(self.version)
        # self.version = e.xpath('div[@class="card-header"]/h5/div/a')[0].text
        # self.downloadLink = e.xpath('div[@class="card-body"]/div/ul/li/a')[0].attrib['href']

    def get_dependencies(self):
        depList = []
        for dependency in self.dependencies:
            depList.append(dependency.get_download_link())
        for dependency in self.dependencies:
            for d in dependency.get_dependencies():
                if(d not in depList):
                    depList.append(d)
        return depList

    def get_download_link(self):
        id = self.link.split("/")[-2]
        return f"https://updates.jenkins.io/download/plugins/{id}/{self.version}/{id}.hpi"

    def __str__(self):
        id = self.depth * "    " + f"{self.name} ≥ {self.version} [{self.link}]"
        if(len(self.dependencies) > 0):
            return id +"\n" +"\n".join(map(str, self.dependencies))
        else:
            return id

def loadFromWeb():
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    initial = JenkinsDependency("Pipeline", "", "https://plugins.jenkins.io/workflow-aggregator/", driver)

    with open("results.pickle","wb") as file:
        pickle.dump(initial, file)

    print(initial)
    driver.close()

def loadFromPickle():
    obj: JenkinsDependency = None
    with open('results.pickle', "rb") as f:
        obj = pickle.load(f)
    with open("plugins-to-download.txt", "w") as f:
        [f.write(d+"\n") for d in obj.get_dependencies()]
        
loadFromPickle()
