"""
    extractor
    ~~~~~~~~

    A simple html extractor.

"""
from bs4 import BeautifulSoup
from bs4.element import Tag

EXCLUDE_TAGS = ['script', 'style', 'iframe', 'noscript', 'link', 'meta', 'ins']


def remove_excluded_tags(soup, exclude_tags=None):
    """Remove excluded tags"""
    if not exclude_tags:
        exclude_tags = EXCLUDE_TAGS

    for tag in soup(exclude_tags):
        tag.decompose()


def group_tags(soup):
    """Extract all tags from html document"""
    remove_excluded_tags(soup)
    stack = [soup]
    while len(stack):
        element = stack.pop()

        children = []
        for child_element in element.children:
            if isinstance(child_element, Tag):
                stack.append(child_element)
                children.append(child_element)
        if children:
            yield children


def sort_groups(groups):
    return sorted(groups, key=lambda g: len(g), reverse=True)


if __name__ == '__main__':
    import requests
    url = 'http://mp.weixin.qq.com/s?src=11&timestamp=1510758727&ver=516&signature=J7-OMfiyT0zc15gCpJdDSJghTBV9Ids-k0Ycn0hptRZjZ9csW1nl3AuZECh7xVe1fAdwUje*dylfmFXvv2hB43isYUuGrB*IuumggGGluuSsfhD97fkZcXxbDboj3scc&new=1'
    resp = requests.get(url)
    soup = BeautifulSoup(resp.content, 'html5lib')
    for g in sort_groups(group_tags(soup)):
        print(list(map(lambda x: x.name, g)))
