import requests
from eth_account.messages import encode_defunct
from fake_useragent import UserAgent
from curl_cffi.requests import Session
from loguru import logger
import time
import urllib.parse
import uuid
from urllib.parse import urlparse, parse_qs
from web3 import Web3
import json
def extract_code(url):
    """
    从 URL 中提取 code 参数值
    :param url: 包含 code 参数的 URL
    :return: 提取的 code 值
    """
    parsed_url = urlparse(url)  # 解析 URL
    query_params = parse_qs(parsed_url.query)  # 提取查询参数
    code = query_params.get('code', [None])[0]  # 获取 code 参数的值
    return code


#初始化web3
w3 = Web3(Web3.HTTPProvider('https://rpc-holesky.morphl2.io'))
ua = UserAgent()
class Twitter_Sync:
    def __init__(self, auth_token, proxies=None):
        self.auth_token = auth_token
        defaulf_cookies = {
            "auth_token": auth_token,
        }

        bearer_token = "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"
        defaulf_headers = {
            "authority": "x.com",
            "origin": "https://x.com",
            "x-twitter-active-user": "yes",
            "x-twitter-client-language": "en",
            "authorization": bearer_token,
            "user-agent": ua.edge,
            "x-client-uuid": str(uuid.uuid4())

        }
        if proxies:
            self.Twitter = Session(headers=defaulf_headers, cookies=defaulf_cookies, timeout=120, impersonate='edge99',
                                   proxies=proxies)
            self.X = Session(headers=defaulf_headers, cookies=defaulf_cookies, timeout=120, impersonate='edge99')
        else:
            self.Twitter = Session(headers=defaulf_headers, cookies=defaulf_cookies, timeout=120, impersonate='edge99',
                                   proxies=proxies)
            self.X = Session(headers=defaulf_headers, cookies=defaulf_cookies, timeout=120, impersonate='edge99')
        self.auth_code = None
        self.auth_success = False  # 增加标志位记录授权是否成功
        self.init_ct0()

    def init_ct0(self):
        response = self.Twitter.get('https://twitter.com/i/api/2/oauth2/authorize')
        if response.status_code == 401:
            raise ValueError('推特token失效')
        self.Twitter.headers.update({"x-csrf-token": self.Twitter.cookies["ct0"]})
        response = self.X.get('https://x.com/i/api/graphql/Yka-W8dz7RaEuQNkroPkYw/UserByScreenName')
        self.X.headers.update({"x-csrf-token": self.X.cookies["ct0"]})

    def get_auth_codeV2(self, client_id, state, code_challenge, redirect_uri, scope, code_challenge_method='plain',
                        response_type='code'):
        # 如果已经授权成功，直接返回 True，不再进行授权
        if self.auth_success:
            logger.info(f'{self.auth_token} 已成功授权，跳过重新授权')
            return True

        try:
            params = {
                'code_challenge': urllib.parse.unquote(code_challenge),
                'code_challenge_method': urllib.parse.unquote(code_challenge_method),
                'client_id': urllib.parse.unquote(client_id),
                'redirect_uri': urllib.parse.unquote(redirect_uri),
                'response_type': urllib.parse.unquote(response_type),
                'scope': urllib.parse.unquote(scope),
                'state': state
            }
            response = self.Twitter.get('https://twitter.com/i/api/2/oauth2/authorize', params=params)
            if "code" in response.json() and response.json()["code"] == 353:
                self.Twitter.headers.update({"x-csrf-token": response.cookies["ct0"]})
                logger.warning(f'{response.json()}')
                return self.get_auth_codeV2(client_id, state, code_challenge, redirect_uri, scope,
                                            code_challenge_method, response_type)
            elif response.status_code == 429:
                time.sleep(5)
                return self.get_auth_codeV2(client_id, state, code_challenge, redirect_uri, scope,
                                            code_challenge_method, response_type)
            elif 'auth_code' in response.json():
                self.auth_code = response.json()['auth_code']
                return True
            logger.error(f'{self.auth_token} 获取auth_code失败')
            return False
        except Exception as e:
            logger.error(e)
            return False

    def twitter_authorizeV1(self, authenticity_token, oauth_token):
        # 如果已经授权成功，直接返回 True，不再进行授权
        if self.auth_success:
            logger.info(f'{self.auth_token} 已成功授权，跳过重新授权')
            return True

        try:
            data = {
                'authenticity_token': authenticity_token,
                'redirect_after_login': f'https://api.x.com/oauth/authorize?oauth_token={oauth_token}',
                'oauth_token': oauth_token,
            }
            response = self.Twitter.post('https://x.com/oauth/authorize', data=data)
            if 'redirect_uri' in response.text:
                self.auth_success = True  # 授权成功，设置标志位
                return True
            elif response.status_code == 429:
                time.sleep(5)
                return self.twitter_authorizeV1(authenticity_token, oauth_token)
            logger.error(f'{self.auth_token} 推特授权失败')
            return False
        except Exception as e:
            logger.error(f'{self.auth_token} 推特授权异常：{e}')
            return False

    def twitter_authorizeV2(self, client_id, state, code_challenge, redirect_uri, scope, code_challenge_method='plain',
                            response_type='code'):
        # 如果已经授权成功，直接返回 True，不再进行授权
        if self.auth_success:
            logger.info(f'{self.auth_token} 已成功授权，跳过重新授权')
            return True

        try:
            if not self.get_auth_codeV2(client_id, state, code_challenge, redirect_uri, scope, code_challenge_method,
                                        response_type):
                return False
            data = {
                'approval': 'true',
                'code': self.auth_code,
            }
            response = self.Twitter.post('https://twitter.com/i/api/2/oauth2/authorize', data=data)
            return extract_code(response.json()['redirect_uri'])
      
    
        except Exception as e:
            logger.error(f'{self.auth_token} 推特授权异常：{e}')
            return False

    def get_rest_id(self, screen_name: str):
        params = {
            'variables': '{"screen_name":"%s"}' % (screen_name.lower()),
            'features': '{"hidden_profile_subscriptions_enabled":true,"rweb_tipjar_consumption_enabled":true,"responsive_web_graphql_exclude_directive_enabled":true,"verified_phone_label_enabled":false,"subscriptions_verification_info_is_identity_verified_enabled":true,"subscriptions_verification_info_verified_since_enabled":true,"highlights_tweets_tab_ui_enabled":true,"responsive_web_twitter_article_notes_tab_enabled":true,"subscriptions_feature_can_gift_premium":true,"creator_subscriptions_tweet_preview_api_enabled":true,"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,"responsive_web_graphql_timeline_navigation_enabled":true}',
            'fieldToggles': '{"withAuxiliaryUserLabels":false}',
        }
        response = self.X_http('https://x.com/i/api/graphql/BQ6xjFU6Mgm-WhEP3OiT9w/UserByScreenName', type='GET',
                               data=params)
        return response.get('data', {}).get('user', {}).get('result', {}).get('rest_id')

    def create(self, screen_name):
        user_id = self.get_rest_id(screen_name)
        data = {
            'include_profile_interstitial_type': '1',
            'include_blocking': '1',
            'include_blocked_by': '1',
            'include_followed_by': '1',
            'include_want_retweets': '1',
            'include_mute_edge': '1',
            'include_can_dm': '1',
            'include_can_media_tag': '1',
            'include_ext_is_blue_verified': '1',
            'include_ext_verified_type': '1',
            'include_ext_profile_image_shape': '1',
            'skip_status': '1',
            'user_id': user_id,
        }
        response = self.X_http('https://x.com/i/api/1.1/friendships/create.json', data=data)
        return response

    def destroy(self, screen_name):
        user_id = self.get_rest_id(screen_name)
        data = {
            'include_profile_interstitial_type': '1',
            'include_blocking': '1',
            'include_blocked_by': '1',
            'include_followed_by': '1',
            'include_want_retweets': '1',
            'include_mute_edge': '1',
            'include_can_dm': '1',
            'include_can_media_tag': '1',
            'include_ext_is_blue_verified': '1',
            'include_ext_verified_type': '1',
            'include_ext_profile_image_shape': '1',
            'skip_status': '1',
            'user_id': user_id,
        }
        response = self.X_http('https://x.com/i/api/1.1/friendships/destroy.json', data=data)
        return response

    def X_http(self, url, type='POST', data=None, json=None):
        if type == "GET":
            response = self.X.get(url, params=data)
        elif type == "POST":
            response = self.X.post(url, data=data, json=json)
        else:
            raise ValueError(f'不支持{type}')
        self.X.headers.update({'x-csrf-token': self.X.cookies.get('ct0')})
        try:
            resp = response.json()
        except:
            raise ValueError(response.text)
        if 'like it might be automated' in str(resp.get('errors')):
            time.sleep(10)
            self.X_http(self, url, type, data)
        assert resp.get('errors') is None or 'already' in str(resp.get('errors')), str(resp.get('errors'))
        return resp

    def like(self, tweet_id):
        json_data = {
            'variables': {
                'tweet_id': tweet_id,
            },
            'queryId': 'lI07N6Otwv1PhnEgXILM7A',
        }
        response = self.X_http('https://x.com/i/api/graphql/lI07N6Otwv1PhnEgXILM7A/FavoriteTweet', json=json_data)
        return response

    def cancel_like(self, tweet_id):
        json_data = {
            'variables': {
                'tweet_id': tweet_id,
            },
            'queryId': 'ZYKSe-w7KEslx3JhSIk5LA',
        }
        response = self.X_http('https://x.com/i/api/graphql/ZYKSe-w7KEslx3JhSIk5LA/UnfavoriteTweet', json=json_data)
        return response

    def retweet(self, tweet_id):
        json_data = {
            'variables': {
                'tweet_id': tweet_id,
                'dark_request': False,
            },
            'queryId': 'ojPdsZsimiJrUGLR1sjUtA',
        }
        response = self.X_http('https://x.com/i/api/graphql/ojPdsZsimiJrUGLR1sjUtA/CreateRetweet', json=json_data)
        return response

    def create_twitter(self, content):
        json_data = {
            'variables': {
                'tweet_text': content,
                'dark_request': False,
                'media': {
                    'media_entities': [],
                    'possibly_sensitive': False,
                },
                'semantic_annotation_ids': [],
                'disallowed_reply_options': None,
            },
            'features': {
                'communities_web_enable_tweet_community_results_fetch': True,
                'c9s_tweet_anatomy_moderator_badge_enabled': True,
                'responsive_web_edit_tweet_api_enabled': True,
                'graphql_is_translatable_rweb_tweet_is_translatable_enabled': True,
                'view_counts_everywhere_api_enabled': True,
                'longform_notetweets_consumption_enabled': True,
                'responsive_web_twitter_article_tweet_consumption_enabled': True,
                'tweet_awards_web_tipping_enabled': False,
                'creator_subscriptions_quote_tweet_preview_enabled': False,
                'longform_notetweets_rich_text_read_enabled': True,
                'longform_notetweets_inline_media_enabled': True,
                'articles_preview_enabled': True,
                'rweb_video_timestamps_enabled': True,
                'rweb_tipjar_consumption_enabled': True,
                'responsive_web_graphql_exclude_directive_enabled': True,
                'verified_phone_label_enabled': False,
                'freedom_of_speech_not_reach_fetch_enabled': True,
                'standardized_nudges_misinfo': True,
                'tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled': True,
                'responsive_web_graphql_skip_user_profile_image_extensions_enabled': False,
                'responsive_web_graphql_timeline_navigation_enabled': True,
                'responsive_web_enhance_cards_enabled': False,
            },
            'queryId': 'znq7jUAqRjmPj7IszLem5Q',
        }
        response = self.X_http('https://x.com/i/api/graphql/znq7jUAqRjmPj7IszLem5Q/CreateTweet', json=json_data)
        return response

    def quote_retweet(self, url):
        json_data = {
            'variables': {
                'tweet_text': '@AdamSchefter @ladygaganownet @TheGSDGroup @WWE @gadgetlab ',
                'attachment_url': url,
                'dark_request': False,
                'media': {
                    'media_entities': [],
                    'possibly_sensitive': False,
                },
                'semantic_annotation_ids': [],
                'disallowed_reply_options': None,
            },
            'features': {
                'communities_web_enable_tweet_community_results_fetch': True,
                'c9s_tweet_anatomy_moderator_badge_enabled': True,
                'responsive_web_edit_tweet_api_enabled': True,
                'graphql_is_translatable_rweb_tweet_is_translatable_enabled': True,
                'view_counts_everywhere_api_enabled': True,
                'longform_notetweets_consumption_enabled': True,
                'responsive_web_twitter_article_tweet_consumption_enabled': True,
                'tweet_awards_web_tipping_enabled': False,
                'creator_subscriptions_quote_tweet_preview_enabled': False,
                'longform_notetweets_rich_text_read_enabled': True,
                'longform_notetweets_inline_media_enabled': True,
                'articles_preview_enabled': True,
                'rweb_video_timestamps_enabled': True,
                'rweb_tipjar_consumption_enabled': True,
                'responsive_web_graphql_exclude_directive_enabled': True,
                'verified_phone_label_enabled': False,
                'freedom_of_speech_not_reach_fetch_enabled': True,
                'standardized_nudges_misinfo': True,
                'tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled': True,
                'responsive_web_graphql_skip_user_profile_image_extensions_enabled': False,
                'responsive_web_graphql_timeline_navigation_enabled': True,
                'responsive_web_enhance_cards_enabled': False,
            },
            'queryId': 'xT36w0XM3A8jDynpkram2A',
        }
        response = self.X_http('https://x.com/i/api/graphql/xT36w0XM3A8jDynpkram2A/CreateTweet', json=json_data)
        return response

    def cancel_retweet(self, tweet_id):
        json_data = {
            'variables': {
                'source_tweet_id': tweet_id,
            },
            'queryId': 'iQtK4dl5hBmXewYZuEOKVw',
        }
        response = self.X_http('https://x.com/i/api/graphql/iQtK4dl5hBmXewYZuEOKVw/DeleteRetweet', json=json_data)
        return response


