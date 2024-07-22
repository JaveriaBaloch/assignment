# fetch_image.py
import requests
from bs4 import BeautifulSoup


def fetch_image_url(page_url):
    try:
        response = requests.get(page_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find the first image on the page
        img_tag = soup.find('img')
        if img_tag and img_tag.get('src'):
            return img_tag.get('src')
        return None
    except Exception as e:
        print(f"Error fetching image URL: {e}")
        return None
