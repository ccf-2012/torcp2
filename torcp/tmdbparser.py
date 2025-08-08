# -*- coding: utf-8 -*-
import re
import time
from loguru import  logger
import requests
from torcp import tortitle
from torcp.torcategory import TorCategory

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




def transFromCCFCat(cat):
    if re.match(r'(Movie)', cat, re.I):
        return 'movie'
    elif re.match(r'(TV)', cat, re.I):
        return 'tv'
    else:
        return cat


def transToCCFCat(mediatype, originCat):
    if mediatype == 'tv':
        return 'TV'
    elif mediatype == 'movie':
        if not re.match(r'(movie)', originCat, re.I):
            return 'Movie'
    return originCat


def tryint(instr):
    try:
        string_int = int(instr)
    except ValueError:    
        string_int = 0
    return string_int

def parseTMDbStr(tmdbstr):
    if tmdbstr.isnumeric():
        return '', tmdbstr
    m = re.search(r'(m(ovie)?|t(v)?)?[-_]?(\d+)', tmdbstr.strip(), flags=re.A | re.I)
    if m:
        if m[1]:
            catstr = 'movie' if m[1].startswith('m') else 'tv'
        else:
            catstr = ''
        return catstr, m[4]
    else:
        return '', ''

class TMDbNameParser():
    def __init__(self, torcpdb_url, torcpdb_apikey, ccfcat_hard=None):
        self.ccfcatHard = ccfcat_hard
        self.ccfcat = ''
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
        self.genre_ids =[]
        self.release_air_date = ''
        self.mediaSource = ''
        self.videoCodec = ''
        self.audioCodec = ''
        self.imdbid = ''
        self.imdbval = 0.0

        self.torcpdb_url = torcpdb_url
        self.torcpdb_apikey = torcpdb_apikey

    def fixSeasonName(self, seasonStr):
        if re.match(r'^Ep?\d+(-Ep?\d+)?$', seasonStr,
                    flags=re.I) or not seasonStr:
            return 'S01'
        else:
            return seasonStr.upper()

    def getGenres(self):
        ll = []
        if self.genre_ids:
            genre_list = GENRE_LIST_cn
            for x in self.genre_ids:
                s = next((y for y in genre_list if str(y['id'])==x), None)
                if s:
                    ll.append(s['name'])
        return ll

    def getGenreStr(self):
        genrestr = ''
        if self.genre_ids:
            genre_list = GENRE_LIST_cn
            for x in self.genre_ids:
                s = next((y for y in genre_list if y['id']==x), None)
                if s:
                    genrestr += s['name'] 
        return genrestr

    def genreStr2List(self, genrestr):
        return genrestr.split(',')

    def clearData(self):
        self.ccfcat = ''
        self.title = ''
        self.year = 0
        self.tmdbid = -1
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
        self.genre_ids =[]
        self.tmdbDetails = None
        self.imdbid = ''
        self.imdbval = 0.0
        self.origin_country = ''
        self.original_title = ''
        self.overview = ''
        self.vote_average = 0
        self.production_countries = ''

    def parse(self, torname, useTMDb=False, hasIMDbId=None, hasTMDbId=None, exTitle='', infolink=''):
        self.clearData()
        tc = TorCategory(torname)
        self.ccfcat, self.group = tc.ccfcat, tc.group
        self.resolution = tc.resolution
        tt = tortitle.TorTitle(torname)
        self.title, parseYear, self.season, self.episode, self.cntitle = tt.title, tt.yearstr, tt.season, tt.episode, tt.cntitle 
        self.mediaSource, self.videoCodec, self.audioCodec = tt.parseTorNameMore(torname)
        self.year = tryint(parseYear)

        if self.season and (self.ccfcat != 'TV'):
            # print('Category fixed: ' + movieItem)
            self.ccfcat = 'TV'
        if self.ccfcat == 'TV':
            self.season = self.fixSeasonName(self.season)

        if self.ccfcatHard:
            self.ccfcat = self.ccfcatHard

        self.tmdbcat = transFromCCFCat(self.ccfcat)
        if (not hasIMDbId) and (not hasTMDbId) and (self.tmdbcat not in ['tv', 'movie']):
            logger.warning('no IMDb id and not movie/tv')
            return

        if useTMDb:
            attempts = 0
            # TODO: 可能可用，待调试
            # if not hasIMDbId:
            #     if imdbid := self.checkNameContainsIMDbId(torname):
            #         hasIMDbId = imdbid
            # if not hasTMDbId:
            #     if tmdbid := self.checkNameContainsTMDbId(torname):
            #         hasTMDbId = tmdbid

            while attempts < 3:
                try:
                    json_data = {}
                    json_data['torname'] = torname
                    if exTitle:
                        json_data['extitle'] = exTitle
                    if infolink:
                        json_data['infolink'] = infolink
                    if hasTMDbId:
                        json_data['tmdbstr'] = hasTMDbId
                    if hasIMDbId:
                        json_data['imdbid'] = hasIMDbId
                    logger.info(f'torname: {torname}, tmdbstr: {hasTMDbId}, imdbid: {hasIMDbId}, exTitle: {exTitle}, infolink: {infolink}')
                    result = self.query_torcpdb(json_data)
                    if result['success']:
                        self.saveResult(result)
                        logger.success(f'TMDb查得: {result["data"]["tmdb_cat"]}-{result["data"]["tmdb_id"]}, {result["data"]["tmdb_title"]}, {result["data"]["year"]}, {result["data"]["production_countries"]}, {result["data"]["genre_ids"]}')
                        self.ccfcat = transToCCFCat(self.tmdbcat, self.ccfcat)
                    else:
                        logger.warning(f'TMDb 没有结果: {torname}, {exTitle}, {hasIMDbId}, {infolink}')

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
            response.raise_for_status()  # 如果响应状态码不是200，抛出异常
            return response.json()
        except requests.RequestException as e:
            print(f"查询失败: {str(e)}")
            raise

    def saveResult(self, result):
        if "data" in result:
            if "tmdb_title" in result["data"]:
                self.title = result["data"]["tmdb_title"]
            if "tmdb_title" in result["data"]:
                self.title = result["data"]["tmdb_title"]
            if "tmdb_cat" in result["data"]:
                self.tmdbcat = result["data"]["tmdb_cat"]
            if "tmdb_id" in result["data"]:
                self.tmdbid = result["data"]["tmdb_id"]
            if "imdb_id" in result["data"]:
                self.imdbid = result["data"]["imdb_id"]
            if "imdb_val" in result["data"]:
                self.imdbval = result["data"]["imdb_val"]
            if "year" in result["data"]:
                self.year = result["data"]["year"]
            if "original_language" in result["data"]:
                self.original_language = result["data"]["original_language"]
            if "popularity" in result["data"]:
                self.popularity = result["data"]["popularity"]
            if "poster_path" in result["data"]:
                self.poster_path = result["data"]["poster_path"]
            if "release_air_date" in result["data"]:
                self.release_air_date = result["data"]["release_air_date"]
            if "genre_ids" in result["data"]:
                self.genre_ids = self.genreStr2List(result["data"]["genre_ids"])
            if "origin_country" in result["data"]:
                self.origin_country = result["data"]["origin_country"]
            if "original_title" in result["data"]:
                self.original_title = result["data"]["original_title"]
            if "overview" in result["data"]:
                self.overview = result["data"]["overview"]
            if "vote_average" in result["data"]:
                self.vote_average = result["data"]["vote_average"]
            if "production_countries" in result["data"]:
                self.production_countries = result["data"]["production_countries"]


    def getProductionArea(self):
        if self.tmdbcat == 'tv':
            # print(self.tmdbDetails.origin_country)
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
        # if self.tmdbDetails and self.tmdbDetails.production_companies:
        #     r = self.tmdbDetails.production_companies[0].origin_country
        # return r

    # TODO: to be continue
    def checkNameContainsIMDbId(self, torname):
        m = re.search(r'[\[{]]imdb(id)?\=(tt\d+)[\]}]', torname, flags=re.A | re.I)
        if m:
            imdbid = m[2]
            return imdbid
        return ''

    def checkNameContainsTMDbId(self, torname):
        m = re.search(r'[\[{]tmdb(id)?[=-](\d+)[\]}]', torname, flags=re.A | re.I)
        if m:
            tmdbid = tryint(m[2])
            return tmdbid
        return -1

