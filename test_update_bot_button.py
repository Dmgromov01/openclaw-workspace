import os
import sys
import tempfile
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


class GetTokenPathsParameterTest(unittest.TestCase):
    def setUp(self):
        self.env = mock.patch.dict(os.environ, {}, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_resolves_env_token_from_passed_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_file = os.path.join(tmp, ".env")
            with open(env_file, "w", encoding="utf-8") as f:
                f.write(f"TELEGRAM_BOT_TOKEN={FILE_TOKEN}\n")
            token = module.get_token(paths={"env_paths": [env_file], "config_paths": []})
        self.assertEqual(token, FILE_TOKEN)

    def test_resolves_config_token_from_passed_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg_file = os.path.join(tmp, "config.json")
            with open(cfg_file, "w", encoding="utf-8") as f:
                f.write(f'{{"bot_token": "{FILE_TOKEN}"}}')
            token = module.get_token(paths={"env_paths": [], "config_paths": [cfg_file]})
        self.assertEqual(token, FILE_TOKEN)

    def test_defaults_look_next_to_script_first(self):
        script_dir = os.path.dirname(os.path.abspath(module.__file__))
        with mock.patch.object(
            module.os.path, "exists",
            side_effect=lambda p: str(p) == os.path.join(script_dir, ".env"),
        ), mock.patch("builtins.open", mock.mock_open(read_data=f"BOT_TOKEN={FILE_TOKEN}\n")):
            self.assertEqual(module.get_token(), FILE_TOKEN)


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


class MainErrorHandlingTest(unittest.TestCase):
    def setUp(self):
        self.env = mock.patch.dict(os.environ, {}, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_malformed_token_prints_friendly_error(self):
        with mock.patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "not-a-token"}), \
                mock.patch.object(module, "Bot", side_effect=ValueError("Invalid token")), \
                mock.patch("builtins.print") as print_mock:
            module.asyncio.run(module.main())
        print_mock.assert_called_once_with("Ошибка при загрузке токена или создании бота: Invalid token")

    def test_unreadable_env_file_prints_friendly_error(self):
        with mock.patch.object(module.os.path, "exists", side_effect=lambda p: p == "/root/openclaw/.env"), \
                mock.patch("builtins.open", side_effect=PermissionError("Permission denied")), \
                mock.patch("builtins.print") as print_mock:
            module.asyncio.run(module.main())
        print_mock.assert_called_once()
        self.assertIn("Ошибка при загрузке токена или создании бота", print_mock.call_args[0][0])


if __name__ == "__main__":
    unittest.main()
