import argparse
import sys
import requests
import time
import logging
import coloredlogs

from time import sleep
from concurrent.futures.thread import ThreadPoolExecutor
from rich.progress import Progress

from intelwatcher.ingress import IntelMap, get_tiles, maybe_byte
from intelwatcher.config import Config
from intelwatcher.queries import Queries
from intelwatcher.get_cookie import mechanize_cookie, selenium_cookie
from intelwatcher.stopwatch import Stopwatch


def update_wp(wp_type, points):
    updated = 0
    log.info(f"Found {len(points)} {wp_type}s")
    for wp in points:
        portal_details = scraper.get_portal_details(wp[0])
        if portal_details is not None:
            try:
                pname = maybe_byte(portal_details.get("result")[portal_name])
                queries.update_point(wp_type, pname, maybe_byte(portal_details.get("result")[portal_url]), wp[0])
                updated += 1
                log.info(f"Updated {wp_type} {pname}")
            except Exception as e:
                log.error(f"Could not update {wp_type} {wp[0]}")
                log.exception(e)
        else:
            log.info(f"Couldn't get Portal info for {wp_type} {wp[0]}")
            
    log.info(f"Updated {updated} {wp_type}s")
    log.info("")


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def needed_tiles(tiles):
    return [t for t in tiles if not t.success and t.fails < 3]


def scrape_all(n):
    bbox = list(config.bbox.split(';'))
    tiles = []
    for cord in bbox:
        bbox_cord = list(map(float, cord.split(',')))
        tiles += get_tiles(bbox_cord)

    log.info(f"Total tiles: {len(tiles)}")

    portals = []
    while len(needed_tiles(tiles)) > 0:
        part_tiles = needed_tiles(tiles)[:config.maxtiles]
        scrapetime = Stopwatch()

        with Progress() as progress:
            task = progress.add_task("Scraping Portals", total=len(part_tiles))
            with ThreadPoolExecutor(max_workers=config.workers) as executor:
                for part_tile in chunks(part_tiles, n):
                    executor.submit(scraper.scrape_tiles, part_tile, portals, log, progress, task)

        log.info(f"Done in {scrapetime.pause()}s - Writing portals to DB")

        failed_tiles = [t for t in part_tiles if t.failed]
        if len(failed_tiles) > 0:
            log.warning(f"There were {len(failed_tiles)} tiles that failed")
            for tile in failed_tiles:
                tile.tries = 0
                tile.fails += 1

        queries = Queries(config)
        try:
            queries.update_portal(portals)
        except Exception as e:
            log.error(f"Failed executing Portal Inserts")
            log.exception(e)

        log.info(f"Updated {len(portals)} Portals")

        queries.close()

        if len(tiles) > config.maxtiles:
            portals = []
            success_tiles = len([t for t in tiles if t.success])
            log.info(f"Total tiles scraped: {success_tiles}/{len(tiles)}")

            next_tiles = needed_tiles(tiles)
            if len(next_tiles) > 0:
                log.info((f"Sleeping {config.areasleep} minutes before getting the next "
                          f"{len(next_tiles[:config.maxtiles])} tiles"))

                with Progress() as progress:
                    total_sleep = 60 * config.areasleep
                    task = progress.add_task("Sleeping", total=total_sleep)
                    for i in range(total_sleep):
                        progress.update(task, advance=1)
                        sleep(1)
                    log.info("")


def send_cookie_webhook(text):
    if config.cookie_wh:
        data = {
            "username": "Cookie Alarm",
            "avatar_url": ("https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/"
                           "apple/237/cookie_1f36a.png"),
            "content": config.cookie_text,
            "embeds": [{
                "description": f":cookie: {text}",
                "color": 16073282
            }]
        }
        result = requests.post(config.wh_url, json=data)
        log.info(f"Webhook response: {result.status_code}")


if __name__ == "__main__":
    portal_name = 8
    portal_url = 7

    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--update", action='store_true', help="Updates all Gyms and Stops using Portal info")
    parser.add_argument("-c", "--config", default="config.ini", help="Config file to use")
    parser.add_argument("-w", "--workers", default=0, help="Workers")
    parser.add_argument("-d", "--debug", action='store_true', help="Run the script in debug mode")
    parser.add_argument("-t", "--tiles", default=15, help="How many tiles to scrape per worker")
    args = parser.parse_args()

    # LOG STUFF
    success_level = 25
    if args.debug:
        log_level = "DEBUG"
    else:
        log_level = "INFO"

    log = logging.getLogger(__name__)
    logging.addLevelName(success_level, "SUCCESS")
    def success(self, message, *args, **kws):
        self._log(success_level, message, args, **kws) 
    logging.Logger.success = success
    logHandler = logging.StreamHandler(sys.stdout)
    logHandler.setLevel(logging.INFO)
    log.addHandler(logHandler)
    coloredlogs.DEFAULT_LEVEL_STYLES["debug"] = {"color": "blue"}
    coloredlogs.install(level=log_level, logger=log, fmt="%(message)s")

    log.info("Initializing...")

    config_path = args.config

    config = Config(config_path)

    scraper = IntelMap(config.cookie)

    if not scraper.getCookieStatus():
        log.error("Oops! Looks like you have a problem with your cookie.")
        cookie_get_success = False
        if config.enable_cookie_getting:
            log.info("Trying to get a new one")
            while not cookie_get_success:
                try:
                    if config.cookie_getting_module == "mechanize":
                        config.cookie = mechanize_cookie(config, log)
                        cookie_get_success = True

                    elif config.cookie_getting_module == "selenium":
                        config.cookie = selenium_cookie(config, log)
                        cookie_get_success = True
                except Exception as e:
                    log.error(("Error while trying to get a Cookie - sending a webhook, "
                               "sleeping 1 hour and trying again"))
                    log.exception(e)
                    send_cookie_webhook(("Got an error while trying to get a new cookie - Please check logs. "
                                         "Retrying in 1 hour."))
                    time.sleep(3600)
            scraper.login(config.cookie)
        else:
            send_cookie_webhook("Your Intel Cookie probably ran out! Please get a new one or check your account.")
            sys.exit(1)
    else:
        log.success("Cookie works!")

    log.success("Got everything. Starting to scrape now.")

    if args.update:
        queries = Queries(config)
        gyms = queries.get_empty_gyms()
        stops = queries.get_empty_stops()
        update_wp("Gym", gyms)
        update_wp("Stop", stops)
        queries.close()
        sys.exit()

    if int(args.workers) > 0:
        config.workers = int(args.workers)

    if int(args.tiles) > 25:
        log.error("Please use a -t count below 25")
        sys.exit(1)

    time = Stopwatch()
    scrape_all(int(args.tiles))
    log.success(f"Total runtime: {time.pause()} seconds")
