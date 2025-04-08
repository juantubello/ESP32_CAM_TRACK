import usocket

def request(method, url, data=None, json=None, headers={}, stream=None):
    try:
        proto, dummy, host, path = url.split('/', 3)
    except ValueError:
        proto, dummy, host = url.split('/', 2)
        path = ''
    if proto == 'http:':
        port = 80
    else:
        raise OSError('Unsupported protocol: ' + proto)

    if ':' in host:
        host, port = host.split(':', 1)
        port = int(port)

    ai = usocket.getaddrinfo(host, port)
    addr = ai[0][-1]
    s = usocket.socket()
    s.connect(addr)
    s.write(b"%s /%s HTTP/1.0\r\n" % (method, path))
    if not 'Host' in headers:
        s.write(b"Host: %s\r\n" % host.encode())
    for k in headers:
        s.write(k.encode() + b": " + headers[k].encode() + b"\r\n")
    if json is not None:
        assert data is None
        import ujson
        data = ujson.dumps(json)
        s.write(b"Content-Type: application/json\r\n")
    if data:
        s.write(b"Content-Length: %d\r\n" % len(data))
    s.write(b"\r\n")
    if data:
        s.write(data)

    l = s.readline()
    protover, status, msg = l.split(None, 2)
    status = int(status)
    while True:
        l = s.readline()
        if not l or l == b"\r\n":
            break
        # ignore headers

    class Response:
        def __init__(self, s):
            self.raw = s
            self.encoding = "utf-8"
            self._cached = None

        def close(self):
            if self.raw:
                self.raw.close()
                self.raw = None
            self._cached = None

        @property
        def content(self):
            if self._cached is None:
                self._cached = self.raw.read()
                self.raw.close()
                self.raw = None
            return self._cached

        @property
        def text(self):
            return str(self.content, self.encoding)

        def json(self):
            import ujson
            return ujson.loads(self.content)

    return Response(s)

def get(url, **kw):
    return request("GET", url, **kw)

def post(url, **kw):
    return request("POST", url, **kw)

def put(url, **kw):
    return request("PUT", url, **kw)

def patch(url, **kw):
    return request("PATCH", url, **kw)

def delete(url, **kw):
    return request("DELETE", url, **kw)
