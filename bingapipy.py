from collections import OrderedDict, Iterable
from socket import gethostbyname, gethostname
from time import sleep
import requests
from requests.models import urlencode

from .errors_and_validations import JsonParsingError, QueryChecker


###############################################
##                                           ##
##       User-defined dictionaries for       ##
##          header and query params          ##
##                                           ##
###############################################
class default_user_params():
    DEFAULT_HEADER_PARAMS = OrderedDict()
    DEFAULT_URL_PARAMS = OrderedDict()

    ###############################################
    ## Enter default-header customizations here. ##
    ###############################################
    ##HEADER_PARAMS['Ocp-Apim-Subscription-Key'] = None                                                               # <--('Ocp-Apim-Subscription-Key' SHOULD NOT BE SET HERE. YOU MUST PASS IT TO THE SEARCH-OBJECT-CONSTRUCTOR CLASS: BingSearch)
    DEFAULT_HEADER_PARAMS['User-Agent'] = "Mozilla/5.0 (Windows NT 6.2; Win64; x64; rv:16.0.1) Gecko/20121011 Firefox/16.0.1" # <--(dummy User-Agent header for consistent response-format)
    DEFAULT_HEADER_PARAMS['X-Search-ClientIP'] = gethostbyname(gethostname())                                                 # <--(these are methods from the 'socket' module which produce the host-machine's public IP)
    DEFAULT_HEADER_PARAMS['X-MSEdge-ClientID'] = None
    DEFAULT_HEADER_PARAMS['Accept'] = None
    DEFAULT_HEADER_PARAMS['Accept-Language'] = None
    DEFAULT_HEADER_PARAMS['X-Search-Location'] = None

    ###############################################
    ##     Enter query customizations here.      ##
    ###############################################
    ##CustomURL['q'] = None              # <--(BOTH THE 'Ocp-Apim-Subscription-Key' FROM 'HEADER_PARAMS' AND THE 'q' FROM 'CustomURL' MUST BE PASSED MANUALLY TO THE SEARCH-OBJECT-CONSTRUCTOR CLASS: BingSearch)
    DEFAULT_URL_PARAMS['cc'] = None               # <--(See constants._COUNTRY_CODES below for available options)
    DEFAULT_URL_PARAMS['count'] = "50"            # <--(Enter a number from 0-50. Must by type==str. EX: count of 5 should be "5")
    DEFAULT_URL_PARAMS['freshness'] = None        # <--(Poss values are 'Day', 'Week', or 'Month')
    DEFAULT_URL_PARAMS['mkt'] = 'en-us'           # <--(See constants._MARKET_CODES below for available options)
    DEFAULT_URL_PARAMS['offset'] = '0'            # <--(Use this in conjunction with totalEstimatedMatches and count to page. Same format as 'count')
    DEFAULT_URL_PARAMS['responseFilter'] = None   # <--(Poss values are 'Computation', 'Images', 'News', 'RelatedSearches', SpellSuggestions', 'TimeZone', 'Videos', or 'Webpages')
    DEFAULT_URL_PARAMS['safeSearch'] = None       # <--(Poss values are 'Off', 'Moderate', and 'Strict.')
    DEFAULT_URL_PARAMS['setLang'] = None          # <--(See ISO 639-1, 2-letter language codes here: https://www.loc.gov/standards/iso639-2/php/code_list.php)
    DEFAULT_URL_PARAMS['textDecorations'] = None  # <--(Case-insensitive boolean. '(t|T)rue', or '(f|F)alse')
    DEFAULT_URL_PARAMS['textFormat'] = None       # <--(Poss values are 'Raw', and 'HTML.' Default is 'Raw' if left blank.)
    # News Search Only!
    DEFAULT_URL_PARAMS['category'] = None         # <--(ONLY FOR NEWS SEARCH. See available categories by mkt)

