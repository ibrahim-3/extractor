from bs4 import BeautifulSoup
from bs4.element import Tag
import re
import requests
import chardet
import heapq


def encode_detect(text):
    """检测文本的编码类型
    """
    encoding = chardet.detect(text)
    return encoding['encoding']


def remove_control_characters(text):
    RE_XML_ILLEGAL = u'([\u0000-\u0008\u000b-\u000c\u000e-\u001f\ufffe-\uffff])' + \
                     u'|' + \
                     u'([%s-%s][^%s-%s])|([^%s-%s][%s-%s])|([%s-%s]$)|(^[%s-%s])' % \
                     (chr(0xd800), chr(0xdbff), chr(0xdc00), chr(0xdfff),
                      chr(0xd800), chr(0xdbff), chr(0xdc00), chr(0xdfff),
                      chr(0xd800), chr(0xdbff), chr(0xdc00), chr(0xdfff),
                      ) + \
                     u'|\u3000'
    text = re.sub(RE_XML_ILLEGAL, "", text)
    text = re.sub(r"[\x01-\x1F\x7F]", "", text)
    return text



class Paragraph(object):

    def __init__(self, id, pid, element):
        self.id = id
        self.pid = pid
        self.element = element

    @property
    def length(self):
        return len(self.element.get_text())

    @property
    def text(self):
        return remove_control_characters(self.element.get_text())

    @property
    def density(self):
        return self.length / (len(self.element.encode().decode()) * 1.0)

    def __lt__(self, other):
        print(self.id, other.id)
        return self.id < other.id


class Section(object):

    def __init__(self, id):
        self.id = id
        self.paragraphs = []
        self._length = 0
        self.length = 0

    def add_paragraph(self, paragraph, add=True):
        self.paragraphs.append(paragraph)
        if add:
            self._length += len(paragraph.text)
        self.length += len(paragraph.text)

    @property
    def ordered_paragraphs(self):
        return sorted(self.paragraphs, key=lambda p: p.id, reverse=False)

    @property
    def text(self):
        text = ''
        for paragraph in self.paragraphs:
            text += paragraph.text
        return text


class Article(object):

    def __init__(self):
        self.sections = []
        self.paragraph_ids = []

    def add_paragraph(self, pid, paragraph, add=True):
        section = self._find_section(pid)
        flag = False
        if section is None:
            flag = True
            section = Section(pid)
        section.add_paragraph(paragraph, add)
        if flag:
            self.sections.append(section)

        self.paragraph_ids.append(paragraph.id)

    def add_others(self, pid, paragraph):
        if not self.is_existed(pid):
            return

        if paragraph.id not in self.paragraph_ids:
            self.add_paragraph(pid, paragraph, add=False)

    def _find_section(self, id):
        for section in self.sections:
            if id == section.id:
                return section

        return None

    def is_existed(self, id):
        for section in self.sections:
            if section.id == id:
                return True
        return False

    @property
    def content(self):
        sections = sorted(self.sections, key=lambda section: section._length, reverse=True)
        return sections[0]

    def print_sections(self):
        for section in self.sections:
            print('section', section.length)
            for paragraph in section.paragraphs:
                print(paragraph.id, paragraph.text, paragraph.density)


class ArticleExtractor(object):
    EXCLUDED_TAGS = ['script', 'style', 'iframe']

    def __init__(self, html_raw):
        self.soup = BeautifulSoup(html_raw, 'html5lib', from_encoding=encode_detect(html_raw))
        self.elements = self._traverse()
        self.article = Article()
        self._clean()

    def _clean(self):
        """清理html文档中的冗余数据"""
        for element in self.soup(self.EXCLUDED_TAGS):
            element.decompose()

    def _traverse(self):
        """遍历整个html文档"""
        elements = []
        stack = [(self.soup, 0)]
        element_id = 0
        while len(stack):
            element, pid = stack.pop(0)

            if not isinstance(element, Tag):
                continue

            element_id += 1
            elements.append((element_id, pid, element))

            for child_element in element.children:
                if isinstance(child_element, Tag):
                    stack.append((child_element, element_id))

        return elements

    def _build_paragraphs(self):
        for id, pid, element in self.elements:
            if element.name == 'p':
                self.article.add_paragraph(pid, Paragraph(id, pid, element))

    def _complete_article(self):
        for id, pid, element in self.elements:
            self.article.add_others(pid, Paragraph(id, pid, element))

if __name__ == '__main__':
    url = 'http://tech.sina.com.cn/i/2017-10-18/doc-ifymviyp2139855.shtml'
    response = requests.get(url)
    extractor = ArticleExtractor(response.content)
    extractor._build_paragraphs()
    extractor._complete_article()
    # extractor.article.print_sections()
    section = extractor.article.content
    for paragraph in section.ordered_paragraphs:
        print(paragraph.id, paragraph.text, paragraph.density)