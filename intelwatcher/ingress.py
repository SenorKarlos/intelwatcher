#! /usr/local/bin/python
# -*- coding: utf-8 -*-
import requests
import re
import json
import time
from requests.utils import dict_from_cookiejar, cookiejar_from_dict
import math
__AUTHOR__ = 'lc4t0.0@gmail.com and ccev'


def get_tiles_per_edge(zoom):
    if zoom > 15:
        zoom = 15
    elif zoom < 3:
        zoom = 3
    else:
        pass
    return [1, 1, 1, 40, 40, 80, 80, 320, 1000, 2000, 2000, 4000, 8000, 16000, 16000, 32000][zoom]


def lng2tile(lng, tpe): # w
    return int((lng + 180) / 360 * tpe);


def lat2tile(lat, tpe): # j
    return int((1 - math.log(math.tan(lat * math.pi / 180) + 1 / math.cos(lat * math.pi / 180)) / math.pi) / 2 * tpe)


def tile2lng(x, tpe):
    return x / tpe * 360 - 180;


def tile2lat(y, tpe):
    n = math.pi - 2 * math.pi * y / tpe;
    return 180 / math.pi * math.atan(0.5 * (math.exp(n) - math.exp(-n)));


def maybe_byte(name):
    try:
        return name.decode()
    except Exception:
        return name


class Tile:
    def __init__(self, x, y):
        self.name = f"15_{x}_{y}_0_8_100"
        self.tries = 0
        self.success = False
        self.fails = 0

    @property
    def failed(self):
        return self.tries > 7


def get_tiles(bbox):
    lower_lon, lower_lat, upper_lon, upper_lat = bbox
    zpe = get_tiles_per_edge(15)
    tiles = []

    lx = lng2tile(lower_lon, zpe)
    ly = lat2tile(lower_lat, zpe)
    ux = lng2tile(upper_lon, zpe)
    uy = lat2tile(upper_lat, zpe)

    for x in range(lx, ux + 1):
        for y in range(uy, ly + 1):
            tiles.append(Tile(x, y))

    return tiles


