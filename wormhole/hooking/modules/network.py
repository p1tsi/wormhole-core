import json
import os.path

from time import time
from urllib.parse import urlparse

from .base import BaseModule


class Response:
    banner = "===== RESPONSE ====="

    def __init__(self, *args):
        self.url = args[0] or "N/A"
        self.status_code = args[1] or "N/A"
        self.headers = args[2] or "N/A"
        self.body = "N/A"

    def set_body(self, data, module_dir):
        if self.body == "N/A":
            filename = f"{urlparse(self.url).hostname}_{time()}"
            with open(os.path.join(module_dir, "Response", filename), "wb") as body_fd:
                body_fd.write(data)
            self.body = filename

    def _parse_headers(self):
        if self.headers:
            headers_str = "\n-- HEADERS --\n"
            headers = json.loads(self.headers)
            for header, value in headers.items():
                headers_str += f"{header}: {value}\n"
            return headers_str
        else:
            return ""

    def __repr__(self):
        response = f"\n{self.banner}\n{self.status_code}\n{self._parse_headers()}"

        if self.body:
            response += "\n-- BODY--\n"
            response += self.body
        response += "\n"
        return response


class Request:
    banner = "\n=============== REQUEST ===============\n"

    def __init__(self, *args):  # url=None, method=None, headers=None, body=None, cookies=None):
        self.url: str = args[0] or "N/A"
        self.method: str = args[1] or "N/A"
        self.headers: str = args[2] or None
        if len(args) > 3:
            self.cookies: str = args[3]
        else:
            self.cookies: str = ""
        self.body: str = "N/A"
        self.response: Response = None

    def set_body(self, data, module_dir):
        if self.body == "N/A":
            filename = f"{urlparse(self.url).hostname}_{time()}"
            with open(os.path.join(module_dir, "Request", filename), "wb") as body_fd:
                body_fd.write(data)
            # try:
            #    self.body = data.decode("utf8")
            # except:
            self.body = filename

    def update_headers(self, new_headers):
        if new_headers:
            self.headers = new_headers

    def _headers_as_str(self):
        if self.headers:
            headers_str = "\n-- HEADERS --\n"
            try:
                headers = json.loads(self.headers)
                for header, value in headers.items():
                    headers_str += f"{header}: {value}\n"
            except:
                pass

            return headers_str
        else:
            return ""

    def _parse_cookies(self):
        if self.cookies:
            cookie_str = "\n-- COOKIES --\n"
            for cookie in self.cookies:
                cookie_str += f"{cookie}\n"
            return cookie_str
        else:
            return ""

    def __repr__(self):
        request = f"{self.banner}{self.method} \033[91m{self.url}\033[0m\n{self._headers_as_str()}\n{self._parse_cookies()}"

        if self.body:
            request += "\n-- BODY--\n"
            request += f"{self.body}\n"

        if self.response:
            request += str(self.response)

        return request

    def to_dict(self):
        request_as_dict = {'request': {}}
        request_as_dict['request']['url'] = self.url
        request_as_dict['request']['method'] = self.method
        request_as_dict['request']['headers'] = json.loads(self.headers) if self.headers else ""
        if self.cookies:
            request_as_dict['request']['cookies'] = self.cookies

        request_as_dict['request']['body'] = self.body

        return request_as_dict


class Network(BaseModule):
    """
    This module is used to collect, process and aggregate the results of network (HTTP) functions hooking.
    Hooked functions:
        -[NSURLSession dataTaskWithRequest:]
        -[NSURLSession dataTaskWithRequest:completionHandler:]
        -[NSURLSession uploadTaskWithRequest:fromData:]
        -[NSURLSession uploadTaskWithRequest:fromData:completionHandler:]
        -[NSURLSession uploadTaskWithRequest:fromFile:]
        -[NSURLSession uploadTaskWithRequest:fromFile:completionHandler:]
        -[NSURLSession downloadTaskWithRequest:]
        -[NSURLSession downloadTaskWithRequest:completionHandler:]
        -[NSURLSession uploadTaskWithStreamedRequest:]
        -[NSURLResponse _initWithCFURLResponse:]
    """

    def __init__(self, data_dir, connector_manager):
        super().__init__(data_dir, connector_manager)
        self.requests = dict()
        self.count = 0

        resp_dir = os.path.join(self._module_dir, "Response")
        if not os.path.exists(resp_dir):
            os.mkdir(resp_dir)

        req_dir = os.path.join(self._module_dir, "Request")
        if not os.path.exists(req_dir):
            os.mkdir(req_dir)

    def init_request(self):
        request = Request(*self.message.args)  # [0], self.message.args[1], self.message.args[2], self.message.args[3])
        if self.message.data:
            request.set_body(self.message.data, self._module_dir)
        return request

    def count_requests(self):
        count = 0
        for _, requests in self.requests.items():
            count = count + len(requests)
        return count

    def _process(self):
        request = self.requests.get(self.message.args[0], None)
        if "callback" in self.message.symbol:
            if request:
                request.response.set_body(self.message.data, self._module_dir)
                self.publish(request)
                del self.requests[self.message.args[0]]
                self.count = self.count + 1
        elif "Response" in self.message.symbol:
            if request:
                request.response = Response(*self.message.args)
                #self.publish(request)
                #del self.requests[self.message.args[0]]
                #self.count = self.count + 1
        elif 'uploadTaskWithStreamedRequest' in self.message.symbol:
            request = self.init_request()
            if request:
                self.requests[self.message.args[0]] = request
        else:
            if not request:
                self.requests[self.message.args[0]] = self.init_request()
                self.publish(self.requests[self.message.args[0]])
            else:
                if self.message.symbol == "CFURLRequestSetHTTPRequestBody":
                    request.set_body(self.message.data, self._module_dir)
                else:
                    request.update_headers(self.message.args[2])

            #self.publish(request)