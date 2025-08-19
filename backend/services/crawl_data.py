import requests
from bs4 import BeautifulSoup
import json
import asyncio
import aiohttp
import math

def crawl_id(link_product):
    """Get productID, spID, sellerID"""
    
    headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
    }
    
    response = requests.get(url=link_product, headers=headers)
    IDs = {}
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        
        pretty_html = soup.prettify()
        
        script_tag = soup.find("script", {
        "id": "__NEXT_DATA__",
        "type": "application/json"
        })

        if script_tag:
            data = script_tag.string
            data_json = json.loads(data)
            id = data_json.get('props',{}).get('initialState',{}).get('productv2',{}).get('reviewData',{}).get('request')
            
            productId = id.get('productId')
            spId = id.get('spid')
            sellerId = id.get('sellerId')
            
            review_count = data_json.get('props',{}).get('initialState',{}).get('productv2',{}).get('productData').get('response').get('data').get('review_count')
            
            IDs = {'productId': productId, 
                   'spId': spId, 
                   'sellerId':sellerId,
                   'review_count':review_count}
        return IDs
    else:
        return IDs

def crawl_info(link_product):
    """Get information about product"""
    
    headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
    }
    
    info = {}
    
    Id= crawl_id(link_product=link_product)
    
    if Id.get('productId') and Id.get('spId'):
        productId = Id.get('productId')
        spId = Id.get('spId')
        sellerId = Id.get("sellerId")
        info_api = f"https://tiki.vn/api/v2/products/{productId}?platform=web&spid={spId}&version=3"
        comment_api = f"https://tiki.vn/api/v2/reviews?limit=1&include=comments,contribute_info,attribute_vote_summary&sort=score%7Cdesc,id%7Cdesc,stars%7Call&page=1&spid={spId}&product_id={productId}&seller_id={sellerId}"
        comment_response = requests.get(comment_api, headers=headers)
        comment = comment_response.json()
        info_response = requests.get(info_api, headers=headers)
        info = info_response.json()
        
        
        name = info.get('name')
        stars=comment.get('stars')
        original_price = info.get('original_price')
        price = info.get('price')
        quantity_sold = info.get('quantity_sold',{}).get('text')
        rating_average = info.get('rating_average')
        return_policy = info.get('return_policy')
        images = info.get('images',{})
        origin_images = [image.get('base_url') for image in images]
        benefits = [benefit.get('text') for benefit in info.get('benefits')]
        description = info.get('description')
        short_description = info.get('short_description')
        discount = info.get('discount')
        discount_rate = info.get('discount_rate')
        gift_item = info.get('gift_item_title')
        warranty_info = info.get('warranty_info')
        
        specifications_response = info.get('specifications')
        specifications = []
        for spe_response in specifications_response:
            specification = {spe.get('name'):spe.get('value') for spe in spe_response.get('attributes')}
            specifications.append(specification)
            
        info = {'name':name,
                'stars':stars,
                'images':origin_images,
                'price':price,
                'original_price':original_price,
                'discount':discount,
                'discount_rate':discount_rate,
                'quantity_sold':quantity_sold,
                'rating_average':rating_average,
                'description':description,
                'short_description':short_description,
                'return_policy':return_policy,
                'benefits':benefits,
                'gift_item':gift_item,
                'warranty_info':warranty_info,
                'specifications':specifications}      
            
        return info


 
async def fetch_comments(session, comment_api):
    async with session.get(comment_api) as resp:
        data = await resp.json()
        comments= [{'content':cmt.get('content'),
            'title':cmt.get('title'),
            'rating':cmt.get('rating'),
            'images':[image.get('full_path') for image in cmt.get('images')],
            'product_attributes':cmt.get('product_attributes')}
           for cmt in data.get('data',[]) if cmt.get('content')]
        return comments

async def crawl_comments(link_product, batch = 20):
    """Get product's comments"""
    
    headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
    }
    
    comments = []
    Id = crawl_id(link_product=link_product)
    
    if Id.get('productId') and Id.get('spId') and Id.get('sellerId'):
        spId = Id.get('spId')
        productId = Id.get('productId')
        sellerId = Id.get('sellerId')
        total_review = Id.get('review_count',0)
        
        total_page = math.ceil(total_review/20)
        
        async with aiohttp.ClientSession(headers=headers) as session:
            
            for start in range(1, total_page+1, batch):
                end = min(start+batch, total_page + 1)
                tasks = []
                for page in range(start, end):
                    comment_api = f"https://tiki.vn/api/v2/reviews?limit=20&include=comments,contribute_info,attribute_vote_summary&sort=score%7Cdesc,id%7Cdesc,stars%7Call&page={page}&spid={spId}&product_id={productId}&seller_id={sellerId}"
                    tasks.append(fetch_comments(session=session,comment_api=comment_api))
                    
                results = await asyncio.gather(*tasks)
                for comment in results:
                    comments.extend(comment)
        return comments
    else:
        return comments
    
def main():
    link_product = "https://tiki.vn/bo-hop-com-giu-nhiet-lock-lock-lhc8015-910ml-xam-bac-p778124.html?itm_campaign=tiki-reco_UNK_DT_UNK_UNK_pdp-hero-sku_UNK_pdp-widget-top-deal-v2-v1_202508031000_MD_batched_PID.172406876&itm_medium=CPC&itm_source=tiki-reco&spid=172406876"
    
    info = crawl_info(link_product=link_product)
    comments = asyncio.run(crawl_comments(link_product=link_product))
    
    print(info)
    print(len(comments))
if __name__ == "__main__":
    main()
      