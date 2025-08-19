from .crawl_data import crawl_id, crawl_info, crawl_comments
import asyncio
from typing import List, Dict

def get_info(link_product)-> Dict:
    id = crawl_id(link_product)
    detail_info = crawl_info(link_product)
    info = id | detail_info
    return info

async def get_comments(link_product) -> List[Dict]:
    id = crawl_id(link_product)
     
    comments = []
    raw_comments = await crawl_comments(link_product)
    for comment in raw_comments:
        new_comment = {'productId': id['productId'],
                       'spId':id['spId'],
                       'sellerId':id['sellerId']} | comment
        comments.append(new_comment)
    
    return comments    
    
def main():
    link_product = "https://tiki.vn/am-dun-nuoc-sieu-toc-elmich-1-8l-kee-1778-p263580125.html?spid=273595020"
    info = get_info(link_product=link_product)
    print(info)
    #'productId': 174599595, 'spId': '187960118', 'sellerId': 192004
    #'productId': 119706880, 'spId': '119706881', 'sellerId': 215908
    # comments = get_comments(link_product)
    # print(comments[0])
if __name__ == "__main__":
    main()