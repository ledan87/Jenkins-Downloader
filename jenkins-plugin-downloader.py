import requests
from zipfile import ZipFile
import os

links = filter(lambda x: x != "\n", open("plugins-to-download.txt"))
links = map(lambda x: x.replace("\n", ""), links)
links = list(links)

with ZipFile("jenkins-plugins.zip", "w") as zipFile:
    for url in links:
        file_name = os.path.basename(url)
        response = requests.get(url)
        open(file_name, "wb").write(response.content)
        zipFile.write(file_name)
        os.remove(file_name)
