import socket
import ssl


def request(url):
    # Finds the scheme
    scheme, url = url.split("://", 1)
    assert scheme in ["http", "https"], \
        "Unknown scheme {}".format(scheme)

    # Get the host and the path
    host, path = url.split("/", 1)
    path = "/" + path

    # http => 80, https => 443
    port = 80 if scheme == "http" else 443

    if ":" in host:
        host, port = host.split(":", 1)
        port = int(port)

    # Create a socket
    s = socket.socket(
        family=socket.AF_INET,
        type=socket.SOCK_STREAM,
        proto=socket.IPPROTO_TCP,
    )

    # Connect to the socket
    s.connect((host, port))

    if scheme == "https":
        ctx = ssl.create_default_context()
        s = ctx.wrap_socket(s, server_hostname=host)

    # Python telnet to download the resource
    s.send("GET {} HTTP/1.1\r\n".format(path).encode("utf8") +
           "Host: {}\r\n".format(host).encode("utf8") +
           "Connection: {}\r\n".format("close").encode("utf8") +
           "User-Agent: {}\r\n\r\n".format("Toy Browser").encode("utf8"))

    # The response we got from the server
    response = s.makefile("r", encoding="utf8", newline="\r\n")

    statusline = response.readline()
    version, status, explanation = statusline.split(" ", 2)
    assert status == "200", "{}: {}".format(status, explanation)

    headers = {}
    while True:
        line = response.readline()
        if line == "\r\n":
            break
        header, value = line.split(":", 1)
        headers[header.lower()] = value.strip()

    assert "transfer-encoding" not in headers
    assert "content-encoding" not in headers

    body = response.read()
    s.close()

    return headers, body


def show(body):
    # Removes the tags and displays the rest
    in_angle = False
    for c in body:
        if c == "<":
            in_angle = True
        elif c == ">":
            in_angle = False
        elif not in_angle:
            print(c, end="")


def load(url):
    # This will download the resource from the remote server
    headers, body = request(url)
    show(body)


if __name__ == "__main__":
    import sys
    load(sys.argv[1])
