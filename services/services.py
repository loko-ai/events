import logging
import os
from concurrent.futures import ThreadPoolExecutor
import time
from pprint import pprint

import requests
import schedule
from flask import Flask, request, jsonify

app = Flask("")


class URLRequest:
    def __init__(self, url):
        self.url = url

    def get(self, **kwargs):
        return requests.get(self.url, **kwargs)

    def post(self, **kwargs):
        return requests.post(self.url, **kwargs)

    def __getattr__(self, k):
        return URLRequest(os.path.join(self.url, k))


u = URLRequest(os.environ.get("GATEWAY") or "http://localhost:9999/")
orch = u.routes.orchestrator
projects = orch.projects


def get_nodes(name):
    for g, v in orch.projects.events.get().json().get("graphs", {}).items():
        for n in v.get("nodes", []):
            _name = n.get("data").get("name")
            if _name == name:
                yield n.get("id")


def sched():
    def p():
        logging.error(orch.projects.events.get().text)
        for id in get_nodes("Extensions"):
            projects.events.trigger.post(json=dict(id=id))

    schedule.every(5).seconds.do(p)
    while True:
        schedule.run_pending()
        time.sleep(1)


@app.route("/", methods=["POST"])
def test():
    args = request.json.get('args')
    print("ARGS", args)
    json = request.json.get("value")
    print("JSON", json)
    return jsonify(dict(os.environ))


@app.route("/files", methods=["POST"])
def test2():
    file = request.files['file']
    fname = file.filename
    print("You have uploaded a file called:", fname)
    return jsonify(dict(msg=f"Hello extensions, you have uploaded the file: {fname}!"))


if __name__ == "__main__":
    with ThreadPoolExecutor() as pool:
        pool.submit(sched)
        app.run("0.0.0.0", 8080)

    print("Executed")
