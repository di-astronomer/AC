import requests
import hunspell
import gevent
import time
import config
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup


def main():
    settings = config.config('config.ini', 'settings')
    version = int(settings.get('version'))

    if version == 0:
        word_counter_asynchrone('data.xml', 'result.xml')
    elif version == 1:
        word_counter('data.xml', 'result.xml')
    elif version == 2:
        start = time.time()
        word_counter('data.xml', 'result.xml')
        end = time.time()
        print('1-thread: ' + str(end - start))
        start = time.time()
        word_counter_asynchrone('data.xml', 'result.xml')
        end = time.time()
        print('Parallel: ' + str(end - start))
    else:
        print('Wrong version')
        exit()


def word_counter(input_file_name, output_file_name):
    urls = get_urls_from_xml(input_file_name)
    data = ET.Element('data')

    for url in urls:
        data.append(get_word_freq_xml(url))

    output_file = open(output_file_name, 'w')
    output_file.write(ET.tostring(data).decode())
    output_file.close()


def word_counter_asynchrone(input_file_name, output_file_name):
    urls = get_urls_from_xml(input_file_name)
    data = ET.Element('data')

    threads = [gevent.spawn(get_word_freq_xml, url) for url in urls]
    gevent.joinall(threads)

    for thread in threads:
        data.append(thread.value)

    output_file = open(output_file_name, 'w')
    output_file.write(ET.tostring(data).decode())
    output_file.close()


def get_word_list(URL):
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, 'html.parser')
    word_list = []

    for p_tag in soup.find_all('p'):
        for word in p_tag.get_text().split():
            word_list.append(word.lower())

    return word_list


def check_word(word_list):
    spellchecker = hunspell.HunSpell('/usr/share/hunspell/uk_UA.dic',
                                     '/usr/share/hunspell/uk_UA.aff')
    result = []

    for i in range(len(word_list)):
        if spellchecker.stem(word_list[i]):
            result.append(spellchecker.stem(word_list[i])[0].decode())

    return result


def get_word_freq(url):
    word_list = get_word_list(url)
    word_list = check_word(word_list)
    word_freq = [word_list.count(p) for p in word_list]
    return dict(list(zip(word_list, word_freq)))


def get_word_freq_xml(url):
    word_list = get_word_list(url)
    word_list = check_word(word_list)
    word_freq = [word_list.count(p) for p in word_list]
    return url_word_freq_to_xml(dict(list(zip(word_list, word_freq))), url)


def url_word_freq_to_xml(word_freq, url):
    url_tag = ET.Element('url')
    url_tag.text = url
    words = ET.SubElement(url_tag, 'words')
    for item in word_freq:
        word = ET.SubElement(words, 'word')
        word.set('name', item)
        word.text = str(word_freq[item])

    return url_tag


def get_urls_from_xml(file_name):
    urls = []

    tree = ET.parse(file_name)
    root = tree.getroot()

    for elem in root:
        for subelem in elem:
            urls.append(subelem.text)

    return urls


if __name__ == "__main__":
    main()