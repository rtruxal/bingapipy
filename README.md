bingapipy
=========

##It's pronounced binga-pip-ee.
###Say it a bunch of times. It's fun!
####Efficiency has been totaly usurped by readabilityism and consolidation. This gives me carte blanche to make the thing as clumsy as i thankyou.




This is a single-file interface to the new **v5** version of the Bing web-search API, hosted by Azure Cognitive Services.

As a prequisite to using this interface, you need an API key which can be obtained from https://portal.azure.com.

**IMPORTANT NOTES:**
   - This is not an interface for the v2/Datamarket API
   - As of now, only web, news, & categorical-news searches are supported for packaging.


Usage
=====

##So you wanna search the web eh?

Like all techincal books you hate, let's start with some theory before we apply it.

##Some quick points:
 1. **BingSearch** is your engine, and the primary structure through which you'll be interfacing with this module.
 2. **BingSearch** has state which must be initialized. This state is primarily concerned with 3 groups of parameters:
    - Your query string (q={ } <== this thing.)
    - Your Headers in the form of an ordered key-value dictionary
    - your supplimental URL params in the form of an ordered key-value dictionary.
 3. You can call `BingSearch`'s **page** or **reset** methods, which should be understood as 2 fundamentally different actions:
    - `BingSearch.page()` will *use your current state-configuration* & make repeated calls, while incrementing the `offset` param.
    - `BingSearch.reset()` will allow you to *change your current state-configuration,* in preparation for an entirely new query.

####Initializing BingSearch with desired state:
 * Take a second to pop open the core module: bingapipy
    * At the top you'll find:
```python
class default_user_params():
    from collections import OrderedDict
    DEFAULT_HEADER_PARAMS = OrderedDict()
    DEFAULT_URL_PARAMS = OrderedDict()

    ###############################################
    ## Enter default-header customizations here. ##
    ###############################################
    ##HEADER_PARAMS['Ocp-Apim-Subscription-Key'] = None # <--SHOULD NOT BE SET HERE. FOR DISPLAY PURPOSES ONLY.
    DEFAULT_HEADER_PARAMS['User-Agent'] = 'Mozilla/5.0 (Windows NT 6.2; Win64; x64; rv:16.0.1) Gecko/20121011 Firefox/16.0.1' 
    DEFAULT_HEADER_PARAMS['X-Search-ClientIP'] = '8.8.8.8'
    DEFAULT_HEADER_PARAMS['X-MSEdge-ClientID'] = None
    DEFAULT_HEADER_PARAMS['Accept'] = None
    DEFAULT_HEADER_PARAMS['Accept-Language'] = None
    DEFAULT_HEADER_PARAMS['X-Search-Location'] = None

    ###############################################
    ##     Enter query customizations here.      ##
    ###############################################
    ##CustomURL['q'] = None              # <--SHOULD NOT BE SET HERE. FOR DISPLAY PURPOSES ONLY.
    DEFAULT_URL_PARAMS['cc'] = None               
    DEFAULT_URL_PARAMS['count'] = "50"            
    DEFAULT_URL_PARAMS['freshness'] = None        
    DEFAULT_URL_PARAMS['mkt'] = 'en-us'           
    DEFAULT_URL_PARAMS['offset'] = '0'            
    DEFAULT_URL_PARAMS['responseFilter'] = None   
    DEFAULT_URL_PARAMS['safeSearch'] = None       
    DEFAULT_URL_PARAMS['setLang'] = None          
    DEFAULT_URL_PARAMS['textDecorations'] = None  
    DEFAULT_URL_PARAMS['textFormat'] = None       
    # News Search Only!
    DEFAULT_URL_PARAMS['category'] = None         # <--(ONLY FOR NEWS SEARCH. See available categories by mkt)
```
These are the templates used to initialize your search query with **headers** & **supplimental URL params**, aka 2/3 of the state that a BingSearch instance will act upon.

Be sure to leave the params which you *don't* want to use set as `None`.

####You will need to pass your API key & query-string to the constructor when you create it. Let's try that:
```python
>>> from bingapipy import BingSearch
>>>
>>> key = 'RAAAAAANDOMLETTERSANDNUMBERRRSS23486832'
>>> query = '"Look! double quotes!"'
>>> 
>>> BingSearchInstance = BingSearch(key, query)
```
Unless you set `BingSearch(...,verbose=False)` manually, the following will be displayed:
```
The search-interface has been initialized w/ the following params:
'Endpoint-Type: web'
 
'Query-URL:https://api.cognitive.microsoft.com/bing/v5.0/search?q=%22Look%21+double+quotes%21%22&count=50&mkt=en-us&offset=0'
 
'Header-Dict: OrderedDict([('Ocp-Apim-Subscription-Key', 'RAAAAAANDOMLETTERSANDNUMBERRRSS23486832'), ('User-Agent', 'Mozilla/5.0 (Windows NT 6.2; Win64; x64; rv:16.0.1) Gecko/20121011 Firefox/16.0.1'), ('X-Search-ClientIP', '8.8.8.8')])'
```
Look familiar?
 
##Paging the query away....
I love a bad joke.  
 
Now that you've successfully initialized your BingSearch instance, you'll need to decide whether you just want the first 50 results for your query, or if you want 5000. If you just want to call the API 1 time, check out the bottom section entitled "Inspecting Your Response"  

For now, we're going to look at the `BingSearch.page()` method. Lets look at the args:
```python
def page(self, count_or_range=None, return_type_function='links_plaintext', break_on_nth_page=100):
    ...
```
####Let's break down what these do:
  - `count_or_range` ==> pass either a positive integer 2 integers inside of an iterable specifying start & stop points
    - EX:
        - `count_or_range=1000` **OK** (will attempt to make 20 queries starting at record 1.)
        - `count_or_range=-59` **NOT OK** (will yell at you)
        - `count_or_range=[100, 200]` **OK** (will attempt to make 2 full queries, starting at record 100)
        - `count_or_range=[76, 84]` **OK** (will attempt to make 1 partial query & return 8 records)
        - `count_or_range=[5, 10, 39]` **NOT OK** (will yell at you. Too many numbers.)
        - `count_or_range=[200, 100]` **KIND OF OK** (this will be changed to `count_or_range=[100, 200]`)
        
  - `return_type_function` ==> What do you want a list of? below are your options:
 ```python
function_types = (
            'links_plaintext',
            'links_encoded',
            'json_packaged',
            'json_raw',
            'full_response',
        )
 ```
 - `break_on_nth_page` ==> let's say you accidentally add an extra 0 somewhere and you've requested 10X too many results. This should help with that.
 
 
####More comming soon.....

##Inspecting Your Response:
Now, you could just use `BingSearchInstance.page(count_or_range=50)` to get the first 50 results. However, maybe you want more granular control, or to look at the response your're getting itself.  

For this reason, the single-call methods, which the paging method acts upon, have been exposed and can be seen here: 
   * `requests_module_response_obj = BingSearchInstance.search_2_response_obj()`
   * `raw_json_dict = BingSearchInstance.search_2_json()`
   * `packaged_json_object = BingSearchInstance.search_2_packaged_json()`
   
These will spit back one request response, corresponding to the various stages of the parsing procedure:
   1. the requests.Response object is returned ==> `.search_2_response_obj()`
   2. Errors in the requests.Response.status_code are handled, and then the JSON is extracted from it. ==> `.search_2_json()`
   3. The JSON is packaged in a bespoke class called xResult, where x is 'Web' or 'News' etc... depending on your endpoint. ==> `.search_2_packaged_json()`
   