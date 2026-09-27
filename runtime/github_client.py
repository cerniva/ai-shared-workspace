from __future__ import annotations

import base64
import json
from urllib import error, parse, request


class GitHubError(RuntimeError):
    pass


class GitHubConfigError(GitHubError):
    pass


class GitHubAuthError(GitHubError):
    pass


class GitHubNotFound(GitHubError):
    pass


class GitHubConflict(GitHubError):
    pass


class UrllibTransport:
    def request(self, method, url, headers, body=None):
        req = request.Request(url, data=body, headers=headers, method=method)
        try:
            with request.urlopen(req, timeout=20) as response:
                return response.status, dict(response.headers), response.read()
        except error.HTTPError as exc:
            return exc.code, dict(exc.headers), exc.read()


class GitHubContentsClient:
    def __init__(self, settings, transport=None):
        self.settings = settings
        self.transport = transport or UrllibTransport()

    def _check(self):
        if not self.settings.ready_for_github:
            raise GitHubConfigError("github configuration missing")

    def _url(self, path: str) -> str:
        if path.startswith(("http://", "https://")) or ".." in path.split("/"):
            raise ValueError("path must be repository-relative")
        safe_path = parse.quote(path, safe="/")
        return f"https://api.github.com/repos/{self.settings.github_repo}/contents/{safe_path}"

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.settings.github_token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    @staticmethod
    def _raise_for_status(status: int):
        if status in (401, 403):
            raise GitHubAuthError("github authorization failed")
        if status == 404:
            raise GitHubNotFound("github resource not found")
        if status in (409, 422):
            raise GitHubConflict("github content conflict")
        raise GitHubError(f"github request failed: {status}")

    def get_json(self, path: str):
        self._check()
        status, _, body = self.transport.request("GET", self._url(path), self._headers())
        if status != 200:
            self._raise_for_status(status)
        payload = json.loads(body.decode("utf-8"))
        decoded = base64.b64decode(payload["content"]).decode("utf-8")
        return json.loads(decoded), payload["sha"]

    def put_json(self, path: str, data, sha: str, message: str) -> str:
        self._check()
        raw = (json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
        body = json.dumps({
            "message": message,
            "content": base64.b64encode(raw).decode("ascii"),
            "sha": sha,
        }).encode("utf-8")
        status, _, response = self.transport.request("PUT", self._url(path), self._headers(), body)
        if status not in (200, 201):
            self._raise_for_status(status)
        payload = json.loads(response.decode("utf-8"))
        return payload["content"]["sha"]
