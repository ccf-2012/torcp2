# -*- coding: utf-8 -*-
import re
import time
from loguru import  logger
import requests
import tortitle
from .torcategory import TorCategory

GENRE_LIST_en = [{'id': 28, 'name': 'Action'}, {'id': 12, 'name': 'Adventure'}, {'id': 16, 'name': 'Animation'}, {'id': 35, 'name': 'Comedy'}, 
                 {'id': 80, 'name': 'Crime'}, {'id': 99, 'name': 'Documentary'}, {'id': 18, 'name': 'Drama'}, {'id': 10751, 'name': 'Family'}, 
                 {'id': 14, 'name': 'Fantasy'}, {'id': 36, 'name': 'History'}, {'id': 27, 'name': 'Horror'}, {'id': 10402, 'name': 'Music'}, 
                 {'id': 9648, 'name': 'Mystery'}, {'id': 10749, 'name': 'Romance'}, {'id': 878, 'name': 'Science Fiction'}, 
                 {'id': 10770, 'name': 'TV Movie'}, {'id': 53, 'name': 'Thriller'}, {'id': 10752, 'name': 'War'}, 
                 {'id': 37, 'name': 'Western'}, {'id': 10763, 'name': 'News'}, {'id': 10764, 'name': 'Reality'}, 
                 {'id': 10762, 'name': 'Kids'}, 
                 {'id': 10765, 'name': 'Sci-Fi & Fantasy'}, {'id': 10766, 'name': 'Soap'}, {'id': 10767, 'name': 'Talk'}, 
                 {'id': 10768, 'name': 'War & Politics'}]
GENRE_LIST_cn = [{'id': 28, 'name': '动作'}, {'id': 12, 'name': '冒险'}, {'id': 16, 'name': '动画'}, {'id': 35, 'name': '喜剧'}, 
                 {'id': 80, 'name': '犯罪'}, {'id': 99, 'name': '纪录'}, {'id': 18, 'name': '剧情'}, {'id': 10751, 'name': '家庭'}, 
                 {'id': 14, 'name': '奇幻'}, {'id': 36, 'name': '历史'}, {'id': 27, 'name': '恐怖'}, {'id': 10402, 'name': '音乐'},
                 {'id': 9648, 'name': '悬疑'}, {'id': 10749, 'name': '爱情'}, {'id': 878, 'name': '科幻'}, 
                 {'id': 10770, 'name': '电视电影'}, {'id': 53, 'name': '惊悚'},  {'id': 10752, 'name': '战争'}, 
                 {'id': 10762, 'name': '儿童'},
                 {'id': 37, 'name': '西部'}, {'id': 10763, 'name': '新闻'}, {'id': 10764, 'name': '真人秀'}, 
                 {'id': 10765, 'name': 'Sci-Fi & Fantasy'}, {'id': 10766, 'name': '肥皂剧'}, {'id': 10767, 'name': '脱口秀'}, 
                 {'id': 10768, 'name': 'War & Politics'}]




def _ccfcat_to_tmdbcat(cat):
    if re.match(r'(Movie)', cat, re.I):
        return 'movie'
    elif re.match(r'(TV)', cat, re.I):
        return 'tv'
    else:
        return cat

def tryint(instr):
    try:
        string_int = int(instr)
    except ValueError:    
        string_int = 0
    return string_int


