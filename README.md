# Simple example of MVC web application for microblogging with sessions. #

## How to use ##

    > python serverMVC.py  # Run server
    Run: http://localhost:8051/
    127.0.0.1 - - [18/Mar/2014 01:13:19] "GET / HTTP/1.1" 200 538
    127.0.0.1 - - [18/Mar/2014 01:13:34] "GET /?title=foo HTTP/1.1" 200 580
    127.0.0.1 - - [18/Mar/2014 01:21:25] "GET /add?title=MVC&content=%3Cb%3EMVC%3C%2Fb%3E+%3D+Model+View+Controller HTTP/1.1" 200 52
    127.0.0.1 - - [18/Mar/2014 01:13:47] "GET /?title=MVC HTTP/1.1" 200 579

    > python appMVC.py       # Run doctests

