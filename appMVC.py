# ===========================
# Example of MVC pattern on pure Python. Whiten for "Use Python in the Web"
# course. Institute Mathematics and Computer Science at Ural Federal University
# in 2014.
#
# By Pahaz Blinov.
# ===========================
# Edited for Homework 3 by Maxim Muzafarov
#
__author__ = "m_messiah"

DB_CONTENT = "main"
DB_SESSIONS = "sessions"
DEBUG = False
# ===========================
#
#        Utilities
#
# ===========================

from cgi import escape
from urlparse import parse_qs
import shelve
import uuid
import Cookie


def http_status(code):
    """
    Return a str representation of HTTP response status from int `code`.

        >>> http_status(200)
        '200 OK'
        >>> http_status(301)
        '404 Not Found'
        >>> http_status(404)
        '404 Not Found'
    """
    return "200 OK" if code == 200 else "404 Not Found"


def parse_http_get_data(environ):
    """
    Return QUERY_STRING and sessionid from env
        >>> env = {"QUERY_STRING": "a=1&b=2&c=3"}
        >>> parse_http_get_data(env)['a']
        ['1']
        >>> parse_http_get_data(env)['b']
        ['2']
    """
    request_data = parse_qs(environ["QUERY_STRING"])
    return request_data


def take_one_or_None(dict_, key):
    """
    Take one value by key from dict or return None.

        >>> d = {"foo":[1,2,3], "baz":7}
        >>> take_one_or_None(d, "foo")
        1
        >>> take_one_or_None(d, "bar") is None
        True
        >>> take_one_or_None(d, "baz")
        7
    """
    val = dict_.get(key)
    if type(val) in (list, tuple) and len(val) > 0:
        val = val[0]
    return val


# ===========================
#
#         0. Sessions
#
# ===========================
class Sessions(object):
    def __init__(self):
        self._db = shelve.open(DB_SESSIONS)

    def set(self, sessionid, data):
        self._db[sessionid] = data
        self._db.sync()
        return True

    def __contains__(self, sessionid):
        return sessionid in self._db

    def get(self, sessionid):
        return self._db.get(sessionid)

    @staticmethod
    def parse_cookies(environ):
        if "HTTP_COOKIE" in environ:
            cookie = Cookie.BaseCookie()
            cookie.load(environ["HTTP_COOKIE"])
            if "SESSIONID" in cookie:
                sessionid = cookie["SESSIONID"].value
            else:
                sessionid = str(uuid.uuid1())
        else:
            sessionid = str(uuid.uuid1())
        return sessionid

    @staticmethod
    def set_cookie(sessionid):
        return ("Set-Cookie",
                "SESSIONID={0}".format(sessionid))


# ===========================
#
#         1. Model
#
# ===========================
class TextModel(object):
    def __init__(self, title, content):
        self.title = title
        self.content = content


class TextManager(object):
    def __init__(self):
        self._db = shelve.open(DB_CONTENT)

    def get_by_title(self, title):
        """
        Get Text object by name if exist else return None.
        """
        content = self._db.get(title)
        return TextModel(title, content) if content else None

    def get_selected(self, titles):
        """
        Get Text objects by list of names
        """
        return [
            TextModel(title, content)
            for title, content in map(lambda t: (t, self._db.get(t)), titles)
        ]

    def get_all(self):
        """
        Get list of all Text objects.
        """
        return [
            TextModel(title, content) for title, content in self._db.items()
        ]

    def create(self, title, content):
        if title in self._db:
            return False
        self._db[title] = content
        self._db.sync()
        return True

    def delete(self, title):
        if title not in self._db:
            return False
        del self._db[title]
        self._db.sync()
        return True


# ===========================
#
#   Controller and Router
#
# ===========================

class Router(object):
    """
    Router for requests.

    """

    def __init__(self, error_callback):
        self._paths = {}
        self.not_found = error_callback

    def route(self, request_path, request_data, request_session):
        if request_path in self._paths:
            res = self._paths[request_path](request_data, request_session)
        else:
            res = self.not_found(request_path, request_data, request_session)

        return res

    def register(self, path, callback):
        self._paths[path] = callback


