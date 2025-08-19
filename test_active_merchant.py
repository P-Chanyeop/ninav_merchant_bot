import requests
from bs4 import BeautifulSoup

if __name__ == "__main__":
    url = "https://kloa.gg/merchant"
    
    res = requests.get(url)
    if res.status_code == 200:
        soup = BeautifulSoup(res.text, 'html.parser')
        merchats = soup.find_all('p', class_='rounded')
        
        print("Merchant found:", len(merchats))
        
    else:
        print("Merchant is not active.")