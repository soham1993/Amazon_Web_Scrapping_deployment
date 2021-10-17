# -*- coding: utf-8 -*-
"""
Created on Thu Oct 14 22:18:45 2021

@author: SOHAM
"""
from flask import Flask, request, render_template, session, redirect
from textblob import TextBlob as tb
import pandas as pd
import numpy as np
import regex as re
import nltk
nltk.download('punkt')
from nltk.tokenize import word_tokenize
from nltk import pos_tag
nltk.download('stopwords')
from nltk.corpus import stopwords
nltk.download('wordnet')
from nltk.corpus import wordnet
from nltk.stem import WordNetLemmatizer
nltk.download('averaged_perceptron_tagger')
import requests
from bs4 import BeautifulSoup 
from time import sleep
from urllib.request import urlopen as uReq


def get_productdetails(searchterm):
    print('Fetching product list')
    searchterm='+'.join(searchterm.split())
    headers = {
    'Accept-Encoding': 'gzip, deflate, sdch',
    'Accept-Language': 'en-US,en;q=0.8',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Referer': 'http://www.wikipedia.org/',
    'Connection': 'keep-alive',
}

    url='https://www.amazon.in/s?k='+searchterm
    sleep(2)
    uClient = uReq(url)
    source = uClient.read()
    uClient.close()
    sleep(2)
    #source = requests.get(url,headers=headers).text
    soup = BeautifulSoup(source, 'html.parser')
    #print(soup)
    Names = []
    #loop to extract the ur of the product 
    for i in soup.find_all('a', class_='a-link-normal a-text-normal'):
        #time.sleep(5)
        try:
            string = i.attrs['href']
            Names.append('https://www.amazon.in'+ string)
        except:
            pass
    Product_Title,price,Product_url=[],[],[]
    Names=Names[:min(15,len(Names))]
    #print(len(Names))
    ##Extracting the title ,price of the product
    print(len(Names))
    for i in Names:
        try:
            uClient = uReq(i)
            source2 = uClient.read()
            uClient.close()
            #source2 = requests.get(i,headers=headers).text
            soup2 = BeautifulSoup(source2, 'html.parser')
            Title = soup2.find('span', id='productTitle').text
            Title = Title.strip()
           
            try:    
                        Price1 = soup2.find('span', id="priceblock_dealprice").text
                        
                        Price1 = Price1.strip()
                        Price1=Price1.replace("₹","")
            except:
                        Price1 = ''
                
            try:
                        Price2 = soup2.find('span', id="priceblock_ourprice").text
                        Price2= Price2.strip()
                        Price2=Price2.replace("₹","")
            except:
                        Price2=''
               
            if Price1=='' and Price2!='':
                    Price=Price2
            elif Price1!='' and Price2=='':
                    Price=Price1
            else:
                    if Price1<Price2:
                        Price=Price1
                    else:
                        Price=Price2
                    
            Product_Title.append(Title)
            price.append(Price)
            Product_url.append(i)
        except:
            pass
            
    cols=['Product_Title','Asin_Num','Price(INR)','Product_url']
    
    df=pd.DataFrame()
    df['Product_Title']=Product_Title
    df['Price(INR)']=price
    df['Product_url']=Product_url
    df['Asin_Num']=df['Product_url'].apply(lambda x:str(x.split('/')[5]))
    df=df[cols]
    df=df.drop_duplicates(subset=['Asin_Num'])
    return df

def get_productreviews(productlist):
    print('Fetching Product reviews')
    reviewlist = []
    product_url=list(productlist['Product_url'].values)
    print(product_url)
    #print(product_url)
    def get_soup(url):
        uClient = uReq(url)
        r = uClient.read()
        uClient.close()
        #sleep(2)
        #r = requests.get(url)
        soup = BeautifulSoup(r, 'html.parser')
        return soup
    def get_reviews(soup,asin):
        reviews = soup.find_all('div', {'data-hook': 'review'})
        try:
            for item in reviews:
                    
                    review={
                    
                    'names' : item.find_all('span',class_='a-profile-name')[0].get_text(),
                    'title': item.find('a', {'data-hook': 'review-title'}).text.strip(),
                    'rating':  float(item.find('i', {'data-hook': 'review-star-rating'}).text.replace('out of 5 stars', '').strip()),
                    'body': item.find('span', {'data-hook': 'review-body'}).text.strip(),
                    'asin':asin}
                    
                    
                    reviewlist.append(review)
        except:
                
                pass
           
        
    for url in product_url:
        product_name,asin_num=str(url.split('/')[3]),str(url.split('/')[5])
        print(product_name)
        for x in range(1,6):
            #print('https://www.amazon.in/'+product_name+'/product-reviews/'+asin_num+'/ref=cm_cr_getr_d_paging_btm_next_'+str(x)+'?ie=UTF8&reviewerType=all_reviews&pageNumber='+str(x))
            soup = get_soup(f'https://www.amazon.in/'+product_name+'/product-reviews/'+asin_num+'/ref=cm_cr_getr_d_paging_btm_next_'+str(x)+'?ie=UTF8&reviewerType=all_reviews&pageNumber='+str(x))
            print(f'Getting page: {x}')
            get_reviews(soup,asin_num)
            print(len(reviewlist))
            if not soup.find('li', {'class': 'a-disabled a-last'}):
                pass
            else:
                break
            
    cust_name,title,rating,body,asin=[],[],[],[],[]   
    
    for i in range (len(reviewlist)):
        cust_name.append(reviewlist[i]['names'])
        title.append(reviewlist[i]['title'])
        rating.append(reviewlist[i]['rating'])
        body.append(reviewlist[i]['body'])
        asin.append(reviewlist[i]['asin'])
        
    df=pd.DataFrame()
    df["Customer_Name"]=cust_name
    df['Asin_Num']=asin
    df["ReviewTitle"]=title
    df['Rating']=rating
    df['Description']=body
    
    
    return df 

