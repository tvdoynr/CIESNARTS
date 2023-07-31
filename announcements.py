import urllib.parse

import requests
from bs4 import BeautifulSoup
from requests.packages.urllib3.exceptions import InsecureRequestWarning


requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

url = "https://cs.hacettepe.edu.tr/json/announcements.json"
json_data = requests.get(url, verify=False).json()[:15]


def cleanup(str_: str) -> str:
    if len(str_) == 0 or str_ == "\n":
        return ""

    chars = list(str_)
    i = 0
    while i < len(chars):
        if chars[i] == "\n":
            j = i
            while j < len(chars) and chars[j] == "\n":
                j += 1
            if j - i > 1:
                chars[i] = ""
                chars[i + 1] = ""
            else:
                chars[i] = " "
            i = j
        i += 1
    return "".join(chars)


def _complete_url(url: str) -> str:
    url = urllib.parse.quote(url, "\./_-:=?%")
    address = "https://www.cs.hacettepe.edu.tr"

    if url[:4] == 'http' or url[:3] == 'www':
        return url
    if url[0] != '/':
        url = '/' + url

    return address + url


def get_announcements():
    new_announcements: list[dict] = []

    for document in json_data:
        body: BeautifulSoup = BeautifulSoup(document['body'], 'lxml')
        title: str = document['title']
        content = body.get_text("\n").replace("\r\n", "\n")  # CRLF to LF
        content = cleanup(content)

        try:
            url = _complete_url(body.find('a').get('href'))
        except AttributeError:
            url = None

        announcement = {'title': title, 'content': content, 'url': url}
        new_announcements.append(announcement)

    return new_announcements
