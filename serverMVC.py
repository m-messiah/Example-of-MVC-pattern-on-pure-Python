__author__ = 'm_messiah'

from wsgiref.simple_server import make_server
import appMVC as app

# Instantiate the WSGI server.
# It will receive the request, pass it to the application
# and send the application's response to the client
httpd = make_server(
    '0.0.0.0',
    8051,
    app.application
)

print "Run: http://0.0.0.0:8051/"
httpd.serve_forever()
