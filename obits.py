from bs4 import BeautifulSoup
from selenium import webdriver
import streamlit as st
import pandas as pd
import re
from selenium.webdriver import FirefoxOptions

st.set_page_config(layout="wide")

def first_and_last(text):
    return text.split(' ')[0] +' '+ text.split(' ')[-1]
def search(search_term,text):
    split_text = text.split()
    split_search_term = search_term.split()
    return all([any([y.find(x)>-1 for y in split_text]) for x in split_search_term])
    
def get_obits(text):
    url = 'https://www.readingeagle.com/?s='+text+'&post_type=obituary&orderby=relevance'
    options = ChromeOptions()
    options.add_argument("--headless=new")
    driver = webdriver.Chrome(options=options)
    
    driver.get(url)
    file = driver.page_source
    driver.quit()
    soup = BeautifulSoup(file, 'lxml')
    
    results = [x.find_previous() for x in soup.find_all(class_='obit-search-result-person-name')]
    names = [x.get_text(strip = True) for x in results]
    links = [x['href'] for x in results]
    matches = [y for x,y in zip(names,links) if search(text,x)]
    return matches

def get_list_of_obits(body):
    name_suggestions = []
    dictionary = {}
    i = 0
    my_bar = st.progress(0, text='Searching...')
    for text in body:
        percent = i/len(body)
        my_bar.progress(percent, text='Searching entry ' + str(i+1) + ' of ' + str(len(body)))
        i+=1
        obits = get_obits(text)
        if len(obits) == 0:
            continue
        name_suggestions.append(text)
        dictionary[text] = obits
    my_bar.empty()
    return name_suggestions,dictionary

# def search_change():
#     st.session_state.have_searched = True

def clean_text(input):
    text = [str(input.iloc[i][0]) + ' ' +str(input.iloc[i][1]) for i in range(len(input))]
    for i in range(len(text)):
        if text[i].find('&')>-1:
            ampersand_text = text[i].split()
            if ampersand_text[-2] == 'Van':
                last_name = ampersand_text[-2] + ' ' + ampersand_text[-1]
                ampersand_text.remove(ampersand_text[-2])
                ampersand_text.remove(ampersand_text[-1])
            else:
                last_name = ampersand_text[-1]
                ampersand_text.remove(last_name)
            both_names = ' '.join(ampersand_text)
            without_ampersand = re.split(' & ',both_names)
            try:
                name_1 = without_ampersand[0] + ' ' + last_name
                name_2 = without_ampersand[1] + ' ' + last_name
                text.remove(text[i])
                text.append(name_1)
                text.append(name_2)
            except:
                text[i] = ' '.join(text[i].replace('&','').split())
    return text

def main():
    # if 'have_searched' not in st.session_state:
    #     st.session_state.have_searched = False
    if 'names' not in st.session_state:
        st.session_state.names = []
    with st.form('search_form'):
        uploaded_file = st.file_uploader("Load an Excel File")
        num_searches = st.text_input('Number of People to Search')
        if uploaded_file:
            excel = pd.read_excel(uploaded_file,header=None)
            if num_searches:
                cleaned_data = clean_text(excel)[:int(num_searches)]
            else:
                cleaned_data = clean_text(excel)
        submit_button = st.form_submit_button("Search")#,on_change = search_change)
        
    if uploaded_file and submit_button: #and st.session_state.have_searched:
        search = cleaned_data
        st.session_state.names,st.session_state.links = get_list_of_obits(search)
        # st.session_state.have_searched = False
    if len(st.session_state.names)>0:
        st.write(f'{len(st.session_state.names)} people have appeared in the search:')
        for x in st.session_state.names:
            print(st.write(x))
        box = st.selectbox('Select Person to Get Additional Info:',st.session_state.names)
        if box:
            for entries in st.session_state.links[box]:
                st.write(entries)
        search_results = pd.DataFrame(dict([(key, pd.Series(value)) for key, value in st.session_state.links.items()])).T
        download_button = st.download_button(
            label="Download Names",
            data=search_results.to_csv(),
            file_name= "results.csv",
            mime="text/csv",
        )

if __name__ == "__main__":
    main()
