# These are necessary to avoid getting 403s
headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    # 'Accept-Encoding': 'gzip, deflate',
    'Referer': 'http://www.diva-portal.org/smash/resultList.jsf?dswid=-6166&language=sv&searchType=SUBJECT&query=&af=%5B%5D&aq=%5B%5B%7B%22categoryId%22%3A%2211649%22%7D%5D%5D&aq2=%5B%5B%5D%5D&aqe=%5B%5D&noOfRows=250&sortOrder=author_sort_asc&sortOrder2=title_sort_asc&onlyFullText=false&sf=all&p=4801',
    'DNT': '1',
    'Connection': 'keep-alive',
    # 'Cookie': 'JSESSIONID=J75dOWOOMkAhh6XXAIuVxAveod0Bo2t_8xD4RMIK.d29a719cc26d',
    'Upgrade-Insecure-Requests': '1',
}
