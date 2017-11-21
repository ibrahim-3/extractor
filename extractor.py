"""
    extractor
    ~~~~~~~~

    A simple html extractor.

"""
from functools import reduce
from bs4 import BeautifulSoup
from bs4.element import Tag
import re


EXCLUDE_TAGS = ['script', 'style', 'iframe', 'noscript', 'link', 'meta', 'ins']


def assoc(d, key, value):
    d[key] = value
    return d


def call(fn, key, source=None):
    def apply_fn(record):
        _key = source or key
        return assoc(record, key, fn(record.get(_key)))
    return apply_fn


def pipeline_each(data, fns):
    return reduce(
        lambda a, x: map(x, a),
        fns,
        data)


def encode_to_utf8(nbytes):
    import chardet
    res = chardet.detect(nbytes)
    print(res)
    _encode = res['encoding']
    if _encode != 'utf-8':
        nbytes.decode(_encode, 'ignore').encode('utf-8')
    return nbytes


def remove_excluded_tags(soup, exclude_tags=None):
    """Remove excluded tags"""
    if not exclude_tags:
        exclude_tags = EXCLUDE_TAGS

    for tag in soup(exclude_tags):
        tag.decompose()


def extract_groups(soup, url=None):
    """Extract all tags from html document"""
    stack = [soup]
    groups = []
    while len(stack):
        element = stack.pop()

        children = []
        for child_element in element.children:
            if isinstance(child_element, Tag):
                stack.append(child_element)
                children.append(child_element)
        if children:
            groups.append({
                'elements': children,
                'tags': list(map(lambda ele: ele.name, children)),
                'images': list(filter(lambda ele: ele.name == 'img', children))
            })
    return groups


def extract_content(soup):
    groups = extract_groups(soup)
    results = pipeline_each(groups, [
        call(
            lambda elements: reduce(
                lambda a, ele: a + len(ele.get_text()) if ele.name == 'p' else 0,
                elements,
                0
            ),
            'length',
            'elements'),
        call(
            lambda elements: reduce(
                lambda a, ele: a + ele.encode().decode(),
                elements,
                ''
            ),
            'html',
            'elements'
        )
    ])
    sorted_results = sorted(results, key=lambda x: x['length'], reverse=True)
    if len(sorted_results):
        return sorted_results[0]['html']
    return ''


def extract_title(soup):
    title_element = soup.find('title')
    title = title_element.get_text()
    title = re.split('_|——|\|', title)[0].strip()
    return title


if __name__ == '__main__':
    import requests
    import chardet
    url = 'http://hot.cnbeta.com/articles/movie/670795.htm'
    resp = requests.get(url)
    soup = BeautifulSoup(resp.content, 'html5lib')
    remove_excluded_tags(soup)
    content = extract_content(soup)
    title = extract_title(soup)
    print(title)
    print(content)
