# -*- coding: utf-8 -*-
"""
Created on Thu Jan 12 16:00:31 2017

@author: tyyg
"""

from __future__ import print_function # Python 2/3 compatibility
import boto3
import json
import decimal
import pandas as pd
from sqlalchemy import create_engine
import requests as rq
from bs4 import BeautifulSoup



# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)

ACCESS_KEY='xxx'
SECRET_KEY='xxx'

TABLE_NAME = "Bestbuy"
REGION = "us-east-1"

### Create dataframes and list to store data
laptops = []
attributes=['Video Memory Configuration','rating','NoRaters','SKU','seller','link','Screen Size','Touchscreen Display','Processor Type','Hard Drive Capacity','RAM Size','Dedicated Video Memory Size','SSD Function'] 
laptopdf=pd.DataFrame(columns=attributes)
pricedf=pd.DataFrame(columns=['SKU','Date','Price'])


def ReadFromDynamoDB():
    dynamodb =boto3.resource(
        'dynamodb',
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        region_name='us-east-1',
        endpoint_url="https://dynamodb.us-east-1.amazonaws.com")
    
    table = dynamodb.Table('Bestbuy')    
    response = table.scan()
    ### Write all Data to a Json file
    with open('data.json', 'w') as outfile:
        for i in response['Items']:
            json.dump(i, outfile, cls=DecimalEncoder, sort_keys=True, separators=(',', ':'))
            outfile.write('\n')
                
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                ExclusiveStartKey=response['LastEvaluatedKey']
                )
        
            for i in response['Items']:
                json.dump(i, outfile, cls=DecimalEncoder, sort_keys=True, separators=(',', ':'))
                outfile.write('\n')
                
    #### Read data back to laptops[] list
    with open('data.json') as f:
        for line in f:
            json_object = json.loads(line)
            laptops.append(json_object)
    return

def CPUpoint(cputype):
    ### Read CPU ranks produced by www.tomshardware.com
    CPUrating = pd.read_excel('CPUrank.xlsx','CPUrank')
    for i in ['Quad-Core','ICD','Intel','Core','intel','core','Quad','AMD','Generation','7th','6th','Processor','5th','4th','(',')','Cache',';','2M','up to 2.56 GHz','NCD']:
        cputype=cputype.replace(i,'')
    while '  ' in cputype:
        cputype = cputype.replace('  ',' ')
    cputype=cputype.strip()
    if cputype=='i5': return 54
    if cputype=='Celeron': return 37
    if cputype=='i7': return 62
    if cputype=='M': return 50
    if cputype in ['Atom','Rockchip RK3288','Rockchip RK3288C']: return 34
    for i in range(len(CPUrating)):
        if cputype.lower() in CPUrating.loc[i,'Model']:
            return CPUrating.loc[i,'Rating']
    return 0


def RAMpoint(ramtype):
    ramtype=str(ramtype)
    temp=''
    while (ramtype[0]) in '0,1,2,3,4,5,6,7,8,9'.split(','):
        temp=temp+ramtype[0]
        if(len(ramtype)>1): ramtype=ramtype[1:]
        else: break
    try: 
        temp=int(temp)
    except ValueError:
        return 0
   # if temp=='none': return 0
    temp=int(temp)
    if temp>=32 : return 100
    if temp>=24 : return 90
    if temp>=16 : return 80
    if temp>=8 : return 70
    if temp>=6 : return 60
    if temp>=4 : return 40
    if temp>=2 : return 20
    return 5


def HDDpoint(hdd):
    point=5
    if '2TB' in hdd or '2 TB' in hdd: point = point+90
    if '1TB' in hdd or '1 TB' in hdd or '1024 GB' in hdd :point=point + 60
    if '750' in hdd: point = point +40
    if '500' in hdd: point=point+30
    if '128' in hdd: point= point+50 
    if '256' in hdd: point= point+90
    if '512' in hdd: point = point + 170
    if '32' in hdd or '64' in hdd or 'NAND' in hdd: point =point + 10
    return point

def Graphpoint(ram):
    ramtype=str(ram)
    temp=''
    while (ramtype[0]) in '0,1,2,3,4,5,6,7,8,9'.split(','):
        temp=temp+ramtype[0]
        if(len(ramtype)>1): ramtype=ramtype[1:]
        else: break
    try: 
        temp=int(temp)
    except ValueError:
        return 0
   # if temp=='none': return 0
    temp=int(temp)
    if('MB' in ram): temp=temp/1024
    if temp>=8 : return 100
    if temp>=6 : return 90
    if temp>=4 : return 60
    if temp>=3 : return 50
    if temp>=2 : return 40
    if temp>=1 : return 35
    return 30

def ReviewPoint(point,num):
    if point >=3 and num >5: return 50
    if point >=3 and num <=5: return 25
    if point <3 and num >5: return -50
    if point <3 and num <5: return -10

    
