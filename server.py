import socket
import select
import os
from subprocess import Popen, PIPE
from ConfigParser import SafeConfigParser
from math import floor, log, pow
from bs4 import BeautifulSoup

"""
What to do:  1. PHP interaction
             2. Multithreading
"""
# Converting byte to higher measure unit
def convert_size(size):
    size_name = ("KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(floor(log(size, 1024)))
    p = pow(1024, i)
    s = round(size / p, 2)
    if (s > 0):
        return '%s %s' % (s, size_name[i])
    else:
        return '0B'

# Change working directory to where server files are
os.chdir('D:\\Document\\IdeaProjects\\HTTPServer\\')

# Reading configuration file for server settings
parser = SafeConfigParser()
parser.read('httpserver.conf')

# Define port and server address
server = parser.get('http_server', 'server')
port = parser.get('http_server', 'port')
port = int(port)

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.bind((server, port))
s.listen(5)

input_socket = [s]

while True:
    read_ready, write_ready, exception = select.select(input_socket, [], [])
    for sock in read_ready:
        if sock == s:
            client_socket, client_addr = s.accept()
            input_socket.append(client_socket)
        else:
            request = sock.recv(1024)
            if request:
                req = request.split()
                # Request example: GET / HTTP/1.1
                # Split example : ['GET','/','HTTP/1.1']
                print client_addr, " LOG: Request received"
                if req[0] == 'GET':
                    # Get the requested URL
                    req[1] = req[1].replace('%20', ' ')
                    url = '.' + req[1]
                    path = os.path.abspath(url)

                    if os.path.isdir(path):
                        print client_addr, " LOG: Directory access to ", path
                        # Get file and folder list in path
                        dirlist = os.listdir(path)
                        there_is_index = 0

                        # Check if there's index.html file
                        for i in dirlist:
                            if i == 'index.html':
                                index_path = path + '\index.html'
                                there_is_index = 1

                        # If there's index.html file, then send that file
                        if there_is_index:
                            print client_addr, " LOG: index.html found"
                            try:
                                fopen = open(index_path, 'rb')
                            except Exception:
                                print "Failed to open " + index_path
                            else:
                                body = fopen.read()
                                length = 'Content-Length: ' + str(len(body)) + '\r\n\r\n'
                                response_header = ['HTTP/1.1 200 OK\r\n', 'Content-Type: text/html; charset=UTF-8\r\n',
                                                   length]
                                data = ''.join(response_header) + body
                                sock.sendall(data)

                        # If there's no index.html file, then display list of files on that directory
                        else:
                            print client_addr, " LOG: index.html not found"
                            files = []

                            # [OS: WINDOWS] If last character of path is not '\', then add it 
                            if path[-1] != "\\":
                                filedir = path + '\\'

                            # Select files only
                            for i in range(len(dirlist)):
                                if os.path.isfile(filedir + dirlist[i]):
                                    files.append(dirlist[i])

                            # Add relative path to files list (For hyperlink purpose)
                            files_with_dir = []
                            for i in range(len(files)):
                                if req[1][-1] != '/':
                                    files_with_dir.append(req[1] + '/' + files[i])
                                else:
                                    files_with_dir.append(req[1] + files[i])

                            file_names = []
                            for i in range(len(files_with_dir)):
                                file_name, file_extension = os.path.splitext(files_with_dir[i])
                                file_names.append('%20'.join(file_name.split('\\')[-1].split()) + file_extension)

                            # Create page, table style presentation
                            html = ['<html>', '<head>', '<title>', 'SERVER TC', '</title>', '</head>', '</html>']
                            body = ['<body>', '<h1>', 'Index of ', req[1], '</h1>', '<table>', '<col width="500">',
                                    '<col width="80">', '<th>', 'Name', '</th>', '<th>', 'Size', '</th>', '</table>',
                                    '</body>']
                            links = []
                            tr_pos = 0
                            # Find </table> position
                            for i in range(len(body)):
                                if body[i] == '</table>':
                                    tr_pos = i
                                    break

                            # Add table rows and insert to html body
                            for i in range(len(files)):
                                temp = '<tr><td><a href=' + '\"' + file_names[i] + '\"' + '>' + files[i] + '</a></td>'
                                size = os.path.getsize('.' + files_with_dir[i])
                                converted = convert_size(size / 1024)
                                temp = temp + '<td>' + converted + '</td></tr>'
                                links.append(temp)
                                body.insert(tr_pos, links[i])

                            # Put html list with body list together
                            html.extend(body)
                            html = ''.join(html)
                            soup = BeautifulSoup(html)
                            html = soup.prettify()
                            length = 'Content-Length: ' + str(len(html)) + '\r\n\r\n'
                            response_header = ['HTTP/1.1 200 OK\r\n', 'Content-Type: text/html; charset=UTF-8\r\n',
                                               length]
                            data = ''.join(response_header) + html

                            sock.sendall(data)
                            print client_addr, " LOG: File list sent"

                    elif os.path.isfile(path):
                        print client_addr, " LOG: File access request", path

                        file_name, file_extension = os.path.splitext(path)
                        file_name = file_name.split('\\')[-1] + file_extension

                        # PHP Handler here
                        if file_extension == '.php':
                            php_exe = "C:\\terminal\\php\\php.exe"
                            php_file = "D:\\Document\\IdeaProjects\\HTTPServer\\" + file_name
                            process = Popen([php_exe, '-f', php_file], stdin=PIPE, stdout=PIPE, stderr=PIPE)
                            output = process.communicate()

                            content_type = 'Content-Type: text/html\r\n'
                            length = 'Content-Length: ' + str(len(output[0])) + '\r\n\r\n'
                            response_header = ['HTTP/1.1 200 OK\r\n', content_type, length]

                            data = ''.join(response_header) + output[0]

                            sock.sendall(data)

                        else:
                            try:
                                fopen = open(path, 'rb')

                            except Exception:
                                print client_addr, " LOG: Cannot access file"

                            else:
                                mime_types = {'.txt': 'text/plain', '.ogv': 'video/ogg', '.mp3': 'audio/mpeg3',
                                              '.html': 'text/html'}


                                if file_extension in mime_types and file_extension != '.html':
                                    content_type = 'Content-Type: ' + mime_types[file_extension] + '\r\n'
                                    content_disposition = 'Content-Disposition: attachment; filename="' + file_name + '"\r\n'

                                elif file_extension == '.html':
                                    content_type = 'Content-Type: text/html\r\n'
                                    content_disposition = ''

                                else:
                                    content_type = 'Content-Type: application/octet-stream\r\n'
                                    content_disposition = 'Content-Disposition: attachment; filename=' + file_name + '\r\n'

                                body = fopen.read()
                                length = 'Content-Length: ' + str(len(body)) + '\r\n\r\n'

                                if content_disposition != '':
                                    response_header = ['HTTP/1.1 200 OK\r\n', content_type, content_disposition, length]
                                else:
                                    response_header = ['HTTP/1.1 200 OK\r\n', content_type, length]

                                data = ''.join(response_header) + body

                                sock.sendall(data)

                    # Not found
                    else:
                        print client_addr, " LOG: Requested file or directory not found"
                        # Create page
                        html = ['<html>', '<head>', '<title>', 'SERVER TC - NOT FOUND', '</title>', '</head>',
                                '</html>']
                        body = ['<body>', '<h1>', 'HTTP 404 Not Found', '</h1>', '</body>']

                        html.extend(body)
                        html = ''.join(html)
                        soup = BeautifulSoup(html)
                        html = soup.prettify()

                        length = 'Content-Length: ' + str(len(html)) + '\r\n\r\n'
                        response_header = ['HTTP/1.1 404 Not Found\r\n', 'Content-Type: text/html; charset=UTF-8\r\n',
                                           length]
                        data = ''.join(response_header) + html

                        sock.sendall(data)
            else:
                sock.close()
                input_socket.remove(sock)
