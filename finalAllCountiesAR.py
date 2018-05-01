# Codes targeting AR, Final

from pathlib import Path
from zipfile import ZipFile
import pandas as pd
import clarify
import requests 
from io import BytesIO as ioDuder 
from lxml import etree 
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC



def website_returns(website_link):
    """
    A master function that takes in a website link and outputs a csv
    """
    
    driver = webdriver.Chrome()
    driver.get(website_link)
    all_counties_element = driver.find_element_by_id("areasreportinglinktxt") # Specific to AR
    all_counties_element.click() # click on the All Counties reporting site for AR
    
    # Implicit wait condition until counties show up
    element = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.ID, "td_legend_name")))
    
    
    # Dict of all counties
    all_counties = {county_name.text: county_name for county_name in driver.find_elements_by_xpath
                    ("//td[@id='td_legend_name']/a[@href='#']")} # Specific to AR
                    
    ########## take 3 counties from all_counties to test ############
    county_name_list = [key for key in all_counties.keys()]
    test_counties = county_name_list[:2]
    # print(test_counties)
    test_counties = {county_name: all_counties[county_name] for county_name in test_counties}
    #################################################################                
           
    df = pd.DataFrame()
    
    # Iterate through dict of all counties
    
    # for county in all_counties: # uncomment this to iterate through all counties
    for county in test_counties: # only testing 3 counties
                
        # driver.execute_script("arguments[0].scrollIntoView();", all_counties[county])
        # all_counties[county].click()
        
        ############### Using 3 sample counties ####################
        driver.execute_script("arguments[0].scrollIntoView();", test_counties[county])
        test_counties[county].click()
        ############################################################
        
        window_all_counties = driver.window_handles[0]
        window_county = driver.window_handles[1]
        driver.switch_to_window(window_county)
        
        link_to_xml(website_link)
        parsed_xml = write_to_xml(driver)
        returns_dict = xml_to_dict(parsed_xml)
        
        county_returns_df = returns_dict_to_df(returns_dict, county)
        
        df = pd.concat([df, county_returns_df])
        
        # print(df)
        
        # switch back to window with all counties to continue clicking
        driver.switch_to_window(window_all_counties)
    
    # name vote_count column
    df.rename(columns={list(df)[0]:'vote_count'}, inplace=True)
    
    df.to_csv('~/test_output.csv')
    
    # driver.quit()
        


def link_to_xml(link):
    """a function that takes a link and returns an xml file"""
    
    s = clarify.Jurisdiction(url=link, level='county')
    r = requests.get(s.report_url('xml'), stream=True)
    z = ZipFile(ioDuder(r.content))

    return z.open('detail.xml') # return an accessed detail.xml file



def write_to_xml(driver):
    """
    a functions that takes in source codes (Selenium driver), writes to returns.xml
    and returns parsed xml codes
    """
    returns = link_to_xml(link = driver.current_url).read()
    root = etree.XML(returns)
    xml_path = Path()/'returns.xml' # also works for earlier Python versions

    # write to returns.xml
    xml_path.write_text(etree.tostring(root).decode('utf-8'))
    
    return root



def xml_to_dict(parsed_xml):
    """
    a function that takes in parsed xml codes and outputs dict for the returns,
    key value is Contest/Office
    """
    returns = {}
    
    for contest in parsed_xml.xpath('Contest'):
        contest_name = contest.get('text')
        # print(contest_name)
        # Create keys named for contests, e.g.  "HOLLY SPRINGS CITY COUNCIL W5"
        returns[contest_name] = {}
    
        for choice in contest.xpath('Choice'):
            # Choices represent candidates
            candidate = choice.get('text')
            returns[contest_name][candidate] = {}
            
            for vote_type in choice.xpath('VoteType'):
                # Vote types are Election-Day, Absentee by mail, etc.
                vote_type_name = vote_type.get('name')
                returns[contest_name][candidate][vote_type_name] = {'precincts': {}}
                
                for precinct in vote_type.xpath('Precinct'):
                    precinct_name = precinct.get('name')
                    returns[contest_name][candidate][vote_type_name]['precincts'][precinct_name] = precinct.get('votes')
    return returns



def returns_dict_to_df(returns_dict, county):
    """
    a function that takes in a dict of returns for a particular county
    and returns a dataframe
    """
    
    df = pd.DataFrame()
    
    for office in returns_dict:
        offices = returns_dict[office]
        for candidate in offices:
            candidates = offices[candidate]
            for vote_type in candidates:
                vote_types = candidates[vote_type]
                for precinct in vote_types:
                    tmp=pd.DataFrame()
                    tmp=tmp.from_dict(vote_types[precinct], orient='index')
                    tmp['office']=office
                    tmp['vote_type']=vote_type
                    tmp['candidate']=candidate
                    tmp['county']=county 
                    df = df.append(tmp)
                    #print(tmp)
    return df

    
if __name__ == '__main__':
    """ Test cases"""
    # For AR
    website_returns('http://results.enr.clarityelections.com/AR/63912/184685/Web01/en/summary.html#')