###############################################
##                                           ##
##      Primary API for SearchWebLite        ##
##                                           ##
###############################################
class BingSearch(object):
    """
     Don't be intimidated because I write spaghetti code.
     Read the docstrings. They're attached to the most important methods.
     """

    ###############################################
    ## Initialization functions and attr-setting ##
    ###############################################
    def __init__(self, api_key=None, query=None, endpoint='web', verbose=True, validate_params=False,
                 params=default_user_params.DEFAULT_URL_PARAMS.copy(),
                 headers=default_user_params.DEFAULT_HEADER_PARAMS.copy()):

        assert isinstance(api_key, str) and len(api_key) == 32
        self._key = api_key
        assert isinstance(query, str)
        self.query_plaintext = query
        assert isinstance(params, dict) and isinstance(headers, dict)
        self.params = params
        self.headers = headers
        assert endpoint in static_constants.API_ENDPOINTS.keys()
        self.endpoint_type = endpoint
        self._verbose = verbose
        # making sure these exisssst....
        self.queries_run = 0
        self.total_estimated_matches = 0
        self._url_comparisons = []
        self.urls_predicted = ''
        # Ok now do stuff:
        self._init_constructor_funcs(validate_params=validate_params)


    def _init_constructor_funcs(self, rewrite=False, skip_cleaning_headers_and_params=False, validate_params=False):
        self.base_url = static_constants.API_ENDPOINTS[self.endpoint_type]
        # encode your query to be URL-rdy
        if 'categories' not in self.endpoint_type:
            self._encoded_q = urlencode(dict(q=self.query_plaintext))
        else:
            self._encoded_q = self._handle_categorical_query()
        # clean out them' dictionary attrs.
        if skip_cleaning_headers_and_params == True: pass
        else:
            self.headers = _clear_null_vals(self.headers)
            self.params = _clear_null_vals(self.params)
        # (>_<) no. Bad monkey.
        # TODO: Make paging-support less hacky.
        if rewrite == True:
            # THIS PORTION OF THIS FUNCTION SHOULD ONLY GET CALLED FROM self._reset()
            # PLZ DON'T USE IT 4 ANYTHING ELSE.
            if self._key != self.headers['Ocp-Apim-Subscription-Key']:
                self.headers = self._inject_key_into_header(self.headers, override=True)
            elif self._verbose:
                print 'INFO: API key equals previous. Header-injection skipped'
                pass
            else: pass
            self.urls_predicted += '\n' + self._predict_url()
        else:
            self.headers = self._inject_key_into_header(self.headers)
            self.urls_predicted += '\n' + self._predict_url(bypass_setting_attrs=True)
        if validate_params:
            QueryChecker.check_web_params(self.params, self.headers)
        if self._verbose:
            print 'The search-interface has been initialized w/ the following params:\n\nEndpoint-Type: {}\n\nQuery-URL: {}\n\nHeader-Dict: {}'.format(self.endpoint_type, self.urls_predicted, self.headers)

    ###############################################
    ##   _methods used BEFORE request is sent    ##
    ###############################################

    def _predict_url(self, bypass_setting_attrs=False):
        """Can be used before or after dictionaries have been cleaned of NoneTypes"""
        prediction = self.base_url + self._encoded_q + '&' + urlencode(self.params)
        if not bypass_setting_attrs:
            self.urls_predicted = prediction
        return prediction

    def _handle_categorical_query(self):
        """Essentially just a validation method. categorical search must be used in conjunction w/ the mkt param"""
        # Must specify mkt param to do categorical searches. Only two working are for GB and US.
        assert self.params['mkt'] != None and self.params['mkt'][-2:].lower() in ('us', 'gb')
        if self.params['mkt'][-2:].lower() == 'us' and self.query_plaintext in static_constants.NEWS_CATEGORIES_US:
            pass
        elif self.params['mkt'][-2:].lower() == 'gb' and self.query_plaintext in static_constants.NEWS_CATEGORIES_GB:
            pass
        else:
            raise ValueError('mkt param and categorical query term do not match')
        return 'category={}'.format(self.query_plaintext)


    def _inject_key_into_header(self, header_dictionary, override=False, verbose=False):
        OD_w_key_added = OrderedDict()
        if 'Ocp-Apim-Subscription-Key' in header_dictionary.keys():
            if override:
                if verbose is True:
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
    # Starting with search_2_response_object, these rest on top of eachother
    # Notice that each search_2_... method starts by calling the previous.
    # requests is a magical black-box that handles all the actual HTTP(S).

    def search_2_response_obj(self):
        """
        Use requests to call the query.
        As of now, this interface only sends individual GET requests & does not set keep-alive or use cookies.
        :return: requests.Response()
        """
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
        """
        Each subsequent function in the BingSearch.search_2_....() family acts on the output from the one above it.

        This one examines the request.Response for error-codes & if everything is ok,
        returns the requests.Response.json from the requests.Response object passed in by search_2_response_obj()

        :param return_html [BOOL] : set to true to get html returned instead of JSON.
                WebResult won't be able to package html, so don't try it.
        :return:
                a messy nested dictionary of JSON containing <= 50 results
                or a giant html string, depending on your URL params & return_html flag.
        """
        response_object = self.search_2_response_obj()
        # Handle error-codes and Warn about potential garbage results if query URL is too long.
        if len(response_object.url) > 1300:
            print('WARNING: URL too long at {} characters.\n Bing can silently truncate your query.\n Limit URLs to < 1,200 chars.').format(len(response_object.url))
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
    ##   _methods used AFTER request is sent     ##
    ###############################################
    def _parse_json(self, json_response):
        """
        Takes raw JSON response and packages them as instances of class WebResult, NewsResult, etc...

        :param json_response: EX -- <requests_response_object>.json()

        :return list of WebResult objects: parsed and prettied JSON results with easy data-access.
                Returned as a LIST of xResult objects with len == the # of links returned by Bing.
        """

        ##TODO: break into parts

        # Catch and handle error-responses
        if json_response['_type'] == 'News':
            return [NewsResult(single_json_entry) for single_json_entry in json_response['value']]
        elif json_response['_type'] == 'SearchResponse':
            if not self.total_estimated_matches:
                try:
                    print(('Bing says there are an estimated {} results matching your query'.format(
                        json_response['webPages']['totalEstimatedMatches'])))
                    self.total_estimated_matches = int(json_response['webPages']['totalEstimatedMatches'])

                #TODO: !!!!! MASSIVE ASSUMPTION BEING MADE THAT NO 'webPages' value during a web-search == no results
                except KeyError:
                    Warning('No results')
                    return None
            packaged_json = [WebResult(single_json_entry) for single_json_entry in json_response['webPages']['value']]
            return packaged_json
        elif 'webPages' not in json_response.keys():
            try:
                if bool(json_response['rankingResponse']) is False:
                    if self._verbose:
                        print('NO RESULTS RETURNED BY BING. RETURNING ORIGINAL JSON.')
                    else: pass
                    return json_response
            except KeyError:
                # print('unable to determine if empty, attempting WebResult extraction.')
                pass
            try:
                link_list = json_response[self.params['responseFilter']]['value']
                try:
                    return [WebResult(single_json_entry) for single_json_entry in link_list]
                except Exception:
                    print('unrecognized response format.\n RETURNING LIST OF URLS, NOT WEBRESULT OBJECTS.')
                    return [json_item['url'] for json_item in link_list]
            except KeyError:
                try:
                    link_list = json_response['value']
                    return [single_json_entry['url'] for single_json_entry in link_list]
                except KeyError:
                    raise EnvironmentError('something is wrong with using responsefilter to id the json.\n aka I"m a bad coder')
        else: raise JsonParsingError('_parse_json in bingapipy did not parse correctly')

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
                raise IOError(static_constants._ERROR_CODES['429'])
        return r2

    ###############################################
    ##             change the query              ##
    ###############################################
    def _reset(self, new_key=None, new_query=None, new_endpoint=None, verbose=None, new_params=None, new_headers=None):
        # Welcome to hell.
        if verbose is not None:
            assert type(verbose) is bool
            self._verbose = verbose
        if new_key is not None:
            assert type(new_key) is str and len(new_key) == 32
            if self._key == new_key:
                if verbose == True:
                    print 'INFO: API key equals previous. No reassignment.'
                pass
            self.total_estimated_matches = 0
            self._key = new_key
        if new_query is not None:
            assert type(new_query) is str
            if self.query_plaintext == new_query:
                if verbose == True:
                    print 'INFO: Query equals previous. No reassignment.'
                pass
            self.total_estimated_matches = 0
            self.query_plaintext = new_query
        if new_endpoint is not None:
            assert new_endpoint in static_constants.API_ENDPOINTS.keys()
            if self.endpoint_type == new_endpoint:
                if verbose == True:
                    print 'INFO: Endpoint equals previous. No reassignment.'
                pass
            self.total_estimated_matches = 0
            self.endpoint_type = new_endpoint
        if new_headers is None and new_params is None:
            self._init_constructor_funcs(rewrite=True, skip_cleaning_headers_and_params=True)
        else:
            if new_params is not None:
                assert isinstance(new_params, dict)
                #We're gonna deal w/ the over-write overhead here in favor of avoiding _init_constructor_funcs() collisions
                self.total_estimated_matches = 0
                self.params = new_params
            if new_headers is not None:
                assert isinstance(new_headers, dict)
                self.total_estimated_matches = 0
                self.headers = new_headers
            self._init_constructor_funcs(rewrite=True)

    def _validate_reset(self):
        #TODO: make some checks to ensure all is good and nothing is broken.
        pass
    
    def _cache_previous_qdata(self):
        #TODO: store some portion of the previous call for anal-y-sis.
        pass
    
    def reset(self, new_key=None, new_query=None, new_endpoint=None, verbose=True, new_headers=None, new_params=None):
        """
        Use this function to reset a BingSearch instance with a new query-state.

        All args are optional, but you must use at least one of them or you will get an error
        informing you that you are trying to reset a query without telling it how.

        :param new_key: new api key <OPTIONAL>
        :param new_query: new value to put in q={} <OPTIONAL>
        :param new_endpoint: new endpoint URL to query <OPTIONAL>
        :param verbose: Make BingSearch quiet or noisy <OPTIONAL>
        :param new_headers: new dict of header-params <OPTIONAL>
        :param new_params: new dict of appended URL params <OPTIONAL>
        :return int:
                    0 on success, 1 on failure.
        """
        #TODO: Ideally, soon this won't be so turrible.
        try:
            self._validate_reset()
            self._cache_previous_qdata()
            self._reset(new_key=new_key, new_query=new_query, new_endpoint=new_endpoint, verbose=verbose, new_headers=new_headers, new_params=new_params)
            return 0
        except Exception:
            return 1

    ###############################################
    ##             Paging Support                ##
    ###############################################
    @staticmethod
    def _determine_num_of_paging_attempts(int_or_2_val_iterable):
        """
        Takes a positive integer or inclusive-range of 2 positive integers
        then returns a positive integer representing the number of times we will need
        to page through results.
        :param int_or_2_val_iterable: (type == int > 0) OR (type == Iterable AND len() == 2 AND min(Iterable) > 0)
        :return:
        """
        if type(int_or_2_val_iterable) is int:
            remainder_page = (1 if int_or_2_val_iterable % 50 != 0 else 0)
            base_pages = int_or_2_val_iterable / 50
            return base_pages + remainder_page

        elif isinstance(int_or_2_val_iterable, Iterable):
            start, stop = int_or_2_val_iterable[0], int_or_2_val_iterable[1]
            rec_count_desired = stop - start
            base_pages = rec_count_desired / 50
            remainder = (1 if rec_count_desired % 50 != 0 else 0)
            return base_pages + remainder
        else:
            raise ValueError('can only accept int or iterable of len == 2')

    
    def _pagination_loop(self, rec_count_desired, paging_attempts, return_type_function, break_on_nth_page=100):
        # import pdb
        # pdb.set_trace()
        """Soooooooo this guy. Essentially this is where the really convoluted magic happens."""

        # defining all possible functions as sub-calls for safetyism.
        def links_plaintext(SearchObj):
            return [decode_response_url(i.url) for i in SearchObj.search_2_packaged_json()]

        def links_encoded(SearchObj):
            return [i.url for i in SearchObj.search_2_packaged_json()]

        def json_packaged(SearchObj):
            return [i for i in SearchObj.search_2_packaged_json()]

        def json_raw(SearchObj):
            foo = SearchObj.search_2_json()
            return [foo]

        def full_response(SearchObj):
            foo = SearchObj.search_2_response_obj()
            return [foo]

        # dict fulla functions.
        function_types = {
            'links_plaintext': links_plaintext,
            'links_encoded': links_encoded,
            'json_packaged': json_packaged,
            'json_raw': json_raw,
            'full_response': full_response,
        }
        assert return_type_function in function_types.keys(), 'Invalid function passed to pagination loop. \nValid params are {}'.format(', '.join(function_types.keys()))
        rec_count_actual = 0
        current_attempt = 1
        full_package = []
        # passing
        desired_attempts = paging_attempts
        if desired_attempts > break_on_nth_page:
            print 'WARNING: break_on_nth_page set to {}, but {} pages requested.'.format(break_on_nth_page,
                                                                                         paging_attempts)
            desired_attempts = break_on_nth_page
        while current_attempt <= desired_attempts:
            # This if-statement will only kick in for the last page of results
            if rec_count_desired - rec_count_actual < 50:
                diff = rec_count_desired - rec_count_actual
                self.params.update({'count': diff})
            newlist = function_types[return_type_function](self)
            full_package += newlist
            rec_count_actual += len(newlist)
            current_attempt += 1
        return full_package
    

    def page(self, count_or_range=None, return_type_function='links_plaintext', break_on_nth_page=100, **kwargs):
        """
        :param count_or_range:
                    (type == int > 0) OR (type == Iterable AND len() == 2 AND min(Iterable) > 0).
                    Setting this equal to None will grab the first 50 records.
        :param return_type_function:
                    Options - 'links_plaintext', 'links_encoded', 'json_packaged', 'json_raw', 'full_response'
        :param break_on_nth_page:
                    Sidestepping the human error of accidentally sticking in an extra zero.
        :param kwargs:
                    Frankly nothing isn't accounted for at this point. Leaving the option open for later.
        :return:
                 An array of results. Their format will depend on the return_type_function you pass.
                 The default is a list of plaintext links.
        """
        if not count_or_range:
            full_package = self._pagination_loop(50, 1)
            return full_package
        # if count given as single digit, assume starting from 0
        elif type(count_or_range) == int:
            assert count_or_range >= 1, 'must provide positive count'
            rec_count_desired = count_or_range
            paging_attempts = BingSearch._determine_num_of_paging_attempts(rec_count_desired)

            # The below, terrible-terrible kwargs-handling starting at **dict(.....
            # prevents arbitrary kwargs from getting into the pagination process.
            # inspect makes an array of specific kwargs from the function being called.
            # I use this as a filter.
            return BingSearch._pagination_loop(self, rec_count_desired=rec_count_desired, paging_attempts=paging_attempts,
                                    return_type_function=return_type_function, break_on_nth_page=break_on_nth_page)
        # allow for a given range.
        elif isinstance(count_or_range, Iterable):
            # Must have len == 2
            assert len(count_or_range) == 2
            # Only non-negative numbers.
            assert min(count_or_range) >= 0
            # If the range is entered in backwards, reverse it.
            if count_or_range[0] > count_or_range[1]:
                count_or_range.reverse()
            elif count_or_range[0] == count_or_range[1]:
                raise ValueError("must specify range larger than 1")
            start, stop = count_or_range[0], count_or_range[1]
            rec_count_desired = stop - start
            # TODO: unit testing for `_determine_num_of_paging_attempts()`
            paging_attempts = BingSearch._determine_num_of_paging_attempts(count_or_range)
            self.params.update({'offset': str(start)})
            return self._pagination_loop( rec_count_desired=rec_count_desired, paging_attempts=paging_attempts,
                                    return_type_function=return_type_function, break_on_nth_page=break_on_nth_page)


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
        self.url_decoded = decode_response_url(self.url)

    def __str__(self):
        return 'WebResponse Obj: {}'.format(self.display_url)

    def __repr__(self):
        return '{}'.format(self.display_url)


