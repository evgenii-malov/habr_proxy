# proxy server
Asynchronous proxy server implemented with tornado which add to words with length 6 ™ sign.
Also it do some text processing in separate process to avoid IO loop block.
Separate text processing implemented via futures lib https://pypi.python.org/pypi/futures (process pool).
