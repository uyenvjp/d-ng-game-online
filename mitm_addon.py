"""
Dungeon Corp — mitmproxy addon
- Log mọi request game gửi (để học protocol thật)
- Intercept các domain bigshot-games.xyz / dead-server → trả response giả từ mock server
"""
import json
import time
from mitmproxy import http, ctx

DEAD_DOMAINS = ("bigshot-games.xyz", "notice.bigshot-games.xyz", "api.bigshot-games.xyz")

LOG_FILE = r"C:\Users\okokok\Desktop\dungeon-re\analysis\captured_requests.log"


def _ts():
    return int(time.time())


def _wrap(data, result="complete"):
    body = {"_result": result, "_timestamp": _ts()}
    body.update(data)
    return json.dumps(body)


def make_response(path: str, form: dict) -> str:
    p = path.lower()

    # time sync — endpoint game đang fail
    if any(k in p for k in ("time", "timestamp", "timevalue")):
        return _wrap({
            "timestamp": _ts(),
            "serverTime": _ts(),
            "timezone": 0,
            "utcOffset": 0,
            "_now": _ts(),
        })

    if "login" in p or "auth" in p or "user" in p:
        return _wrap({
            "_loginKey": "localofflinesession",
            "_userID": form.get("_userID", "guest"),
            "_userName": form.get("_userName", "Player"),
            "_gameID": form.get("_gameID", "guest"),
            "_dataFile": "",
            "_isBan": "0",
            "_chatBan": "0",
            "_maintenance": "0",
            "_banIgnore": "0",
            "_isNewUser": "0",
            "_exist": "1",
            "_notExist": "0",
            "_complete": "1",
        })

    if "save" in p or "backup" in p or "data" in p:
        return _wrap({"_complete": "1", "_fail": "0"})

    if "rank" in p or "leaderboard" in p or "pvp" in p:
        return _wrap({"_list": "[]", "_rank": "1", "_score": "0", "_totalUsers": "1"})

    if "event" in p:
        return _wrap({"_eventNo": "0", "_list": "[]"})

    if "version" in p or "update" in p or "check" in p:
        return _wrap({"_updateCheck": "0", "_maintenance": "0", "_maintenance_exit": "0"})

    if "agree" in p:
        return "<html><body>Local server - agreement placeholder</body></html>"

    # Mặc định: trả result complete + timestamp
    return _wrap({"_complete": "1"})


class DungeonCorpAddon:
    def request(self, flow: http.HTTPFlow) -> None:
        url = flow.request.pretty_url
        host = flow.request.pretty_host

        # Log tất cả request để phân tích protocol
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(f"[{_ts()}] {flow.request.method} {url}\n")
                if flow.request.urlencoded_form:
                    f.write(f"  FORM: {dict(flow.request.urlencoded_form)}\n")
                f.write(f"  HEADERS: {dict(flow.request.headers)}\n\n")
        except Exception as e:
            ctx.log.warn(f"log fail: {e}")

        # Intercept domain server chết
        if any(d in host for d in DEAD_DOMAINS):
            path = flow.request.path
            form = dict(flow.request.urlencoded_form) if flow.request.urlencoded_form else {}
            body = make_response(path, form)
            ctx.log.info(f"[INTERCEPT] {flow.request.method} {url} -> mock ({len(body)} bytes)")
            flow.response = http.Response.make(
                200,
                body.encode(),
                {"Content-Type": "application/json"}
            )


addons = [DungeonCorpAddon()]
