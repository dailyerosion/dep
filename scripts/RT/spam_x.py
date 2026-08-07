"""Publish message to X when daily erosion output is available."""

import datetime
from io import BytesIO

import requests
import tweepy
from pyiem.database import sql_helper, with_sqlalchemy_conn
from pyiem.util import exponential_backoff, get_properties, logger
from sqlalchemy.engine import Connection

LOG = logger()


@with_sqlalchemy_conn("iembot")
def get_client(conn: Connection | None = None):
    """Do the tweeting."""
    props = get_properties()
    res = conn.execute(
        sql_helper("""
        select access_token, access_token_secret
        from iembot_twitter_oauth o JOIN iembot_accounts a on
        (o.iembot_account_id = a.id) WHERE o.screen_name = 'dailyerosion'
        """)
    )
    if res.rowcount == 0:
        raise ValueError("No oauth for dailyerosion")
    row = res.mappings().fetchone()
    auth = tweepy.OAuth1UserHandler(
        props.get("bot.twitter.consumerkey"),
        props.get("bot.twitter.consumersecret"),
        row["access_token"],
        row["access_token_secret"],
    )
    client = tweepy.Client(
        consumer_key=props.get("bot.twitter.consumerkey"),
        consumer_secret=props.get("bot.twitter.consumersecret"),
        access_token=row["access_token"],
        access_token_secret=row["access_token_secret"],
    )
    return auth, client


def main():
    """Do Wonderful things"""
    if datetime.date.today().month < 4 or datetime.date.today().month > 10:
        LOG.warning("Tweeting disabled Nov-Mar")
        return
    auth, twitter = get_client()
    v1client = tweepy.API(auth)
    # assume we run for yesterday
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    yyyymmdd = yesterday.strftime("%Y%m%d")
    media_ids = []
    for vname in ["qc_precip", "avg_delivery"]:
        uri = (
            f"http://depbackend.local/auto/{yyyymmdd}_{yyyymmdd}_0_{vname}.png"
        )
        req = exponential_backoff(requests.get, uri, timeout=120)
        if req is None or req.status_code != 200:
            LOG.warning("Download %s failed", uri)
            continue
        bio = BytesIO()
        bio.write(req.content)
        bio.seek(0)
        media = v1client.media_upload(f"{vname}.png", file=bio)
        media_ids.append(media.media_id)

    status = (
        f"Daily Erosion output for {yesterday:%B %-d %Y} is available "
        f"https://dailyerosion.org/map/#{yyyymmdd}//qc_precip"
    )

    res = twitter.create_tweet(text=status, media_ids=media_ids)
    LOG.warning("Posted https://x.com/dailyerosion/status/%s", res.data["id"])


if __name__ == "__main__":
    main()