class NewsResult(object):
    def __init__(self, result):
        try:
            self.about_name = result.get('about')[0]['name']
            self.about_readlink = result.get('about')[0]['readLink']
        except Exception:
            self.about_name = None
            self.about_readlink = None
        try:
            self.image_url = result.get('image')['thumbnail']['contentUrl']
            self.image_width = result.get('image')['thumbnail']['width']
            self.image_height = result.get('image')['thumbnail']['height']
        except Exception:
            self.image_url = None
            self.image_width = None
            self.image_height = None
        try:
            self.provider_type = result.get('provider')[0]['_type']
            self.provider_name = result.get('provider')[0]['name']
        except Exception:
            self.provider_type = None
            self.provider_name = None
        self.category = result.get('category')
        self.name = result.get('name')
        self.date_published = result.get('datePublished')
        self.description = result.get('description')
        self.url = result.get('url')
        self.url_decoded = decode_response_url(self.url)

    def __str__(self):
        return 'NewsResult'
###############################################
##                                           ##
##          class-independent funcs          ##
##                                           ##
###############################################
def _clear_null_vals(dictionary):
    """iterates over a dict forward-ways. Deletes NoneType entries."""
    return OrderedDict((k, v) for k, v in dictionary.items() if v)

def decode_response_url(bing_encoded_url):
    import urllib
    new_url = bing_encoded_url[153:-15].lstrip('=')
    ans = urllib.unquote(new_url).decode('utf8')
    # if, for any reason, urllib.unquote() fails, try again manually with binascii:
    if ans == bing_encoded_url[153:-15].lstrip('='):
        import binascii
        # yes it appears to be this easy.
        new_url = bing_encoded_url[153:-15].lstrip('=')
        new_new_url = new_url.replace('%3a', binascii.a2b_hex('3a'))
        new_url = new_new_url.replace('%2f', binascii.a2b_hex('2f'))
        new_new_url = new_url.replace('%3f', binascii.a2b_hex('3f'))
        ans2 = new_new_url.replace('%3d', binascii.a2b_hex('3d'))
        return ans2
    else: return ans

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
        elif str(response.status_code) in list(static_constants._ERROR_CODES.keys()):
            raise AssertionError(static_constants._ERROR_CODES[str(response.status_code)])
        else:
            raise ReferenceError('unknown status code returned: {}\nurl string is: {}'.format(response.status_code, response.url))
    else: return True


