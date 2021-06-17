from configparser import ConfigParser


class Config:
    def __init__(self, config_path):
        config_file = ConfigParser()
        config_file.read(config_path)

        self.bbox = config_file.get("Config", "bbox")
        self.cookie_wh = config_file.getboolean("Config", "cookie_webhooks")
        self.cookie_text = config_file.get("Config", "custom_cookie_text", fallback="")
        self.wh_url = config_file.get("Config", "webhook_url")
        self.workers = config_file.getint("Config", "workers", fallback=1)
        self.maxtiles = config_file.getint("Config", "max_tiles", fallback=450)
        self.areasleep = config_file.getint("Config", "sleep_between_areas", fallback=3)

        self.scan_type = config_file.get("DB", "scanner").lower()
        self.db_name_scan = config_file.get("DB", "scanner_db_name")
        self.db_name_portal = config_file.get("DB", "portal_db_name")

        self.db_host = config_file.get("DB", "host")
        self.db_port = config_file.getint("DB", "port")
        self.db_user = config_file.get("DB", "user")
        self.db_password = config_file.get("DB", "password")

        self.scan_db_host = config_file.get("DB", "scan_host", fallback=self.db_host)
        self.scan_db_port = config_file.getint("DB", "scan_port", fallback=self.db_port)
        self.scan_db_user = config_file.get("DB", "scan_user", fallback=self.db_user)
        self.scan_db_password = config_file.get("DB", "scan_password", fallback=self.db_password)

        self.enable_cookie_getting = config_file.getboolean("Ingress Login", "enable", fallback=False)
        self.cookie_getting_module = config_file.get("Ingress Login", "module", fallback="mechanize").lower()
        self.ingress_user = config_file.get("Ingress Login", "user", fallback="")
        self.ingress_password = config_file.get("Ingress Login", "password", fallback="")

        self.ingress_login_type = config_file.get("Selenium", "login_type", fallback="google").lower()
        self.headless_mode = config_file.getboolean("Selenium", "headless_mode", fallback=True)
        self.webdriver = config_file.get("Selenium", "driver", fallback="chrome").lower()

        with open("cookie.txt", encoding="utf-8", mode="r+") as cookie:
            self.cookie = cookie.read()
