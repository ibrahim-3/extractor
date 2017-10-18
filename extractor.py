from bs4 import BeautifulSoup
from bs4.element import Tag
import chardet
import re


def encode_detect(text):
    """检测文本的编码类型
    """
    encoding = chardet.detect(text)
    return encoding['encoding']


def remove_control_characters(text):
    """删除控制字符"""
    RE_ILLEGAL = u'([\u0000-\u0008\u000b-\u000c\u000e-\u001f\ufffe-\uffff])' + \
                     u'|' + \
                     u'([%s-%s][^%s-%s])|([^%s-%s][%s-%s])|([%s-%s]$)|(^[%s-%s])' % \
                     (chr(0xd800), chr(0xdbff), chr(0xdc00), chr(0xdfff),
                      chr(0xd800), chr(0xdbff), chr(0xdc00), chr(0xdfff),
                      chr(0xd800), chr(0xdbff), chr(0xdc00), chr(0xdfff),
                      ) + \
                     u'|\u3000'
    text = re.sub(RE_ILLEGAL, "", text)
    text = re.sub(r"[\x01-\x1F\x7F]", "", text)
    return text


class Paragraph(object):

    def __init__(self, id, pid, element):
        self.id = id
        self.pid = pid
        self.element = element
        self.text = remove_control_characters(self.element.get_text())

    @property
    def length(self):
        return len(self.text)


class Section(object):

    def __init__(self, id):
        self.id = id
        self.paragraphs = []

    @property
    def length(self):
        return sum([paragraph.length for paragraph in self.paragraphs])

    def has_paragraph(self, id):
        for paragraph in self.paragraphs:
            if paragraph.id == id:
                return True
        return False


class Article(object):
    EXCLUDED_TAGS = ['script', 'style', 'iframe']

    def __init__(self, html_raw):
        self.soup = BeautifulSoup(
            html_raw,
            'html5lib',
            from_encoding=encode_detect(html_raw)
        )
        self.sections = []
        self.paragraphs = []
        self.elements = []
        self.content = None
        self._clean()
        self._find_element_p()
        self._find_paragraphs()
        self._find_sections()
        self._find_content()

    def _find_element_p(self):
        """找到所有的p标签"""
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

        self.elements = elements

    def _find_paragraphs(self):
        """找到所有的Paragraph"""
        for id, pid, element in self.elements:
            if element.name == 'p':
                self.paragraphs.append(Paragraph(id, pid, element))

    def _find_sections(self):
        """找到所有的Section"""
        for paragraph in self.paragraphs:
            section = self._find_section_by_paragraph(paragraph)
            section.paragraphs.append(paragraph)

    def _find_content(self):
        """找到正文"""
        ordered_sections = sorted(self.sections, key=lambda s: s.length, reverse=True)
        self.content = ordered_sections[0]

    @property
    def text(self):
        for paragraph in self.paragraphs:
            if paragraph.pid == self.content.id and \
                    not self.content.has_paragraph(paragraph.id):
                self.content.paragraphs(paragraph)

        ordered_paragraphs = sorted(
            self.content.paragraphs,
            key=lambda p: p.id
        )

        return "\n".join([paragraph.text for paragraph in ordered_paragraphs])


    def _clean(self):
        """清理html文档中的冗余数据"""
        for element in self.soup(self.EXCLUDED_TAGS):
            element.decompose()

    def _find_section_by_paragraph(self, paragraph):
        for section in self.sections:
            if section.id == paragraph.pid:
                return section

        section = Section(paragraph.pid)
        self.sections.append(section)
        return section


if __name__ == '__main__':
    url = 'http://finance.sina.com.cn/china/gncj/2017-10-18/doc-ifymviyp2242742.shtml'
    import requests
    response = requests.get(url)
    article = Article(response.content)
    print(article.text)