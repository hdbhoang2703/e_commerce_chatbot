from typing import List,Dict
import re
def dict_to_str(data:List[Dict])->List[str]:
    data_str = []
    for dt in data:
        dt_str = ",".join(f"{key}:{value}" for key,value in dt.items())
        data_str.append(dt_str)
        
    return data_str


def main():
    data = [
        {'sản phẩm':'cà phê không đường',
         'lượt bán' : 45,
         'image':["http1:....","http:2...."]},
        {'sản phẩm':'cà phê có đường',
         'lượt bán' : 47,
         'image':["http1:....","http:2...."]}
    ]
    
    data_str = dict_to_str(data=data)
    print(data_str)
    
if __name__ == "__main__":
    main()