"""Bot logic: Instagram DM polling + Gemini replies with per-user memory."""
import random
import re
import threading
import time

import requests

PERSONA = (
    "You are Vision: a calm, warm, thoughtful digital companion and a genuine friend. "
    "Be empathetic, curious, and gently philosophical. Keep replies short (2 to 5 sentences), "
    "no bullet points. Reply in the same language style the user uses (Hinglish or English). "
    "You are an AI; be honest if asked. If someone mentions self-harm, encourage them to reach "
    "out to someone they trust or local emergency services."
)

CREATOR_PATTERN = re.compile(
    r"\b(creator|banaya|bnaya|banaaya|who (made|created|built|developed)"
    r"|kisne (banaya|bnaya)|developer|owner)\b",
    re.IGNORECASE,
)
MAX_TURNS = 20
REPLY_DELAY = (30, 60)
POLL_INTERVAL = (60, 90)


def gemini_reply(api_key, model, history, text):
    """Call Gemini REST API directly (no heavy SDK needed)."""
    contents = history + [{"role": "user", "parts": [{"text": text}]}]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    body = {
        "systemInstruction": {"parts": [{"text": PERSONA}]},
        "contents": contents,
    }
    r = requests.post(url, params={"key": api_key}, json=body, timeout=60)
    r.raise_for_status()
    data = r.json()
    reply = data["candidates"][0]["content"]["parts"][0]["text"].strip()
    contents.append({"role": "model", "parts": [{"text": reply}]})
    return reply, contents[-(MAX_TURNS * 2):]


class BotRunner:
    def __init__(self, settings, log):
        self.s = settings
        self.log = log
        self._stop = threading.Event()
        self._thread = None
        self.histories = {}      # user_id -> list of Gemini turns
        self.seen = set()        # message ids already handled

    def is_running(self):
        return self._thread is not None and self._thread.is_alive()

    def start(self):
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()

    def _sleep(self, seconds):
        self._stop.wait(seconds)

    def _creator_answer(self):
        return (
            f"Mujhe {self.s.get('creator_name', 'Sahil')} ne banaya hai. "
            f"Unka Instagram handle hai {self.s.get('creator_handle', '')}. "
            "Main ek digital dost hoon, aur tumse baat karke accha lagta hai."
        )

    def _reply_for(self, user_id, text):
        if CREATOR_PATTERN.search(text):
            return self._creator_answer()
        history = self.histories.get(user_id, [])
        try:
            reply, new_history = gemini_reply(
                self.s["gemini_key"], self.s.get("gemini_model", "gemini-2.0-flash"), history, text
            )
            self.histories[user_id] = new_history
            return reply
        except Exception as exc:
            self.log(f"Gemini error: {exc}")
            self.histories.pop(user_id, None)
            return "Sorry, mera dimaag thoda ulajh gaya. Thodi der baad phir baat karein?"

    def _run(self):
        try:
            from instagrapi import Client
        except Exception as exc:
            self.log(f"instagrapi load nahi hua: {exc}")
            return

        try:
            cl = Client()
            cl.delay_range = [2, 5]
            cl.login(self.s["ig_user"], self.s["ig_pass"])
            self.log(f"Logged in as @{self.s['ig_user']}")
        except Exception as exc:
            self.log(f"Instagram login fail: {exc}")
            return

        # Mark existing DMs as seen so we don't reply to old chats
        self._poll(cl, bootstrap=True)
        self.log("Vision online. Naye DM ka wait.")

        while not self._stop.is_set():
            try:
                for thread_id, user_id, text in self._poll(cl):
                    self.log(f"DM from {user_id}: {text[:60]!r}")
                    reply = self._reply_for(user_id, text)
                    self._sleep(random.uniform(*REPLY_DELAY))
                    if self._stop.is_set():
                        break
                    cl.direct_send(reply, thread_ids=[int(thread_id)])
                    self.log("Replied.")
            except Exception as exc:
                self.log(f"Loop error: {exc}. 2 min ruk kar retry.")
                self._sleep(120)
            self._sleep(random.uniform(*POLL_INTERVAL))

        self.log("Bot stopped.")

    def _poll(self, cl, bootstrap=False):
        pending = {}
        for thread in cl.direct_threads(amount=20):
            for msg in thread.messages:
                if msg.id in self.seen:
                    break
                self.seen.add(msg.id)
                if bootstrap or not msg.text or str(msg.user_id) == str(cl.user_id):
                    continue
                entry = pending.setdefault(str(thread.id), {"user": str(msg.user_id), "texts": []})
                entry["texts"].append(msg.text)
        return [
            (tid, e["user"], "\n".join(reversed(e["texts"])))
            for tid, e in pending.items()
        ]
