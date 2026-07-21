import traceback

try:
    from scripts.oklink_scraper import scrape_oklink_tags
except Exception as e:
    traceback.print_exc()
