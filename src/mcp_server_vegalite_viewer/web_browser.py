import json
import logging
import os
import threading
import time
import webbrowser

from . import LOCALHOST

WEB_BROWSER_REOPEN_SECS = 300
WEB_BROWSER_CONTROLLER_STATE_FILE = os.path.join(
    os.path.expanduser("~"), ".mcp", __package__, ".web_browser_controller_state.json"
)
WEB_BROWSER_REOPEN_DISABLED_UNTIL_KEY = "reopen_disabled_until"

logger = logging.getLogger(__name__)


class WebBrowserController:
    def __init__(self, reopen_secs=WEB_BROWSER_REOPEN_SECS):
        self._opened = False
        self._reopen_timer = None
        self._reopen_secs = reopen_secs
        self._load_state()

    def _load_state(self):
        if os.path.exists(WEB_BROWSER_CONTROLLER_STATE_FILE):
            try:
                # Load persisted state
                with open(WEB_BROWSER_CONTROLLER_STATE_FILE) as f:
                    # Do nothing if state file is empty or contains only whitespace
                    content = f.read().strip()
                    if not content:
                        return

                    # Try to parse as JSON
                    state = json.loads(content)
                    reopen_disabled_until = state.get(
                        WEB_BROWSER_REOPEN_DISABLED_UNTIL_KEY, 0
                    )

                    # Adjust runtime state
                    now = time.time()
                    if now < reopen_disabled_until:
                        self._opened = True
                        delay = reopen_disabled_until - now
                        self._reopen_timer = threading.Timer(delay, self._enable)
                        self._reopen_timer.daemon = True
                        self._reopen_timer.start()
                    else:
                        self._opened = False
            except json.JSONDecodeError as e:
                logger.warning(f"State file contains invalid JSON: {e}")
                self._opened = False
            except Exception as e:
                logger.warning(f"Failed to load web browser controller state: {e}")
                self._opened = False

    def _save_state(self, reopen_disabled_until):
        try:
            # Make sure that parent folder of state file exists
            os.makedirs(
                os.path.dirname(WEB_BROWSER_CONTROLLER_STATE_FILE), exist_ok=True
            )

            # Persit current state
            with open(WEB_BROWSER_CONTROLLER_STATE_FILE, "w") as f:
                state = {WEB_BROWSER_REOPEN_DISABLED_UNTIL_KEY: reopen_disabled_until}
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save web browser controller state: {e}")

    def _disable(self):
        logger.info(
            f"Disabling automatic opening of web browser for the next {self._reopen_secs}s"
        )
        self._opened = True

        # Start reopen timer
        if self._reopen_timer is not None:
            self._reopen_timer.cancel()
        self._reopen_timer = threading.Timer(self._reopen_secs, self._enable)
        self._reopen_timer.daemon = True
        self._reopen_timer.start()

        # Persist next reopen time
        reopen_disabled_until = time.time() + self._reopen_secs
        self._save_state(reopen_disabled_until)

    def _enable(self):
        logger.info("Re-enabling automatic opening of web browser")
        self._opened = False

        # Clear reopen timer
        self._reopen_timer = None

        # Clear persisted next reopen time
        self._save_state(0)

    def open(self, port: int):
        if not self._opened:
            logger.info(
                f"Opening viewer app running at http://{LOCALHOST}:{port} in default web browser"
            )
            webbrowser.open(f"http://{LOCALHOST}:{port}")
            self._disable()


# Create a singleton instance for use throughout the app
web_browser = WebBrowserController()
