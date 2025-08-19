from urllib.parse import urlparse
import requests
from services.crawl_data import crawl_id

def is_tiki_url(link: str) -> bool:
    try:
        parsed = urlparse(link)
        return parsed.netloc.endswith("tiki.vn")
    except:
        return False

def is_product_tiki_url(link: str) -> bool:
    try:
        IDs = crawl_id(link_product=link)
        required_keys = ['productId', 'spId', 'sellerId', 'review_count']
        return not any(IDs.get(k) is None for k in required_keys)
    except:
        return False


def main():
    link = "https://tiki.vn/deal-hot?tab=now"
    valid_1 = is_tiki_url(link)
    valid_2 = is_product_tiki_url(link)
    valid = valid_1 and valid_2
    print(valid_1)
    print(valid_2)
    print(valid)

if __name__ =="__main__":
    main()