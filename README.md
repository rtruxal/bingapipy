bingapipy
=========

##It's pronounced binga-pip-ee.
####Say it a bunch of times. It's fun!




This is a single-file interface to the new **v5** version of the Bing web-search API, hosted by Azure Cognitive Services.

As a prequisite to using this interface, you need an API key which can be obtained from https://portal.azure.com.

**IMPORTANT NOTE: This is not an interface for the v2/Datamarket API**


Usage
=====

```py
>>> from bingapipy import BingSearcher
>>>
>>> key = 'RAAAAAANDOMLETTERSANDNUMBERRRSS23486832'
>>> query = '"Look! double quotes!"'
>>> 
>>> BingSearcherInstance = BingSearcher(key, query)

The search-interface has been initialized w/ the following params:
 
'Endpoint-Type: web'
 
'Query-URL:https://api.cognitive.microsoft.com/bing/v5.0/search?q=%22Look%21+double+quotes%21%22&count=50&mkt=en-us&offset=0'
 
'Header-Dict: OrderedDict([('Ocp-Apim-Subscription-Key', 'RAAAAAANDOMLETTERSANDNUMBERRRSS23486832'), ('User-Agent', 'Mozilla/5.0 (Windows NT 6.2; Win64; x64; rv:16.0.1) Gecko/20121011 Firefox/16.0.1'), ('X-Search-ClientIP', '8.8.8.8')])'
```
 
 
 * Then, you search using one of the 4 exposed search methods with usage shown here:
    * `packaged_json_object = BingSearcherInstance.search_2_packaged_json()`
    * `raw_json_dict = BingSearcherInstance.search_2_json()`
    * `raw_html_str = BingSearcherInstance.search_2_html()`
    * `requests_module_response_obj = BingSearcherInstance.search_2_response_obj()`


 * And then we rinse and repeat!
 ```py
>>> BingSearcherInstance.reset_query_string_and_paging('IP:"8.8.8.8"')
>>> new_packaged_json_object = BingSearcherInstance.search_2_packaged_json()
>>>
>>> BingSearcherInstance.reset_query_string_and_paging('Yet another plaintext query')
>>> new_NEW_packaged_json_object = BingSearcherInstance.search_2_packaged_json()
```
 
paging support coming soon.
