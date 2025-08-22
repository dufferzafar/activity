import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Dict, List

import aiohttp

from tqdm.auto import tqdm

import importlib
settings = importlib.import_module("settings")  # type: ignore


BASE_URL = "https://api.trakt.tv"
HISTORY_ENDPOINT_TMPL = "/users/{username}/history"

DEFAULT_USERNAME = "dufferzafar"
DEFAULT_LIMIT = 1000
CONCURRENT_REQUESTS = 2
REQUEST_TIMEOUT_SECONDS = 30
RETRY_STATUS_CODES = {429, 500, 502, 503, 504}
MAX_RETRIES = 5


def _now_iso() -> str:
	return datetime.now(timezone.utc).isoformat()


def build_headers() -> Dict[str, str]:
	headers = {
		"Content-Type": "application/json",
		"trakt-api-version": "2",
		"trakt-api-key": settings.CLIENT_ID,
		"User-Agent": "dufferzafar-activity-analytics-trakt/1.0",
	}
	return headers


async def fetch_page(session: aiohttp.ClientSession, username: str, page: int, limit: int) -> Dict[str, Any]:
	params = {
		"page": str(page),
		"limit": str(limit),
		"extended": "full",
	}
	url = f"{BASE_URL}{HISTORY_ENDPOINT_TMPL.format(username=username)}"

	retry = 0
	backoff = 1.0
	while True:
		try:
			async with session.get(url, params=params, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
				status = resp.status
				text = await resp.text()
				if status == 200:
					items = json.loads(text)
					headers = {k.lower(): v for k, v in resp.headers.items()}
					meta = {
						"page": int(headers.get("x-pagination-page", page)),
						"limit": int(headers.get("x-pagination-limit", limit)),
						"page_count": int(headers.get("x-pagination-page-count", 1)),
						"item_count": int(headers.get("x-pagination-item-count", len(items))),
						"ratelimit": headers.get("x-ratelimit"),
						"etag": headers.get("etag"),
						"last_modified": headers.get("last-modified"),
					}
					return {"items": items, "meta": meta}

				if status in RETRY_STATUS_CODES and retry < MAX_RETRIES:
					await asyncio.sleep(backoff)
					retry += 1
					backoff *= 2
					continue

				raise aiohttp.ClientResponseError(
					resp.request_info, resp.history, status=status, message=text, headers=resp.headers
				)
		except aiohttp.ClientError as e:
			if retry < MAX_RETRIES:
				await asyncio.sleep(backoff)
				retry += 1
				backoff *= 2
				continue
			raise e


async def fetch_all_history(username: str, limit: int = DEFAULT_LIMIT) -> List[Dict[str, Any]]:
	connector = aiohttp.TCPConnector(limit=CONCURRENT_REQUESTS, ssl=False)
	async with aiohttp.ClientSession(headers=build_headers(), connector=connector) as session:
		first = await fetch_page(session, username=username, page=1, limit=limit)
		all_items: List[Dict[str, Any]] = list(first["items"]) if first and first.get("items") else []
		page_count = int(first["meta"].get("page_count", 1))

		# Page progress bar
		with tqdm(total=page_count, desc="fetch pages", unit="page") as pbar:
			pbar.update(1)
			for page in range(2, page_count + 1):
				result = await fetch_page(session, username=username, page=page, limit=limit)
				all_items.extend(result.get("items", []))
				pbar.update(1)

		return all_items


async def main() -> None:
	username = DEFAULT_USERNAME
	output_path = "trakt/history.jsonl"

	print(f"[{_now_iso()}] Fetching Trakt history for '{username}' with limit={DEFAULT_LIMIT} and extended=full...")
	items = await fetch_all_history(username=username, limit=DEFAULT_LIMIT)
	print(f"[{_now_iso()}] Retrieved {len(items)} items. Writing to {output_path} ...")

	with open(output_path, "w", encoding="utf-8") as f:
		with tqdm(total=len(items), desc="write file", unit="item") as wbar:
			for item in items:
				f.write(json.dumps(item, ensure_ascii=False) + "\n")
				wbar.update(1)

	print(f"[{_now_iso()}] Done.")


if __name__ == "__main__":
	asyncio.run(main()) 