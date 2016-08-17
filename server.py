# encoding: utf-8
import tornado.ioloop
import tornado.web
from tornado import httpclient, gen
from lxml import etree
from traceback import format_exc
from concurrent.futures import ProcessPoolExecutor
from xml.sax.saxutils import unescape

SERVER_PORT = 8888
TAGS_TO_CHECK_TEXT_IN = (
    'p', 'span', 'div', 'li', 'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'br',
    'strong', 's', 'b', 'i', 'em', 'mark', 'small', 'del', 'ins', 'sub',
    'sup', 'blockquote', 'q')
ALLOW_LETTERS = u"""абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙК"
"ЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯabcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"""
STRIP_WORD_CHARS = u'!;,.?()[]"<>«»^'''


def process_word(w):
    sw = w.strip(STRIP_WORD_CHARS)
    if (len(sw) == 6 and all(c in ALLOW_LETTERS for c in sw)):
        return w.replace(sw, sw + u'™')
    return w


def process_text(str):
    if not isinstance(str, basestring):
        return str
    r = u" ".join((process_word(w) for w in str.split(" ")))
    return unescape(r, entities={'&plus;': '+'})


def process_html(html):
    root = etree.HTML(html, parser=etree.HTMLParser(encoding='utf-8'))

    for e in root.xpath('//body')[0].iterdescendants(*TAGS_TO_CHECK_TEXT_IN):
        try:
            e.attrib['href'] = e.attrib['href'].replace(
                'https://habrahabr.ru/', 'http://127.0.0.1:8888/')
        except KeyError:
            pass
        e.text = process_text(e.text)
        e.tail = process_text(e.tail)

    return etree.tostring(root, encoding='utf-8', method='html')


class MainHandler(tornado.web.RequestHandler):
    @gen.coroutine
    def get(self):
        try:
            print(self.request.uri)
            response = yield httpclient.AsyncHTTPClient().fetch(
                "https://habrahabr.ru{}".format(self.request.uri))
            if response.headers["Content-Type"] == 'text/html; charset=UTF-8':
                # CPU bound task - do it in separate process to avoid IO loop
                # block!
                fut = pool.submit(process_html, response.body)
                ret = yield fut
                self.write(ret)
            else:
                self.write(response.body)
        except Exception as e:
            self.write('Exception: %s' % format_exc(e))


def make_app():
    return tornado.web.Application([
        (r".*", MainHandler),
    ])


if __name__ == "__main__":
    app = make_app()
    app.listen(SERVER_PORT)
    pool = ProcessPoolExecutor()
    tornado.ioloop.IOLoop.current().start()