def get(li: list, index: int = 0):
    if len(li) > index:
        return li[index]
    else:
        return ""


def get_morphl_x_params(address, signature):
    url = "https://events-social-api-holesky.morphl2.io/login"

    # 查询参数
    params = {
        "address": address,
        "app": "twitter",
        "redirect": "https://www.morphl2.io/points/genesis_jungle/mypoints",
        "sigMsg": signature
    }

    # 请求头部
    headers = {
        "sec-ch-ua": '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "sec-fetch-site": "same-site",
        "sec-fetch-mode": "navigate",
        "sec-fetch-dest": "document",
        "referer": "https://www.morphl2.io/",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8"
    }

    response = requests.get(url, headers=headers, params=params, allow_redirects=False)
    if response.status_code == 307:
        redirect_url = response.headers['Location']
        parsed_url = urlparse(redirect_url)
        query_params = parse_qs(parsed_url.query)
        return {
            'client_id': query_params['client_id'][0],
            'state': query_params['state'][0],
            'scope': query_params['scope'][0],
            'code_challenge': query_params['code_challenge'][0],
            'response_type': query_params['response_type'][0],
            'code_challenge_method': query_params['code_challenge_method'][0],
            'redirect_uri': query_params['redirect_uri'][0],
        }


def send_get_request(token):
    cls = Twitter_Sync(token)
    params = {
        'client_id': 'Zm42al9ZVk9QMWJDQ2dkaHB3MnU6MTpjaQ',
        'state': 'Redacted',
        'scope': 'tweet.read%20users.read',
        'code_challenge': 'Redacted',
        'response_type': 'code',
        'code_challenge_method': 'plain',
        'redirect_uri': 'https%3A%2F%2Fquest.redactedairways.com%2Flogin',
    }
    data = cls.twitter_authorizeV2(**params)
    url = "https://quest.redactedairways.com/ecom-gateway/twitter/callback"
    params = {
        "state": "Redacted",
        "code": {data}
    }
    headers = {
        "sec-ch-ua-platform": '"Windows"',
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "sec-ch-ua": '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": "https://quest.redactedairways.com/login?state=Redacted&code=UjNiUFhqZ290S3BtbWRfaWMtZUhuUF9MM1JDRERaeEtTWEhLZDFmamN0bGZ3OjE3MzE4MzQ3OTcwNjU6MToxOmFjOjE",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Cookie": "_ga=GA1.1.1718485006.1731828133; _ga_79MVPN70LJ=GS1.1.1731832087.2.1.1731834865.0.0.0"
    }

    response = requests.get(url, headers=headers, params=params)
    print("X token 状态码:", response.status_code)
    return response.json()

