import requests
from requests.models import urlencode
from socket import gethostbyname, gethostname
from collections import OrderedDict
from time import sleep


###############################################
##                                           ##
##       User-defined dictionaries for       ##
##          header and query params          ##
##                                           ##
###############################################
class local_user_constants():
    HEADERS = OrderedDict()
    INCLUDED_PARAMS = OrderedDict()

    ###############################################
    ## Enter default-header customizations here. ##
    ###############################################
    HEADERS['User-Agent'] = "Mozilla/5.0 (Windows NT 6.2; Win64; x64; rv:16.0.1) Gecko/20121011 Firefox/16.0.1"
    HEADERS['X-Search-ClientIP'] = gethostbyname(gethostname())
    HEADERS['X-MSEdge-ClientID'] = None
    HEADERS['Accept'] = None
    HEADERS['Accept-Language'] = None
    HEADERS['X-Search-Location'] = None

    ###############################################
    ##     Enter query customizations here.      ##
    ###############################################
    ## Web Params: ['query_plaintext'] = None HAS BEEN LEFT OUT ON PURPOSE. THAT DON'T GO HERE.
    INCLUDED_PARAMS['cc'] = None               # <--(See constants._COUNTRY_CODES below for available options)
    INCLUDED_PARAMS['count'] = "50"            # <--(Enter a number from 0-50. Must by type==str. EX: count of 5 should be "5")
    INCLUDED_PARAMS['freshness'] = None        # <--(Poss values are 'Day', 'Week', or 'Month')
    INCLUDED_PARAMS['mkt'] = 'en-us'           # <--(See constants._MARKET_CODES below for available options)
    INCLUDED_PARAMS['offset'] = '0'            # <--(Use this in conjunction with totalEstimatedMatches and count to page. Same format as 'count')
    INCLUDED_PARAMS['responseFilter'] = None   # <--(Poss values are 'Computation', 'Images', 'News', 'RelatedSearches', SpellSuggestions', 'TimeZone', 'Videos', or 'Webpages')
    INCLUDED_PARAMS['safeSearch'] = None       # <--(Poss values are 'Off', 'Moderate', and 'Strict.')
    INCLUDED_PARAMS['setLang'] = None          # <--(See ISO 639-1, 2-letter language codes here: https://www.loc.gov/standards/iso639-2/php/code_list.php)
    INCLUDED_PARAMS['textDecorations'] = None  # <--(Case-insensitive boolean. '(t|T)rue', or '(f|F)alse')
    INCLUDED_PARAMS['textFormat'] = None       # <--(Poss values are 'Raw', and 'HTML.' Default is 'Raw' if left blank.)