class TMDbNameParser():
    """A class to parse torrent names and query The Movie Database (TMDb) for additional information."""
    def __init__(self, torcpdb_url, torcpdb_apikey):
        """Initializes the TMDbNameParser object."""
        self.title = ''
        self.year = 0
        self.tmdbid = 0
        self.tmdbhard = False
        self.season = ''
        self.episode = ''
        self.cntitle = ''
        self.resolution = ''
        self.group = ''
        self.tmdbcat = ''
        self.original_language = ''
        self.popularity = 0
        self.poster_path = ''
        self.release_air_date = ''
        self.genres = ''
        self.media_source = ''
        self.video_codec = ''
        self.audio_codec = ''
        self.imdbid = ''
        self.imdbval = 0.0
        self.torname = ''
        self.origin_country = ''
        self.original_title = ''
        self.overview = ''
        self.vote_average = 0
        self.production_countries = ''
        self.ccfcat = ''

        self.torcpdb_url = torcpdb_url
        self.torcpdb_apikey = torcpdb_apikey
        # self.tmdb_details = None

    def _fix_season_name(self, seasonStr):
        if re.match(r'^Ep?\d+(-Ep?\d+)?$', seasonStr,
                    flags=re.I) or not seasonStr:
            return 'S01'
        else:
            return seasonStr.upper()

    def get_genres_list(self):
        return [x.strip() for x in self.genres.split(',')]
        # ll = []
        # if self.genres:
        #     genre_list = GENRE_LIST_cn
        #     for x in self.genres:
        #         s = next((y for y in genre_list if str(y['id'])==x), None)
        #         if s:
        #             ll.append(s['name'])
        # return ll

    def get_genres_str(self):
        genrestr = ''
        if self.genres:
            genre_list = GENRE_LIST_cn
            for x in self.genres:
                s = next((y for y in genre_list if y['id']==x), None)
                if s:
                    genrestr += s['name'] 
        return genrestr

    def parse(self, torname, by_tordb=False, imdbid=None, tmdbid=None, extitle='', infolink=''):
        """Parses a torrent name and queries TMDb for more information."""
        self.torname = torname
        tc = TorCategory(torname)
        self.ccfcat, self.group, self.resolution = tc.ccfcat, tc.group, tc.resolution
        tt = tortitle.TorTitle(torname)
        self.title, parseYear, self.season, self.episode, self.cntitle = tt.title, tt.year, tt.season, tt.episode, tt.cntitle 
        self.media_source, self.video_codec, self.audio_codec = tt.media_source, tt.video, tt.audio
        self.year = tryint(parseYear)

        if self.ccfcat == 'TV':
            self.season = self._fix_season_name(self.season)

        self.tmdbcat = _ccfcat_to_tmdbcat(self.ccfcat)
        if (not imdbid) and (not tmdbid) and (self.tmdbcat not in ['tv', 'movie']):
            logger.info('can not identify movie/tv, set to movie')
            self.tmdbcat = 'movie'

        if by_tordb:
            attempts = 0
            while attempts < 3:
                try:
                    json_data = {}
                    json_data['torname'] = torname
                    if extitle:
                        json_data['extitle'] = extitle
                    if infolink:
                        json_data['infolink'] = infolink
                    if tmdbid:
                        json_data['tmdbstr'] = tmdbid
                    if imdbid:
                        json_data['imdbid'] = imdbid
                    logger.info(f'torname: {torname}, tmdbstr: {tmdbid}, imdbid: {imdbid}, exTitle: {extitle}, infolink: {infolink}')
                    result = self.query_torcpdb(json_data)
                    if result:
                        self._save_result(result)
                        if self.tmdbid > 0:
                            if "id_score" in result:
                                logger.debug(f'identication score: {result["id_score"]}')
                            logger.success(f'TMDb查得: {self.tmdbcat}-{self.tmdbid}, {self.title}, {self.year}, {self.genres}, {self.origin_country}, {self.original_title}')
                        else:
                            logger.warning(f'TMDb 没有结果: {torname}, {extitle}, {imdbid}, {infolink}')
                    else:
                        logger.warning(f'TMDb 没有结果: {torname}, {extitle}, {imdbid}, {infolink}')

                    break
                except:
                    attempts += 1
                    logger.warning("TORCPDb connection failed. Trying %d " % attempts)
                    time.sleep(3)

    def query_torcpdb(self, json_data):
        if self.torcpdb_apikey:
            headers = {
                'User-Agent': 'python/request:torcp',
                'X-API-Key': self.torcpdb_apikey
            }    
        try:
            response = requests.post(
                self.torcpdb_url+ "/api/query", 
                headers=headers,
                json=json_data
            )
            if response.status_code == 404:
                logger.debug(f'{json_data["torname"]} not found')
            # response.raise_for_status()  # 如果响应状态码不是200，抛出异常
            return response.json()
        except requests.RequestException as e:
            print(f"查询失败: {str(e)}")
            raise

    def _save_result(self, result):
        # logger.debug(f"Received from torcpdb: {result}")
        if "tmdb_title" in result:
            self.title = result["tmdb_title"]
        if "tmdb_cat" in result:
            self.tmdbcat = result["tmdb_cat"]
        if "tmdb_id" in result:
            self.tmdbid = result["tmdb_id"]
        if "imdb_id" in result:
            self.imdbid = result["imdb_id"]
        if "imdb_val" in result:
            self.imdbval = result["imdb_val"]
        if "tmdb_year" in result:
            self.year = result["tmdb_year"]
        if "original_language" in result:
            self.original_language = result["original_language"]
        if "popularity" in result:
            self.popularity = result["popularity"]
        if "tmdb_poster" in result:
            self.poster_path = result["tmdb_poster"]
        if "release_air_date" in result:
            self.release_air_date = result["release_air_date"]
        if "tmdb_genres" in result:
            self.genres = result["tmdb_genres"]
        if "origin_country" in result:
            self.origin_country = result["origin_country"]
        if "original_title" in result:
            self.original_title = result["original_title"]
        if "tmdb_overview" in result:
            self.overview = result["tmdb_overview"]
        if "vote_average" in result:
            self.vote_average = result["vote_average"]
        if "production_countries" in result:
            self.production_countries = result["production_countries"]

    def get_production_area(self):
        if self.tmdbcat == 'tv':
            if self.origin_country:
                return self.origin_country
            elif self.original_language:
                return self.original_language
        else:            
            if self.production_countries:
                return self.production_countries
            elif self.original_language:
                return self.original_language

        return ''

