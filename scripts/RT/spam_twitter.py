"""Publish messages to twitter denoting interesting things"""
import datetime
from io import BytesIO

from pyiem import util
import requests

LOG = util.logger()


def main():
    """Do Wonderful things"""
    if datetime.date.today().month < 4 or datetime.date.today().month > 10:
        LOG.info("Tweeting disabled Nov-Mar")
        return
    twitter = util.get_twitter("dailyerosion")
    # assume we run for yesterday
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    yyyymmdd = yesterday.strftime("%Y%m%d")
    media_ids = []
    for vname in ["qc_precip", "avg_delivery"]:
        uri = ("http://depbackend.local/auto/%s_%s_0_%s.png") % (
            yyyymmdd,
            yyyymmdd,
            vname,
        )
        req = util.exponential_backoff(requests.get, uri, timeout=120)
        if req is None or req.status_code != 200:
            print("Download %s failed" % (uri,))
            continue
        bio = BytesIO()
        bio.write(req.content)
        bio.seek(0)
        response = twitter.upload_media(media=bio)
        del bio
        media_ids.append(response["media_id"])

    status = (
        "Daily Erosion output for %s is available "
        "https://dailyerosion.org/map/#%s//qc_precip"
    ) % (yesterday.strftime("%B %-d, %Y"), yyyymmdd)

    res = twitter.update_status(status=status, media_ids=media_ids)
    print(
        ("Posted https://twitter.com/dailyerosion/status/%s")
        % (res["id_str"],)
    )


if __name__ == "__main__":
    main()