###############################################
##                                           ##
##      Primary API for SearchWebLite        ##
##                                           ##
###############################################
class BingSearcher(object):

    ###############################################
    ## Initialization functions and attr-setting ##
    ###############################################
    def __init__(self, api_key=None, query=None, endpoint='web', verbose=True, params=local_user_constants.INCLUDED_PARAMS.copy() , headers=local_user_constants.HEADERS.copy()):
        self._key = api_key
        self.query_plaintext = query
        self.params = params
        self.headers = headers
        self.current_offset = 0
        self.endpoint_type = endpoint
        self.queries_run = 0
        self.total_estimated_matches = 0
        self._verbose = verbose
        self.last_predicted_url = None
        self.last_actual_url = None
        self._init_constructor_funcs()
        self._url_comparisons = []


    def _init_constructor_funcs(self):
        self.base_url = local_static_constants.API_ENDPOINTS[self.endpoint_type]
        # encode your query to be URL-rdy
        self._encoded_q = urlencode(dict(q=self.query_plaintext))
        # clean out them' dictionary attrs.
        self.headers = _clear_null_vals(self.headers)
        self.params = _clear_null_vals(self.params)
        # inject key into header
        self.headers = self._inject_key_into_header(self.headers)
        self.last_predicted_url = self._predict_url(bypass_setting_attrs=True)
        if self._verbose:
            print 'The search-interface has been initialized w/ the following params:\n\nEndpoint-Type: {}\n\nQuery-URL: {}\n\nHeader-Dict: {}'.format(self.endpoint_type, self.last_predicted_url, self.headers)

    ###############################################
    ##   _methods used BEFORE request is sent    ##
    ###############################################
    def _predict_url(self, bypass_setting_attrs=False):
        """Can be used before or after dictionaries have been cleaned of NoneTypes"""
        prediction = self.base_url + self._encoded_q + '&' + urlencode(self.params)
        if not bypass_setting_attrs:
            self.last_predicted_url = prediction
        return prediction

    def _inject_key_into_header(self, header_dictionary, override=False):
        OD_w_key_added = OrderedDict()
        if 'Ocp-Apim-Subscription-Key' in header_dictionary.keys():
            if override:
                print 'API key in supplied dictionary will be replaced.'
                del header_dictionary['Ocp-Apim-Subscription-Key']
            else:
                raise IndexError('API key detected in dictionary arg. Please set override=True to replace it')
        OD_w_key_added['Ocp-Apim-Subscription-Key'] = self._key
        for key, value in header_dictionary.items():
            OD_w_key_added[key] = value
        return OD_w_key_added

    ###############################################
    ##    callable methods which make requests   ##
    ###############################################

    def search_2_response_obj(self):
        try:
            ##############################
            #           BEHOLD!          #
            response_object = requests.get(self.base_url + self._encoded_q, params=self.params, headers=self.headers)
            ##############################
            self.last_actual_url = response_object.url
            if self._verbose:
                self._url_comparisons.append((self._predict_url(), self.last_actual_url))
            self.queries_run += 1
            return response_object
        except requests.Timeout:
            print('request timed out. Aborting search.')
            raise Warning('Request timed out')

    def search_2_json(self, return_html=False):
        response_object = self.search_2_response_obj()
        # Handle error-codes and Warn about potential garbage results if query URL is too long.
        if len(response_object.url) > 1300:
            print('WARNING: URL too long at {} characters.\n Bing can silently truncate your query.\n Limit URLs to < 1,200 chars.').format(len(response_object.url))
        # import pdb
        # pdb.set_trace()
        response_validated = validate_request_response(response_object)
        if response_validated == '429':
            response_object = self._handle_429_error(url=response_object.url)
        else:
            pass
        if return_html:
            return response_object.text()
        return response_object.json()

    def search_2_packaged_json(self):
        """returns list of WebResult objects w/ len(list) == # of links returned"""
        raw_json = self.search_2_json()
        return self._parse_json(raw_json)

    def search_2_html(self):
        if 'textFormat' in self.params.keys() and self.params['textFormat'].upper() == 'HTML':
            return self.search_2_json(return_html=True)
        else:
            raise AssertionError('Attempting html retreival without specifying html under "textFormat" param')




    ###############################################
    ##     change the query and reset paging     ##
    ###############################################
    def reset_query_string_and_paging(self, unencoded_query_str):
        self.query_plaintext = unencoded_query_str
        self._encoded_q = urlencode(dict(q=self.query_plaintext))
        self.current_offset = 0
        self.total_estimated_matches = 0

    ###############################################
    ##   _methods used AFTER request is sent     ##
    ###############################################
    def _parse_json(self, json_response):
        """
        Takes raw JSON response and packages them as instances of class WebResult.
        :param json_response: EX -- <requests_response_object>.json()
        :return list of WebResult objects: parsed and prettied JSON results with easy data-access.
                Returned as a LIST of WebResult objects with len == the # of links returned by Bing.
        """
        if not self.total_estimated_matches and self.endpoint_type == 'web':
            print(('Bing says there are an estimated {} results matching your query'.format(json_response['webPages']['totalEstimatedMatches'])))
            self.total_estimated_matches = int(json_response['webPages']['totalEstimatedMatches'])
        packaged_json = [WebResult(single_json_entry) for single_json_entry in json_response['webPages']['value']]
        return packaged_json

    def _handle_429_error(self, url):
        timeout_cnt = 0
        while True:
            if timeout_cnt < 5:
                sleep(2)
                r2 = requests.get(url, self.headers)
                if validate_request_response(r2) == '429':
                    timeout_cnt += 1
                    pass
                elif r2.status_code == 200:
                    break
                else:
                    raise AssertionError('response not successful')
            else:
                raise IOError(local_static_constants._ERROR_CODES['429'])
        return r2



