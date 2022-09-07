import requests
response = requests.get('https://plugins.jenkins.io/pipeline-model-definition/#dependencies')
print (response.content)