def get_finallist(reviewlist,prod_detail):
    print('Preparing Final list')
    data=reviewlist.copy()
    data=data.dropna()
    data=data.drop(['Customer_Name','ReviewTitle'],axis=1)
    df=pd.DataFrame()
    # Define a function to clean the text
    def clean(text):
    # Removes all special characters and numericals leaving the alphabets
        text = re.sub('[^A-Za-z]+', ' ', text)
        return text
    
    # Cleaning the text in the review column
    data['Cleaned_Reviews'] =data['Description'].apply(clean)
    # POS tagger dictionary
    pos_dict = {'J':wordnet.ADJ, 'V':wordnet.VERB, 'N':wordnet.NOUN, 'R':wordnet.ADV}
    def token_stop_pos(text):
        tags = pos_tag(word_tokenize(text))
        newlist = []
        for word, tag in tags:
            
            if word.lower() not in set(stopwords.words('english')):
                newlist.append(tuple([word, pos_dict.get(tag[0])]))
        return newlist
    
    data['POS_Tagged'] = data['Cleaned_Reviews'].apply(token_stop_pos)
    ##lemmatization
    wordnet_lemmatizer = WordNetLemmatizer()
    def lemmatize(pos_data):
        lemma_rew = " "
        for word, pos in pos_data:
            if not pos:
                lemma = word
                lemma_rew = lemma_rew + " " + lemma
            else:
                lemma = wordnet_lemmatizer.lemmatize(word, pos=pos)
                lemma_rew = lemma_rew + " " + lemma
        return lemma_rew
    
    data['Lemma'] = data['POS_Tagged'].apply(lemmatize)
    data=data[['Asin_Num','Lemma','Rating']]
    # function to calculate polarity
    def getPolarity(review):
            return tb(review).sentiment.polarity  
        
    data['Polarity'] = data['Lemma'].apply(getPolarity) 
    def high_polarity_analysis(x):
        if x>0.5:
            return 1
        else:
            return 0
    def positive_review(x):
        if x>0 and x<=0.5:
            return 1
        else:
            return 0
    def negative_review(x):
        if x<=0 and x>-0.5:
            return 1
        else:
            return 0
    def high_negative_polarity(x):
        if x<=-0.5:
            return 1
        else:
            return 0
    data['Extremely_Positive_Review']=data['Polarity'].apply(lambda x:high_polarity_analysis(x))
    data['Moderately_Positive_Review']=data['Polarity'].apply(lambda x:positive_review(x))
    data['Moderately_Negative_Review']=data['Polarity'].apply(lambda x:negative_review(x))
    data['Extremely_Negative_Review']=data['Polarity'].apply(lambda x:high_negative_polarity(x))
    df=pd.pivot_table(data,index=['Asin_Num'],values=['Extremely_Positive_Review','Moderately_Positive_Review','Moderately_Negative_Review','Extremely_Negative_Review'],aggfunc=np.sum).reset_index()
    df1=pd.pivot_table(data,index=['Asin_Num'],values='Rating',aggfunc=np.median).reset_index()
    #df['High_Positive_Review']=(((df['high_positive_review']/(df['positive_review']+df['negative_review']))*100).astype(float))
    #df['High_Positive_Review']=df['High_Positive_Review'].round(2)
    #df['Positive_review']=((df['positive_review']/(df['positive_review']+df['negative_review']))*100).astype(float)
    #df['Positive_review']=df['Positive_review'].round(2)
    df['Total_Review_Scrapped']=df['Extremely_Positive_Review']+df['Extremely_Negative_Review'] + df['Moderately_Negative_Review'] +df['Moderately_Positive_Review']              
    df=df.merge(df1,how='outer',on='Asin_Num')
    df=df.rename(columns={'Rating':'Median_Rating'})  
    df=df.sort_values(by=['Extremely_Positive_Review','Moderately_Positive_Review','Moderately_Negative_Review','Extremely_Negative_Review'],ascending=False)
    #df['High_Positive_Review']=df['High_Positive_Review'].astype(str)+'%'
    #df['Positive_review']=df['Positive_review'].astype(str)+'%'
    #df=df.drop(['high_positive_review','negative_review','positive_review'],axis=1)
    df['Rank']=np.arange(1,df.shape[0]+1)
    df_final=df.merge(prod_detail,on='Asin_Num',how='left')
    col_name=['Rank','Product_Title','Price(INR)','Median_Rating','Total_Review_Scrapped','Extremely_Positive_Review','Moderately_Positive_Review','Extremely_Negative_Review','Moderately_Negative_Review','Product_url']
    df_final=df_final[col_name]
    df_final=df_final.rename({'Median_Rating':'Median_Customer_Rating'}) 
    
    return df_final


app = Flask(__name__)

@app.route('/')
def home():
    return render_template('view.html')


@app.route('/search',methods=['POST'])
def search():
    s=requests.Session()
    sterm = [str(x) for x in request.form.values()]
    sterm=sterm[0]
    print(sterm)
    productlist=get_productdetails(sterm)
    if productlist.empty:
        return render_template('error404.html')
    reviews=get_productreviews(productlist)
    finallist=get_finallist(reviews,productlist)
    df=finallist.copy()
    
    return render_template('view.html',message='Search results for '+sterm ,tables=[df.to_html(classes='data',header='True',index=False)])
  
        
       



if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8001, debug=True)
