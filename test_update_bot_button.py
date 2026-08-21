import os
import sys
import unittest
from unittest import mock

import update_bot_button as module

ENV_TOKEN = "123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefgh"
FILE_TOKEN = "9876543210:" + "Z" * 35


class GetTokenResolutionTest(unittest.TestCase):
    def setUp(self):
        self.env = mock.patch.dict(os.environ, {}, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_env_var_wins_over_files(self):
        with mock.patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": ENV_TOKEN}), \
                mock.patch.object(module.os.path, "exists", return_value=True), \
                mock.patch("builtins.open", mock.mock_open(read_data=f"TELEGRAM_BOT_TOKEN={FILE_TOKEN}\n")):
            self.assertEqual(module.get_token(), ENV_TOKEN)

    def test_bot_token_env_var_is_accepted(self):
        with mock.patch.dict(os.environ, {"BOT_TOKEN": ENV_TOKEN}), \
                mock.patch.object(module.os.path, "exists", return_value=True), \
                mock.patch("builtins.open", mock.mock_open(read_data="")):
            self.assertEqual(module.get_token(), ENV_TOKEN)

    def test_dotenv_fallback(self):
        with mock.patch.object(module.os.path, "exists", side_effect=lambda p: p == "/root/openclaw/.env"), \
                mock.patch("builtins.open", mock.mock_open(read_data=f"TELEGRAM_BOT_TOKEN={FILE_TOKEN}\n")):
            self.assertEqual(module.get_token(), FILE_TOKEN)

    def test_config_fallback(self):
        config = "/root/openclaw/config.json"
        with mock.patch.object(module.os.path, "exists", side_effect=lambda p: p == config), \
                mock.patch("builtins.open", mock.mock_open(read_data=f'{{"bot_token": "{FILE_TOKEN}"}}')):
            self.assertEqual(module.get_token(), FILE_TOKEN)

    def test_returns_none_when_token_missing(self):
        with mock.patch.object(module.os.path, "exists", return_value=False):
            self.assertIsNone(module.get_token())


class ArgvTokenRejectionTest(unittest.TestCase):
    def test_argv_token_is_not_accepted(self):
        module_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "update_bot_button.py")
        with open(module_path, encoding="utf-8") as f:
            source = f.read()
        def _close(coro):
            coro.close()

        with mock.patch.object(module.asyncio, "run", side_effect=_close) as run_mock, \
                mock.patch.dict(os.environ, {}, clear=True), \
                mock.patch.object(module.os.path, "exists", return_value=False), \
                mock.patch("builtins.print"):
            old_argv = sys.argv
            sys.argv = ["update_bot_button.py", ENV_TOKEN]
            try:
                exec(compile(source, module_path, "exec"), {"__name__": "__main__"})
            finally:
                sys.argv = old_argv
            self.assertIsNone(os.environ.get("TELEGRAM_BOT_TOKEN"))
        run_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