class IntelMap:
    headers = {
        'accept': '*/*',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'en-US,en;q=0.8',
        'content-type': 'application/json; charset=UTF-8',
        'origin': 'https://intel.ingress.com',
        'referer': 'https://intel.ingress.com/intel',
        'user-agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/90.0.4430.93 Safari/537.36'),
    }
    data_base = {
        'v': '',
    }
    proxy = {
        # 'http': 'socks5://127.0.0.1:1080',
        # 'https': 'socks5://127.0.0.1:1080',
    }

    def __init__(self, cookie):
        self.isCookieOk = False
        self.login(cookie)

    def login(self, cookie):
        try:
            self.cookie_dict = {k.strip(): v for k, v in re.findall(r"(.*?)=(.*?);", cookie)}
            s = requests.Session()
            s.cookies = cookiejar_from_dict(self.cookie_dict)
            test = s.get("https://intel.ingress.com/intel", proxies=self.proxy)
            self.data_base["v"] = re.findall(r'/jsc/gen_dashboard_([\d\w]+).js"', test.text)[0]
            self.r = s
            self.cookie_dict = dict_from_cookiejar(self.r.cookies)
            self.headers.update({"x-csrftoken": self.cookie_dict["csrftoken"]})
            self.isCookieOk = True
        except IndexError:
            self.isCookieOk = False

    def getCookieStatus(self):
        return self.isCookieOk

    def scrape_tiles(self, tiles, portals, log, progress, task):
        if not tiles:
            return
        try:
            data = self.data_base.copy()

            to_scrape = []
            for tile in tiles:
                if not tile.failed:
                    to_scrape.append(tile.name)
                    tile.tries += 1

            if not to_scrape:
                return
            data["tileKeys"] = to_scrape

            now = int(time.time())

            attempts = 0
            while attempts < 4:
                try:
                    result = self.r.post("https://intel.ingress.com/r/getEntities", json=data, headers=self.headers,
                                         proxies=self.proxy)
                    attempts = 10
                except Exception as e:
                    attempts += 1
                    if attempts == 4:
                        log.exception(e)
                        return

            if not result or result.text == "{}" or not result.text:
                self.scrape_tiles(tiles, portals, log, progress, task)
                return
            try:
                result = result.json()["result"]["map"]
            except:
                self.scrape_tiles(tiles, portals, log, progress, task)
                return
            
            errors = []
            for tile in tiles:
                payload = result.get(tile.name)

                if not payload:
                    errors.append(tile)
                    continue

                if "error" in payload.keys():
                    errors.append(tile)
                    continue

                entities = payload.get("gameEntities")
                if not entities:
                    errors.append(tile)
                    continue

                tile.success = True
                progress.update(task, advance=1)
                for entry in entities:
                    if entry[2][0] == "p":
                        p_id = entry[0]
                        p_lat = entry[2][2] / 1e6
                        p_lon = entry[2][3] / 1e6
                        p_name = maybe_byte(entry[2][8])
                        p_img = maybe_byte(entry[2][7])
                        portals.append((p_id, p_name, p_img, p_lat, p_lon, now, now))

            self.scrape_tiles(errors, portals, log, progress, task)
        except Exception as e:
            log.exception(e)
            self.scrape_tiles(tiles, portals, log, progress, task)

    def get_portal_details(self, guid):
        data = self.data_base.copy()
        data["guid"] = guid
        result = self.r.post("https://intel.ingress.com/r/getPortalDetails", json=data, headers=self.headers,
                        proxies=self.proxy)
        try:
            return result.json()
        except Exception as e:
            return None

    # UNUSED

    def get_game_score(self):
        data = self.data_base
        data = json.dumps(data)
        _ = self.r.post('https://intel.ingress.com/r/getGameScore', data=data, headers=self.headers, proxies=self.proxy)
        print(_.text)
        return json.loads(_.text)

    def get_entities(self, tilenames):
        _ = {
          "tileKeys": tilenames,    # ['15_25238_13124_8_8_100']
        }
        data = self.data_base
        data.update(_)
        data = json.dumps(data)
        _ = self.r.post('https://intel.ingress.com/r/getEntities', data=data, headers=self.headers, proxies=self.proxy)
        return json.loads(_.text)

    def get_plexts(self, min_lng, max_lng, min_lat, max_lat, tab='all', maxTimestampMs=-1, minTimestampMs=0,
                   ascendingTimestampOrder=True):
        if minTimestampMs == 0:
            minTimestampMs = int(time.time()*1000)
        data = self.data_base
        data.update({
            'ascendingTimestampOrder': ascendingTimestampOrder,
            'maxLatE6': max_lat,
            'minLatE6': min_lat,
            'maxLngE6': max_lng,
            'minLngE6': min_lng,
            'maxTimestampMs': maxTimestampMs,
            'minTimestampMs': minTimestampMs,
            'tab': tab,
        })
        data = json.dumps(data)
        _ = self.r.post('https://intel.ingress.com/r/getPlexts', headers=self.headers, data=data, proxies=self.proxy)
        return json.loads(_.text)

    def send_plexts(self, lat, lng, message, tab='faction'):
        data = self.data_base
        data.update({
            'latE6': lat,
            'lngE6': lng,
            'message': message,
            'tab': tab,
        })
        data = json.dumps(data)
        _ = self.r.post('https://intel.ingress.com/r/sendPlext', headers=self.headers, data=data, proxies=self.proxy)
        return json.loads(_.text)

    def get_region_score_details(self, lat, lng):
        data = self.data_base
        data.update({
            'latE6': lat,   # 30420109, 104938641
            'lngE6': lng,
        })
        data = json.dumps(data)
        _ = self.r.post('https://intel.ingress.com/r/getRegionScoreDetails', headers=self.headers, data=data,
                        proxies=self.proxy)
        return json.loads(_.text)