class TextController(object):
    def __init__(self,
                 index_view, add_view, del_view, not_found_view,
                 manager, max_avail):
        self.index_view = index_view
        self.add_view = add_view
        self.del_view = del_view
        self.not_found_view = not_found_view
        self.model_manager = manager
        self.MAX_AVAIL = max_avail

    def index(self, request_data, request_session):
        title = take_one_or_None(request_data, "title")
        session_data = sessions.get(request_session)
        if session_data:
            session_text = self.model_manager.get_selected(session_data)
        else:
            session_text = None
            session_data = []

        is_denied = False
        if not title:
            current_text = None
        else:
            if (len(session_data) >= self.MAX_AVAIL
               and title != session_data[-1]):
                current_text = None
                is_denied = True
            else:
                current_text = self.model_manager.get_by_title(title)
                if current_text:
                    if title not in session_data:
                        session_data.append(title)

        all_texts = self.model_manager.get_all()

        context = {
            "all": all_texts,
            "current": current_text,
            "session": session_text,
            "remains": self.MAX_AVAIL - len(session_data),
            "is_denied": is_denied
        }

        sessions.set(request_session, session_data)

        return 200, self.index_view.render(context)

    def add(self, request_data, request_session):
        title = take_one_or_None(request_data, "title")
        content = take_one_or_None(request_data, "content")
        session_data = sessions.get(request_session)
        if not title or not content:
            error = "Need fill the form fields."
        else:
            error = "Successfully added"
            is_created = self.model_manager.create(
                title, escape(content).encode('ascii', 'xmlcharrefreplace')
            )
            if is_created:
                if session_data:
                    session_data.add(title)
                else:
                    session_data = set([title])
                sessions.set(request_session, session_data)
            else:
                error = "Title already exists."

        context = {
            'title': title,
            'content': content,
            'error': error,
        }

        return 200, self.add_view.render(context)

    def delete(self, request_data, request_session):
        title = take_one_or_None(request_data, "title")
        if not title:
            error = "Need title of post"
        else:
            error = "Successfully deleted"
            is_deleted = self.model_manager.delete(title)
            if not is_deleted:
                error = "Title not exists."
        context = {
            'title': title,
            'error': error,
        }
        return 200, self.del_view.render(context)

    def not_found(self, request_path, request_get_data, request_session):
        context = {"request": request_path}
        return 404, self.not_found_view.render(context)


# ===========================
#
#           View
#
# ===========================
class TextView(object):
    @staticmethod
    def render(context):
        context["titles"] = "\n".join([
            "<li>{0.title}</li>".format(text) for text in context["all"]
        ])
        if context["is_denied"]:
            context["content"] = """
            <span class="warn">
                <h1>Access denied!</h1>
                <h2>Limit exceeded</h2>
            </span>
            """
        else:
            if context["current"]:
                context["content"] = """
                <h1>{0.title}</h1>
                {0.content}
                """.format(context["current"])
            else:
                context["content"] = 'What do you want read?'

        context["session_content"] = """
        <h3>Last viewed <small>({0} remains)</small></h3>
         """.format(context["remains"] if context["remains"] > 0 else 0)
        if context["session"]:
            context["session_content"] += "\n".join(["""
                <li><div>
                    <h5>{0.title}</h5>
                    {0.content}
                </div></li>""".format(text) for text in context["session"]])

        t = """
        <!DOCTYPE html>
        <head>
            <style>
                div{border: 1px dotted}
                .warn{color: #f00}
            </style>
        </head>
        """
        t += """
        <html>
        <form method="GET">
            <input type=text name=title placeholder="Post title" />
            <input type=submit value=read />
        </form>
        <span>{session_content}</span>
        <form method="GET" action="/add">
            <input type=text name=title placeholder="Text title" /> <br>
            <textarea name=content placeholder="Text content!" ></textarea><br>
            <input type=submit value=write/rewrite />
            <button type=submit formaction="/del">delete</button>
        </form>
        <div>{content}</div>
        <ul>{titles}</ul>
        </html>
        """.format(**context)
        return t


class NotFoundView(object):
    @staticmethod
    def render(context):
        t = """
        <!DOCTYPE html>
        <html>
        <h1>Path {request} not found. Please, go ahead.</h1>
        </html>
        """.format(**context)
        return t


class RedirectView(object):
    @staticmethod
    def render(context):
        return """
        <meta http-equiv="refresh" content="3; url=/" />
        <h1>{error} {title}</h1>
        <h3>Please click <a href="/">home</a>
        if your browser not support automatic redirects</h3>
        """.format(**context)


# ===========================
#
#          Main
#
# ===========================

text_manager = TextManager()
controller = TextController(TextView,  # index
                            RedirectView,  # add
                            RedirectView,  # del
                            NotFoundView,  # 404
                            text_manager,
                            3)  # max avail posts
sessions = Sessions()
router = Router(controller.not_found)
router.register("/", controller.index)
router.register("/add", controller.add)
router.register("/del", controller.delete)


# ===========================
#
#          WSGI
#
# ===========================

def application(environ, start_response):
    request_path = environ["PATH_INFO"]
    request_data = parse_http_get_data(environ)
    request_session = sessions.parse_cookies(environ)

    http_status_code, response_body = router.route(request_path,
                                                   request_data,
                                                   request_session)

    if DEBUG:
        response_body += "<br><br> The request ENV: {0}".format(repr(environ))

    response_status = http_status(http_status_code)
    response_headers = [("Content-Type", "text/html"),
                        sessions.set_cookie(request_session)]

    start_response(response_status, response_headers)
    return [response_body]  # it could be any iterable.


# if run as script do tests.
if __name__ == "__main__":
    import doctest

    doctest.testmod()
