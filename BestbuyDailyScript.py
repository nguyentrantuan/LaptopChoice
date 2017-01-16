from __future__ import print_function # Python 2/3 compatibility
import boto3
import requests as rq
from botocore.exceptions import ClientError
import json
import decimal

#import urllib
from bs4 import BeautifulSoup
import pandas as pd
import datetime


# BESTBUY Website Scrapping
Prdname = []
CurrPrice =[]
SavingAmt =[]
SKU=[]
Seller=[]
Link=[]
link = "http://www.bestbuy.ca/en-CA/category/laptops/36711.aspx?type=product&page=1"
page = rq.get(link).text
soup = BeautifulSoup(page,"lxml")
soup.prettify()
lastpage = int(soup.find('li',class_="pagi-dots disabled").find_next_sibling().string)
i=1
for i in range(1,lastpage): #number of pages
    link = "http://www.bestbuy.ca/en-CA/category/laptops/36711.aspx?type=product&page="+str(i)
    page = rq.get(link).text
    soup = BeautifulSoup(page,"lxml")
    soup.prettify()    
    
    for j in soup.find_all('li', class_='listing-item equal-height-container'):
        Prdname.append(j.find(class_= 'prod-title').string)
        if j.find('a') is not None: 
             Link.append("http://www.bestbuy.ca/"+j.find('a').get('href'))
        CurrPrice.append(j.find(class_= 'amount').string)
        if (j.find(class_= 'prod-saving') is not None):
            SavingAmt.append((j.find(class_= 'prod-saving')).span.find_next_sibling().string)
        else: 
            SavingAmt.append("$0")
        SKU.append(j['data-sku'])
        if(j['data-seller-name']!=''):
            Seller.append(j['data-seller-name'])
        else:
            Seller.append("Best Buy")


#### Add scraped data to dataframe
df=pd.DataFrame(SKU,columns=['SKU'])
df['Seller']=Seller
df['ProductName']= Prdname
df['OriginalPrice'] = 1
df['Link']= Link
now = datetime.datetime.now()
today=str(now.strftime("%Y-%m-%d"))
for i in range(len(df['Seller'])):
    df['OriginalPrice'][i]=float(CurrPrice[i][1:]) + float(SavingAmt[i][1:])
    df[today][i]=float(CurrPrice[i][1:])

    
###########Update DynamoDB table######################

# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)

ACCESS_KEY='AKIAJS6EV7XP44PHDEZA'
SECRET_KEY='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'

TABLE_NAME = "Bestbuy"
REGION = "us-east-1"

dynamodb =boto3.resource(
    'dynamodb',
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    region_name='us-east-1',
    endpoint_url="https://dynamodb.us-east-1.amazonaws.com")

table = dynamodb.Table('Bestbuy')

##### Write data to a json file
df.to_json('bestbuy.json',orient='records')


### Update new laptop #####
#### Read data from json file to transfer to DynamoDB

with open('bestbuy.json') as json_file:
    laptops = json.load(json_file, parse_float = decimal.Decimal)
    for lap in laptops:
        SKU = str(lap['SKU'])
        Seller = lap['Seller']
        OriginalPrice = lap['OriginalPrice']
        Link = lap['Link']
        ProductName = lap['ProductName']
        today=str(now.strftime("%Y-%m-%d"))
        CurrentPrice = lap[today]
        today1=str(now.strftime("%Y%m%d"))  
        info = {today1:lap[today]}
        try:
            response=table.put_item(
               Item={
                   'SKU': SKU,
                   'Seller': Seller,
                   'OriginalPrice':OriginalPrice,
                   'Link':Link,
                   'ProductName':ProductName,
                   'CurrentPrice':CurrentPrice,
                   'Prices': info,
                },
                 ConditionExpression="attribute_not_exists(SKU) AND attribute_not_exists(Seller)"
            )
        except ClientError as e:
            if e.response['Error']['Code'] in ["ConditionalCheckFailedException" ,"ClientError"]:
                 print(e.response['Error']['Message'])
            else:
                raise
        else:
            print("Write succeeded:")
            print(json.dumps(response, indent=4, cls=DecimalEncoder))
            
### Update old laptops with new price#####

for i in range(len(df)):
    item = df.loc[i]
    SKU = item.SKU
    Seller = item.Seller
    today=str(now.strftime("%Y-%m-%d"))
    NewPrice = item[today]   
    today=str(now.strftime("%Y%m%d"))        
    UpdateExpression1="set CurrentPrice = :np, Prices.u"+today+"=:np"
    t=str("u"+today)
    info = {t:NewPrice}
    print("Attempting conditional update...")        
        
    try:
        
        response = table.update_item(
            Key={
                'SKU': SKU,
                'Seller': Seller
            },
            UpdateExpression=UpdateExpression1,
            ConditionExpression="CurrentPrice <> :np AND attribute_exists(SKU) AND attribute_exists(Seller) ",
            ExpressionAttributeValues={
                ':np': decimal.Decimal(str(NewPrice)),
            },
            ReturnValues="UPDATED_NEW"
        )
    except ClientError as e:
        if e.response['Error']['Code'] in ["ConditionalCheckFailedException" ,"ClientError"]:
            print(e.response['Error']['Message'],',',SKU)
        else:
            raise
    else:
        print("UpdateItem succeeded:")
        print(json.dumps(response, indent=4, cls=DecimalEncoder))