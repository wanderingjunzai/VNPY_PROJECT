from pymongo import MongoClient

def check_saved_data():
    # 连接数据库
    client = MongoClient('localhost', 27017)
    db = client.crypto_trading
    collection = db.market_data
    
    # 查询数据
    count = collection.count_documents({"symbol": "BTCUSDT"})
    first = collection.find_one({"symbol": "BTCUSDT"})
    last = collection.find_one({"symbol": "BTCUSDT"}, sort=[("datetime", -1)])
    
    print(f"数据库中的记录数: {count}")
    print(f"第一条数据时间: {first['datetime']}")
    print(f"最后一条数据时间: {last['datetime']}")

if __name__ == "__main__":
    check_saved_data()