###############################################
##                                           ##
##       Constants specified by Bing         ##
##                                           ##
###############################################
class static_constants():
    API_ENDPOINTS = {
        'web': 'https://api.cognitive.microsoft.com/bing/v5.0/search?', # <-- SUPPORTED
        'images': 'https://api.cognitive.microsoft.com/bing/v5.0/images/search?',
        'images_trending': 'https://api.cognitive.microsoft.com/bing/v5.0/images/trending/search?', # <-- works only for mkt= en-US, en-CA, and en-AU
        'videos': 'https://api.cognitive.microsoft.com/bing/v5.0/videos/search?',
        'videos_trending': 'https://api.cognitive.microsoft.com/bing/v5.0/videos/trending/search?',
        'videos_details': 'https://api.cognitive.microsoft.com/bing/v5.0/videos/details/search?',
        'news': 'https://api.cognitive.microsoft.com/bing/v5.0/news/search?', # <-- SUPPORTED
        'news_categories': 'https://api.cognitive.microsoft.com/bing/v5.0/news?', # <-- SUPPORTED
        'news_trending': 'https://api.cognitive.microsoft.com/bing/v5.0/news/trendingtopics&',
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
    NEWS_CATEGORIES_US = (
        'Business',
        'Entertainment',
        'Entertainment_MovieAndTV',
        'Entertainment_Music',
        'Health',
        'Politics',
        'ScienceAndTechnology',
        'Science',
        'Technology',
        'Sports',
        'Sports_Golf',
        'Sports_MLB',
        'Sports_NBA',
        'Sports_NFL',
        'Sports_NHL',
        'Sports_Soccer',
        'Sports_Tennis',
        'Sports_CFB',
        'Sports_CBB',
        'US',
        'US_Northeast',
        'US_South',
        'US_Midwest',
        'US_West',
        'World',
        'World_Africa',
        'World_Americas',
        'World_Asia',
        'World_Europe',
        'World_MiddleEast',
    )
    NEWS_CATEGORIES_GB = (
        'Business',
        'Entertainment',
        'Health',
        'Politics',
        'ScienceAndTechnology',
        'Sports',
        'UK',
        'World',
    )
if __name__ == '__main__':
    key = 'ENTER_YOUR_API_KEY_HERE_ENTER_YOUR_API_KEY_HERE'

    q = 'Seattle +"engineer" intitle:"career*"'
    searcher = BingSearch(key, q)
    # res_list is an array of WebResult objects
    res_list = searcher.search_2_packaged_json()
    # Gives plaintext URLs of the first 10 records returned
    print [decode_response_url(i.url) for i in res_list[:10]]
    # Create a list of dictionaries from a list of WebResults. Print first record.
    res_list_converted_to_dicts = [WR.__dict__ for WR in res_list]
    print res_list_converted_to_dicts[0]