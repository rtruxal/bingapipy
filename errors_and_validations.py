class JsonParsingError(Exception):
    pass



###############################################
##                                           ##
##       Query & Response-checking.          ##
##    (currently not implemented above)      ##
##                                           ##
###############################################
class QueryChecker():
    """
    Isolated human-error-checker class.
    All methods are static and do not modify state.
    if/else mess below forgoes optimization in favor of clarity.
    """
    @staticmethod
    def check_web_params(query_dict, header_dict):
        responseFilters = ('Computation', 'Images', 'News', 'RelatedSearches', 'SpellSuggestions', 'TimeZone', 'Videos', 'Webpages')

        if 'cc' in list(query_dict.keys()):
            if query_dict['cc'] and not header_dict['Accept-Language']:
                raise AssertionError('Attempt to use cc_country-cc_code without specifying language.')
            if query_dict['mkt']:
                raise ReferenceError('cc and mkt cannot be specified simultaneously')

        if 'count' in list(query_dict.keys()) and query_dict['count']:
            if int(query_dict['count']) >= 51 or int(query_dict['count']) < 0:
                raise ValueError('Count specified out of range. 50 max objects returned.')

        if 'freshness' in list(query_dict.keys()) and query_dict['freshness']:
            if query_dict['freshness'] not in ('Day', 'Week', 'Month'):
                raise ValueError('Freshness must be == Day, Week, or Month. Assume Case-Sensitive.')

        if 'offset' in list(query_dict.keys()) and query_dict['offset']:
            if int(query_dict['offset']) < 0:
                raise ValueError('Offset cannot be negative.')

        if 'responseFilter' in list(query_dict.keys()) and query_dict['responseFilter']:
            if query_dict['responseFilter'] not in responseFilters:
                raise ValueError('Improper response filter.')

        if 'safeSearch' in list(query_dict.keys()) and query_dict['safeSearch']:
            if query_dict['safeSearch'] not in ('Off', 'Moderate', 'Strict'):
                raise ValueError('safeSearch setting must be Off, Moderate, or Strict. Assume Case-Sensitive.')
            if 'X-Search-ClientIP' in list(header_dict.keys()) and header_dict['X-Search-ClientIP']:
                Warning('You have specified both an X-Search-ClientIP header and safesearch setting\nplease note: header takes precedence')

        if 'setLang' in list(query_dict.keys()):
            if 'Accept-Language' in list(header_dict.keys()) and header_dict['Accept-Language']:
                raise AssertionError('Attempt to use both language header and query param.')

        if 'textDecorations' in list(query_dict.keys()) and query_dict['textDecorations']:
            if query_dict['textDecorations'].lower() not in ('true', 'false'):
                raise TypeError('textDecorations is type bool')

        if 'textFormat' in list(query_dict.keys()) and query_dict['textFormat']:
            if query_dict['textFormat'] not in ('Raw', 'HTML'):
                raise ValueError('textFormat must be == Raw or HTML. Assume Case-Sensitive.')

        return True
#
# class ResponseChecker():
#     """
#     Meant to examine returned objects and check/handle errors.
#     """
#     @staticmethod
#     def validate_request_response(response):
#         """
#         Return nothing if valid response object returned.
#         Otherwise handle or throw exceptions
#         :param response: requests.response object.
#         :return: func will pass or raise exception. That's all.
#         """
#         if not response.status_code == 200:
#             if response.status_code == 429:
#                 print('queries/second quota exceeded. this func will make 5 attempts to resend.')
#                 return '429'
#             elif response.status_code == 400:
#                 json = response.json()
#                 print '400 error: Bad params\n\nBing is showing {} param(s) set to {}'.format(json['errors'][0]['parameter'], json['errors'][0]['value'])
#                 raise ValueError()
#             elif str(response.status_code) in list(local_static_constants._ERROR_CODES.keys()):
#                 raise AssertionError(static_constants._ERROR_CODES[str(response.status_code)])
#             else:
#                 raise ReferenceError('unknown status code returned: {}\nurl string is: {}'.format(response.status_code, response.url))
#         else: return True
#
#     @staticmethod
#     def _handle_429_error(url):
#         timeout_cnt = 0
#         while True:
#             if timeout_cnt < 5:
#                 sleep(2)
#                 r2 = requests.get(url, self.header)
#                 if ResponseChecker.validate_request_response(r2) == '429':
#                     timeout_cnt += 1
#                     pass
#                 elif r2.status_code == 200:
#                     break
#                 else:
#                     raise AssertionError('response not successful')
#             else:
#                 raise IOError(static_constants._ERROR_CODES['429'])
#         return r2
#
#     @staticmethod
#     def validations_and_429_handling(response):
#         resp = validate_request_response(response)
#         if resp == '429':
#             resp = _handle_429_error(response)
#         return resp