### scrape Bestbuy for laptop's specs 
def GetLaptopSpecs():
    row = -1 ### row for laptopdf
    row2=-1  ### row for pricedf
    i=0
    for i in range(len(laptops)):
        lap=laptops[i]
        #link = "http://www.bestbuy.ca/en-CA/product/acer-acer-aspire-e-15-6-laptop-black-iron-intel-i3-6100u-1tb-hdd-8gb-ram-windows-10-e5-574-322e/10409027.aspx?icmp=Homepage_SectionC_Acer_laptops"
        link = lap['Link'] 
        page = rq.get(link).text
        soup = BeautifulSoup(page,"lxml")
        soup.prettify()
        if(soup.title.string != '\r\n\tPage Not Found - Best Buy Canada - Best Buy Canada\r\n' and soup.title.string !='\r\n\tPage introuvable - Best Buy Canada - Best Buy Canada\r\n'):
            row=row+1
            laptopdf.loc[row,'link']=link
            if (soup.find(class_="rating-score font-xs colour-dark-grey inline-block margin-right-one") != None):
                laptopdf.loc[row,'rating'] = float(soup.find(class_="rating-score font-xs colour-dark-grey inline-block margin-right-one").string.strip())
                noofraters=soup.find(class_="rating-number font-xs colour-dark-grey inline-block margin-right-one").string.strip()
                laptopdf.loc[row,'NoRaters']= float(noofraters.replace('(','').replace(')',''))
            else:
                laptopdf.loc[row,'rating'] = 0
                laptopdf.loc[row,'NoRaters']=0
            
            laptopdf.loc[row,'imgsrc'] = soup.find(class_="product-image")['src']
            laptopdf.loc[row,'SKU']=lap['SKU']
            laptopdf.loc[row,'ProductName']=lap['ProductName']
            laptopdf.loc[row,'CurrentPrice']=lap['CurrentPrice']
            laptopdf.loc[row,'seller']=lap['Seller']
            for j in soup.find_all(class_='attribute-key span5'):
                if (j.find_next_sibling().find('span').string !=' '):
                    if (j.find('a') is not None):
                        temp=j.find('a').string
                    else:
                        temp=j.find('span').string    
                    if temp in attributes:
                        laptopdf.loc[row,temp]=j.find_next_sibling().find('span').string
                    #mydict[j.find('a').string]=j.find_next_sibling().find('span').string
            for j in lap['Prices']:
                row2=row2+1
                pricedf.loc[row2,'SKU']=lap['SKU']
                date=pd.datetime
                if j=='2016-12-22': date = pd.to_datetime('2016-12-21')
                elif j=='2016-12-23': date = pd.to_datetime(j)
                else:
                    if(j[0]=='u'): 
                        temp=j[1:] 
                    else: 
                        temp=j
                    date=pd.to_datetime(temp[:4]+'-'+temp[4:6]+'-'+temp[6:8])
                pricedf.loc[row2,'Date']=date
                pricedf.loc[row2,'Price']=lap['Prices'][j]
        print(row)
        laptopdf=laptopdf.fillna('none')
    return  
        
        
#######Point calculation for each laptop based on its specs
def PointCalculation():
    for i in range(len(laptopdf.index)):
        temp1=HDDpoint(laptopdf.loc[i,'Hard Drive Capacity'])
        temp2=RAMpoint(laptopdf.loc[i,'RAM Size'])
        temp3=CPUpoint(laptopdf.loc[i,'Processor Type'])*1.5
        temp4=0
        if laptopdf.loc[i,'Video Memory Configuration']=='Dedicated':
            temp4 = Graphpoint(laptopdf.loc[i,'Dedicated Video Memory Size'])
        total=0
        temp5=0
        if laptopdf.loc[i,'Touchscreen Display'] =='Yes': total = 50 #touch screen bonus point
        if laptopdf.loc[i,'rating'] >0: temp5 = ReviewPoint(laptopdf.loc[i,'rating'],laptopdf.loc[i,'NoRaters'])
        total=temp1+temp2+temp3+temp4+temp5
        laptopdf.loc[i,'TotalPoint']=total
        laptopdf.loc[i,'HDD point']=temp1
        laptopdf.loc[i,'RAM point']=temp2
        
        laptopdf.loc[i,'CPU point']=temp3
        laptopdf.loc[i,'Graphic point']=temp4
        laptopdf.loc[i,'Review point']=temp5
        laptopdf.loc[i,'Bestmatch']=laptopdf.loc[i,'CurrentPrice']/total
        print(i)
    return

if __name__ == '__main__':
    
    laptops = []
    attributes=['Video Memory Configuration','rating','NoRaters','SKU','seller','link','Screen Size','Touchscreen Display','Processor Type','Hard Drive Capacity','RAM Size','Dedicated Video Memory Size','SSD Function'] 
    laptopdf=pd.DataFrame(columns=attributes)
    pricedf=pd.DataFrame(columns=['SKU','Date','Price'])

    ReadFromDynamoDB()
    GetLaptopSpecs()
    PointCalculation()
    
    ### Convert to solve encoding problems
    laptopdf.to_csv('laptop.csv')
    with open('laptop.csv', encoding="latin-1") as datafile:  laptopdf=pd.read_csv(datafile)
    
    ### Write data to MySQL
    conn_str = "mysql+mysqldb://bob:Funnysun333@54.90.116.35:3306/test"
    engine = create_engine(conn_str)
    laptopdf.to_sql('laptops',engine,if_exists='replace')   
    pricedf.to_sql('prices',engine,if_exists='replace')   

    
    """

## CHARACTER PARROT TABLE ###
table_characters = Table('characters', meta,
    Column('Character', TEXT, nullable=True),
    Column('actor_id', Integer, ForeignKey('actors.actor_id'))
)


"""


"""
import MySQLdb
db=MySQLdb.connect(host="54.90.116.35",port=3306,user="bob",
                  passwd="Funnysun333",db="test")

laptopdf.to_sql('test',conn,flavor='mysql', if_exists='replace',index=True)
"""
"""

        
        
df=pd.DataFrame(SKU,columns=['SKU'])
df['ProductName']= Prdname
df['date'] = date
df['price']= price
        

import json
data = {'key': 'value', 'whatever': [1, 42, 3.141, 1337]}
with open('data.json', 'w') as outfile:
    json.dump(data, outfile, indent=4, sort_keys=True, separators=(',', ':'))

"""    
        

