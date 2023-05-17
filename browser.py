import socket
import ssl
import gzip
from json import dumps


def request_remote_resource(path: str, scheme: str, host: str, num_of_reqs=5):
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

    # Send the HTTP request
    s.send("GET {} HTTP/1.1\r\n".format(path).encode("utf8") +
           "Host: {}\r\n".format(host).encode("utf8") +
           "Connection: {}\r\n".format("close").encode("utf8") +
           "User-Agent: {}\r\n".format("Toy Browser").encode("utf8") +
           "Accept-Encoding: {}\r\n\r\n".format("gzip").encode("utf8"))

    # The response we got from the server
    response = s.makefile("rb")

    # Check if the response is compressed
    is_compressed = False
    headers = {}
    while True:
        line = response.readline()
        if line == b"\r\n" or line == b"\n":
            break
        header = line.decode("utf8").rstrip("\r\n").split(":", 1)
        if len(header) == 2:
            headers[header[0]] = header[1].strip()
        else:
            statusline = header[0]
        if line.startswith(b"Content-Encoding:") and b"gzip" in line:
            is_compressed = True

    is_chunked = False
    try:
        if headers["Transfer-Encoding"] == "chunked":
            is_chunked = True
    except KeyError:
        is_chunked = False

    if is_chunked and is_compressed:
        decompressed_data = b""
        while True:
            # Read the chunk size line
            chunk_size_line = response.readline().strip()
            if not chunk_size_line:
                break
            chunk_size = int(chunk_size_line, 16)

            # Read the chunk
            chunk = response.read(chunk_size)

            # Decompress the chunk using gzip
            decompressed_chunk = gzip.decompress(chunk)
            decompressed_data += decompressed_chunk

            # Consume the trailing CRLF after the chunk
            response.readline()

        content = decompressed_data
    elif is_compressed:
        decompressed_data = gzip.GzipFile(fileobj=response)
        content = decompressed_data.read(1024)
    else:
        # Read and handle the uncompressed content
        content = response.read()

    content = content.decode("utf8")

    version, status, explanation = statusline.split(" ", 2)

    if int(status) >= 300 and int(status) <= 400:
        location = headers["Location"]
        # Find the index of the first occurrence of "//"
        double_slash_index = location.find("//")
        # Find the index of the next slash ("/") after the double slash
        next_slash_index = location.find("/", double_slash_index + 2)
        # Extract the path part of the URL
        path = location[next_slash_index:]

        if num_of_reqs >= 0:
            return request_remote_resource(path, scheme, host, num_of_reqs - 1)

    assert status == "200", "{}: {}".format(status, explanation)

    assert "transfer-encoding" not in headers
    assert "content-encoding" not in headers

    body = content
    s.close()

    return headers, body


def request_file(path: str):
    file = open(path, 'r')
    body = file.read()
    headers = {
        "method": "GET",
        "Content-Type": "file"
    }
    return dumps(headers), body


def request(url: str):
    # Allows inlining HTML content into the URL itself
    if url.startswith("data:"):
        headers = dumps({"method": "GET"})
        body = url.split(",")[1]
        return headers, body
    # Finds the scheme
    scheme, url = url.split("://", 1)
    assert scheme in ["http", "https", "file"], \
        "Unknown scheme {}".format(scheme)

    # Get the host and the path
    host, path = url.split("/", 1)

    if scheme in ["http", "https"]:
        path = "/" + path
        return request_remote_resource(path, scheme, host)
    return request_file(path)


def lex(body: str):
    # Removes the tags and displays the rest
    tags = []
    entities = {"&lt;": "<", "&gt;": ">"}
    in_angle = False
    in_body = False
    in_entity = False
    tag = ""
    entity = ""
    text = ""
    for c in body:
        if c == "<":
            in_angle = True
        elif c == ">":
            tags.append(tag)
            if tag == "body":
                in_body = True
            elif tag == "/body":
                in_body = False
            tag = ""
            in_angle = False
        elif in_angle:
            tag = tag + c
        elif c == "&":
            in_entity = True
            entity = entity + c
        elif c == ";" and in_entity:
            in_entity = False
            entity = entity + c
            try:
                text += entities[entity]
            except KeyError:
                text += ""
            entity = ""
        elif in_entity:
            entity = entity + c
        elif not in_angle and in_body:
            text += c
    return text


def load(url: str = "file:///public/index.html"):
    # This will download the resource from the remote server
    view_source = False
    if url.startswith("view-source:"):
        view_source = True
        url = url.replace("view-source:", "")
    headers, body = request(url)
    if view_source == False:
        print(lex(body))
    else:
        print(body)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        load(sys.argv[1])
    else:
        load()