###############################################
##                                           ##
##       Packaging for JSON responses        ##
##                                           ##
###############################################
class WebResult(object):
    '''
    Attributes which can be called from WebResult instance(aka WebResults instance aka WRi) --

    WRi.json: full JSON entry.
    WRi.url: The URL sent back by Bing.
    WRi.display_url: Display URL. Not always accurate.
    WRi.name: The title of the page linked to by WRi.url.
    WRi.snippet: A snippet of text from the page linked to by WRi.url.
    WRi.id: the index value for this JSON entry. Used primarily for compound queries.
    '''

    def __init__(self, result):
        self.json = result
        self.url = result.get('url')
        self.display_url = result.get('displayUrl')
        self.name = result.get('name')
        self.snippet = result.get('snippet')
        self.id = result.get('id')
        try:
            self.date_crawled = result.get('dateLastCrawled')
            self.about = result.get('about')
        except Exception:
            self.date_crawled = None
            self.about = None
        # maintain compatibility
        self.title = result.get('name')
        self.description = result.get('snippet')

    def __str__(self):
        return 'WebResponse Obj: {}'.format(self.display_url)

    def __repr__(self):
        return '{}'.format(self.display_url)

###############################################
##                                           ##
##          class-independent funcs          ##
##                                           ##
###############################################
def _clear_null_vals(dictionary):
    """iterates over a dict forward-ways. Deletes NoneType entries."""
    return OrderedDict((k, v) for k, v in dictionary.items() if v)




def validate_request_response(response):
    """
    Return nothing if valid response object returned.
    Otherwise handle or throw exceptions
    :param response: requests.response object.
    :return: func will pass or raise exception. That's all.
    """
    if not response.status_code == 200:
        if response.status_code == 429:
            print('queries/second quota exceeded. this func will make 5 attempts to resend.')
            return '429'
        elif response.status_code == 400:
            json = response.json()
            print '400 error: Bad params\n\nBing is showing {} param(s) set to {}'.format(json['errors'][0]['parameter'], json['errors'][0]['value'])
            raise ValueError()
        elif str(response.status_code) in list(local_static_constants._ERROR_CODES.keys()):
            raise AssertionError(local_static_constants._ERROR_CODES[str(response.status_code)])
        else:
            raise ReferenceError('unknown status code returned: {}\nurl string is: {}'.format(response.status_code, response.url))
    else: return True


###############################################
##                                           ##
##       Constants specified by Bing         ##
##                                           ##
###############################################
class local_static_constants():
    API_ENDPOINTS = {
        'web': 'https://api.cognitive.microsoft.com/bing/v5.0/search?',
        'images': 'https://api.cognitive.microsoft.com/bing/v5.0/images/search?',
        'images_trending': 'https://api.cognitive.microsoft.com/bing/v5.0/images/trending/search?', # <-- works only for mkt= en-US, en-CA, and en-AU
        'videos': 'https://api.cognitive.microsoft.com/bing/v5.0/videos/search?',
        'videos_trending': 'https://api.cognitive.microsoft.com/bing/v5.0/videos/trending/search?',
        'videos_details': 'https://api.cognitive.microsoft.com/bing/v5.0/videos/details/search?',
        'news': 'https://api.cognitive.microsoft.com/bing/v5.0/news/search?',
        'news_trending': 'https://api.cognitive.microsoft.com/bing/v5.0/news/trendingtopics&'
    }
    _ERROR_CODES = {
        '200': 'The call succeeded',
        '400': 'One of the query parameters is missing or not valid',
        '401': 'The subscription _key is missing or not valid',
        '403': "The user is authenticated but doesn't have permission to the requested resource. Bing may also return this status if the caller exceeded their queries per month quota",
        '404': 'Page not found: Bing should not be throwing this error. There is likely a fundamental problem with the structure of your query URL.',
        '410': 'The request was made using HTTP. Only HTTPS is supported.(_BASE_ENDPOINT USES HTTPS. EITHER YOU CHANGED THAT OR YOU ARE NOT AT FAULT)',
        '429': 'The user exceeded their queries per second quota',
    }