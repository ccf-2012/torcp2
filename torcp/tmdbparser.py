# -*- coding: utf-8 -*-
import re
import time
# from tmdbv3api import TMDb, Movie, TV, Search, Find
# from imdb import Cinemagoer
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


def query_media_name(json_data, api_url="http://127.0.0.1:5009", torcpdb_apikey=''):
    """
    查询种子名称对应的媒体信息
    
    Args:
        seed_name (str): 需要查询的种子名称
        api_url (str): API基础URL地址
    
    Returns:
        dict: 查询结果
            成功返回示例:
            {
                'success': True,
                'data': {
                    'id': 1,
                    'seed_name': '示例种子名',
                    'media_name': '正确的媒体名称',
                    'category': '电影',
                    'tmdb_id': 12345,
                    'year': 2024,
                    'created_at': '2024-01-01 12:00:00'
                }
            }
            
            失败返回示例:
            {
                'success': False,
                'message': '未找到匹配记录'
            }
    
    Raises:
        requests.RequestException: 当API请求失败时抛出异常
    """
    if torcpdb_apikey:
        headers = {
            'User-Agent': 'python/request:torcp',
            'X-API-Key': torcpdb_apikey
        }    
    try:
        response = requests.post(
            f"{api_url}/api/query", headers=headers,
            json=json_data
        )
        response.raise_for_status()  # 如果响应状态码不是200，抛出异常
        return response.json()
    except requests.RequestException as e:
        print(f"查询失败: {str(e)}")
        raise

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
                s = next((y for y in genre_list if y['id']==x), None)
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

    def parse(self, torname, useTMDb=False, hasIMDbId=None, hasTMDbId=None, exTitle=''):
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
                    if hasTMDbId:
                        cat, tmdbstr = parseTMDbStr(hasTMDbId)
                        if self.ccfcatHard and (not cat):
                            cat = self.tmdbcat
                        if tmdbstr:
                            json_data = {
                                "seed_name": torname,
                                "tmdbid": tmdbstr
                            }
                    elif hasIMDbId:
                        json_data = {
                            "seed_name": torname,
                            "imdbid": hasIMDbId
                        }
                    elif self.tmdbcat in ['tv', 'movie', 'Other', 'HDTV']:
                        json_data = {
                            "seed_name": torname,
                            "extitle": exTitle
                        }
                    result = query_media_name(json_data, self.torcpdb_url, self.torcpdb_apikey)
                    if result['success']:
                        self.saveResult(result)
                        logger.success(f'success: {result["data"]["media_name"]},{result["data"]["tmdb_cat"]}-{result["data"]["tmdb_id"]}')
                        self.ccfcat = transToCCFCat(self.tmdbcat, self.ccfcat)
                    break
                except:
                    attempts += 1
                    logger.warning("TORCPDb connection failed. Trying %d " % attempts)
                    time.sleep(3)



    def saveResult(self, result):
        if "data" in result:
            if "media_name" in result["data"]:
                self.title = result["data"]["media_name"]
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

    # def getIMDbInfo(self, imdb_id):
    #     ia = Cinemagoer()
    #     self.imdbid = imdb_id
    #     try:
    #         movie = ia.get_movie(imdb_id[2:])
    #         self.imdbval = movie.get('rating')
    #         # 检查是否是电视剧
    #         if movie.get('kind') in [ 'episode'] :
    #             self.imdbid = 'tt'+movie.get('episode of').movieID
    #             logger.error(f"提供的ID {imdb_id} 是个 episode, 剧集 为 {self.imdbid}")
    #     except Exception as e:
    #         logger.error(f"获取 IMDb 信息时发生错误: {e}")
    #     return self.imdbid


    # def getDetails(self):
    #     attempts = 0
    #     while attempts < 3:
    #         try:
    #             if self.tmdbid > 0:
    #                 if self.tmdbcat == 'movie':
    #                     movie = Movie()
    #                     self.tmdbDetails = movie.details(self.tmdbid)
    #                 elif self.tmdbcat == 'tv':
    #                     tv = TV()
    #                     self.tmdbDetails = tv.details(self.tmdbid)
    #             break
    #         except:
    #             attempts += 1
    #             logger.info("TMDb connection failed. Trying %d " % attempts)
    #             time.sleep(3)


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

    # def verifyYear(self, resultDate, checkYear, cat):
    #     match = False
    #     resyear = checkYear
    #     m = re.match(r'^(\d+)\b', resultDate)
    #     if m:
    #         resyear = m.group(0)
    #         intyear = int(resyear)
    #         if cat == 'tv':
    #             match = not (self.season == 'S01' and self.year and self.year not in [str(intyear-1), str(intyear), str(intyear+1)])
    #         else:
    #             match = not self.year or (self.year in [str(intyear-1), str(intyear), str(intyear+1)])
    #     if match:
    #         self.year = resyear
    #     return match

    # def saveTmdbTVResultMatch(self, result):
    #     if result:
    #         if hasattr(result, 'name'):
    #             self.title = result.name
    #             # print('name: ' + result.name)
    #         elif hasattr(result, 'original_name'):
    #             self.title = result.original_name
    #             # print('original_name: ' + result.original_name)
    #         self.tmdbid = result.id
    #         self.tmdbcat = 'tv'
    #         if hasattr(result, 'original_language'):
    #             if result.original_language == 'zh':
    #                 self.original_language = 'cn'
    #             else:
    #                 self.original_language = result.original_language
    #         if hasattr(result, 'popularity'):
    #             self.popularity = result.popularity
    #         if hasattr(result, 'poster_path'):
    #             self.poster_path = result.poster_path
    #         if hasattr(result, 'first_air_date'):
    #             self.year = self.getYear(result.first_air_date)
    #             self.release_air_date = result.first_air_date
    #         elif hasattr(result, 'release_date'):
    #             self.year = self.getYear(result.release_date)
    #             self.release_air_date = result.release_date
    #         else:
    #             self.year = 0
    #         if hasattr(result, 'genres'):
    #             self.genre_ids = [x['id'] for x in result.genres]
    #         if hasattr(result, 'genre_ids'):
    #             self.genre_ids = result.genre_ids
    #         logger.info('Found [%d]: %s' % (self.tmdbid, self.title))
    #     else:
    #         logger.info('Not match in tmdb: [%s] ' % (self.title))

    #     return result is not None

    # def saveTmdbMovieResult(self, result):
    #     if hasattr(result, 'title'):
    #         self.title = result.title
    #     elif hasattr(result, 'original_title'):
    #         self.title = result.original_title
    #     # if hasattr(result, 'media_type'):
    #     #     self.ccfcat = transToCCFCat(result.media_type, self.ccfcat)
    #     self.tmdbid = result.id
    #     self.tmdbcat = 'movie'
    #     if hasattr(result, 'original_language'):
    #         if result.original_language == 'zh':
    #             self.original_language = 'cn'
    #         else:
    #             self.original_language = result.original_language
    #     if hasattr(result, 'popularity'):
    #         self.popularity = result.popularity
    #     if hasattr(result, 'poster_path'):
    #         self.poster_path = result.poster_path
    #     if hasattr(result, 'release_date'):
    #         self.year = self.getYear(result.release_date)
    #         self.release_air_date = result.release_date
    #     elif hasattr(result, 'first_air_date'):
    #         self.year = self.getYear(result.first_air_date)
    #         self.release_air_date = result.first_air_date
    #     else:
    #         self.year = 0
    #     if hasattr(result, 'genres'):
    #         self.genre_ids = [x['id'] for x in result.genres]
    #     if hasattr(result, 'genre_ids'):
    #         self.genre_ids = result.genre_ids
        
    #     logger.info('Found [%d]: %s' % (self.tmdbid, self.title))
    #     return True

    # def saveTmdbMultiResult(self, result):
    #     if hasattr(result, 'media_type'):
    #         self.imdbcat = result.media_type
    #         if result.media_type == 'tv':
    #             self.saveTmdbTVResultMatch(result)
    #         elif result.media_type == 'movie':
    #             self.saveTmdbMovieResult(result)
    #         else:
    #             logger.info('Unknow media_type %s ' % result.media_type)
    #     return

    # def imdbMultiQuery(self, title, year=None):
    #     search = Search()
    #     return search.multi({"query": title, "year": year, "page": 1})

    # def sortByPopularity(resultList):
    #     newlist = sorted(resultList, key=lambda x: x.popularity, reverse=True)

    # def getYear(self, datestr):
    #     intyear = 0
    #     m2 = re.search(
    #         r'\b((19\d{2}\b|20\d{2})(-19\d{2}|-20\d{2})?)',
    #         datestr,
    #         flags=re.A | re.I)
    #     if m2:
    #         yearstr = m2.group(2)
    #         intyear = tryint(yearstr)
    #     return intyear

    # def getTitle(self, result):
    #     tt = ''
    #     if hasattr(result, 'name'):
    #         tt = result.name
    #     elif hasattr(result, 'title'):
    #         tt = result.title
    #     elif hasattr(result, 'original_name'):
    #         tt = result.original_name
    #     elif hasattr(result, 'original_title'):
    #         tt = result.original_title
    #     return tt


    # def containsCJK(self, str):
    #     return re.search(r'[\u4e00-\u9fa5]', str)

    # def findYearMatch(self, results, year, strict=True):
    #     matchList = []
    #     for result in results:
    #         if year == 0:
    #             matchList.append(result)
    #             continue

    #         datestr = ''
    #         if hasattr(result, 'first_air_date'):
    #             datestr = result.first_air_date
    #         elif hasattr(result, 'release_date'):
    #             datestr = result.release_date

    #         resyear = self.getYear(datestr)
    #             # return result

    #         if strict:
    #             if resyear == year:
    #                 matchList.append(result)
    #                 continue
    #         else:
    #             if resyear in [year-3, year-2, year-1, year, year+1]:
    #                 self.year = resyear
    #                 matchList.append(result)
    #                 continue

    #     if len(matchList) > 0:
    #         # prefer item with CJK
    #         if self.tmdb.language == 'zh-CN':
    #             for item in matchList[:3]:
    #                 tt = self.getTitle(item)
    #                 if not tt:
    #                     continue
    #                 if self.containsCJK(tt):
    #                     return item
    #         return matchList[0]
    #     return None

    # def selectOrder(self, cntitle, cuttitle, list):
    #     if len(cntitle) < 3 and len(cuttitle)> 5:
    #         list[0], list[1] = list[1], list[0]
    #         return list
    #     else:
    #         return list
    
    # def fixTmdbParam(self, tparam):
    #     if "year" in tparam and len(tparam["year"]) != 4:
    #         del tparam["year"]
    #     return tparam

    # def replaceRomanNum(self, titlestr):
    #     # no I and X
    #     romanNum = [ (r'\bII\b', '2'), (r'\bIII\b', '3'), (r'\bIV\b', '4'), (r'\bV\b', '5'), (r'\bVI\b', '6'), (r'\bVII\b', '7'), (r'\bVIII\b', '8'),
    #                 (r'\bIX\b', '9'), (r'\bXI\b', '11'), (r'\bXII\b', '12'), (r'\bXIII\b', '13'), (r'\bXIV\b', '14'), (r'\bXV\b', '15'), (r'\bXVI\b', '16')]
    #     for s in romanNum:
    #         titlestr = re.sub(s[0], s[1], titlestr, flags=re.A)
    #     return titlestr

    # def searchTMDb(self, title, cat=None, parseYearStr=None, cntitle=None):
    #     searchList = []
    #     if title == cntitle:
    #         cntitle = ''
    #     cuttitle = re.sub(r'^(Jade|\w{2,3}TV)\s+', '', title, flags=re.I)
    #     cuttitle = re.sub(r'\b(Extended|Anthology|Trilogy|Quadrilogy|Tetralogy|Collections?)\s*$', '', title, flags=re.I)
    #     cuttitle = re.sub(r'\b(Extended|HD|S\d+|E\d+|V\d+|4K|DVD|CORRECTED|UnCut|SP)\s*$', '', cuttitle, flags=re.I)
    #     cuttitle = re.sub(r'^\s*(剧集|BBC：?|TLOTR|Jade|Documentary|【[^】]*】)', '', cuttitle, flags=re.I)
    #     cuttitle = re.sub(r'(\d+部曲|全\d+集.*|原盘|系列|\s[^\s]*压制.*)\s*$', '', cuttitle, flags=re.I)
    #     cuttitle = re.sub(r'(\b国粤双语|[\b\(]?\w+版|\b\d+集全).*$', '', cuttitle, flags=re.I)
    #     cuttitle = re.sub(r'(The[\s\.]*(Complete\w*|Drama\w*|Animate\w*)?[\s\.]*Series|The\s*Movie)\s*$', '', cuttitle, flags=re.I)
    #     cuttitle = re.sub(r'\b(Season\s?\d+)\b', '', cuttitle, flags=re.I)
    #     if cntitle:
    #         cntitle = re.sub(r'(\d+部曲|全\d+集.*|原盘|系列|\s[^\s]*压制.*)\s*$', '', cntitle, flags=re.I)
    #         cntitle = re.sub(r'(\b国粤双语|[\b\(]?\w+版|\b\d+集全).*$', '', cntitle, flags=re.I)

    #     cuttitle = self.replaceRomanNum(cuttitle)

    #     m1 = re.search(r'the movie\s*$', cuttitle, flags=re.A | re.I)        
    #     if m1 and m1.span(0)[0] > 0:
    #         cuttitle = cuttitle[:m1.span(0)[0]].strip()
    #         cat = 'movie'

    #     m2 = re.search(
    #         r'\b((19\d{2}\b|20\d{2})(-19\d{2}|-20\d{2})?)\b(?!.*\b\d{4}\b.*)',
    #         cuttitle,
    #         flags=re.A | re.I)
    #     if m2 and m2.span(1)[0] > 0:
    #         cuttitle = cuttitle[:m2.span(1)[0]].strip()
    #         cuttitle2 = cuttitle[m2.span(1)[1]:].strip()

    #     intyear = self.getYear(parseYearStr)

    #     if self.ccfcatHard:
    #         if cat.lower() == 'tv':
    #             searchList = [('tv', cntitle), ('tv', cuttitle)]
    #         elif cat.lower() == 'movie':
    #             searchList = [('movie', cntitle), ('movie', cuttitle)]
    #     else:
    #         if self.season:
    #             searchList = self.selectOrder(cntitle, cuttitle, [('tv', cntitle), ('tv', cuttitle), ('multi', cntitle)])
    #         elif cat.lower() == 'tv':
    #             searchList = self.selectOrder(cntitle, cuttitle, [('multi', cntitle), ('tv', cuttitle), ('multi', cuttitle)])
    #         elif cat.lower() == 'hdtv':
    #             searchList = [('multi', cntitle), ('multi', cuttitle)]
    #         elif cat.lower() == 'movie':
    #             searchList = self.selectOrder(cntitle, cuttitle, [('movie', cntitle), ('multi', cntitle), ('movie', cuttitle), ('multi', cuttitle)])
    #         else:
    #             searchList = [('multi', cntitle), ('multi', cuttitle)]

    #     for s in searchList:
    #         if s[0] == 'tv' and s[1]:
    #             logger.info('Search TV: ' + s[1])
    #             # tv = TV()
    #             # results = tv.search(s[1])
    #             search = Search()

    #             results = search.tv_shows(self.fixTmdbParam({"query": s[1], "year": str(intyear), "page": 1}))
    #             if len(results) > 0:
    #                 if intyear > 0:
    #                     if self.season and 'S01' not in self.season:
    #                         intyear = 0
    #                 result = self.findYearMatch(results, intyear, strict=True)
    #                 if result:
    #                     self.saveTmdbTVResultMatch(result)
    #                     return self.tmdbid, self.title, self.year
    #                 else:
    #                     result = self.findYearMatch(results, intyear, strict=False)
    #                     if result:
    #                         self.saveTmdbTVResultMatch(result)
    #                         return self.tmdbid, self.title, self.year

    #         elif s[0] == 'movie' and s[1]:
    #             logger.info('Search Movie:  %s (%d)' % (s[1], intyear))
    #             search = Search()
    #             if intyear == 0:
    #                 results = search.movies({"query": s[1], "page": 1})
    #             else:
    #                 results = search.movies(self.fixTmdbParam({"query": s[1], "year": str(intyear), "page": 1}))

    #             if len(results) > 0:
    #                 result = self.findYearMatch(results, intyear, strict=True)
    #                 if result:
    #                     self.saveTmdbMovieResult(result)
    #                     return self.tmdbid, self.title, self.year
    #                 else:
    #                     result = self.findYearMatch(results, intyear, strict=False)
    #                     if result:
    #                         self.saveTmdbMovieResult(result)
    #                         return self.tmdbid, self.title, self.year
    #             elif intyear > 0:
    #                 results = search.movies({"query": s[1], "page": 1})
    #                 if len(results) > 0:
    #                     result = self.findYearMatch(results, intyear, strict=False)
    #                     if result:
    #                         self.saveTmdbMovieResult(result)
    #                         return self.tmdbid, self.title, self.year
    #         elif s[0] == 'multi' and s[1]:
    #             logger.info('Search Multi:  %s (%d)' % (s[1], intyear))
    #             search = Search()
    #             if intyear == 0:
    #                 results = search.multi({"query": s[1], "page": 1})
    #             else:
    #                 results = search.multi(self.fixTmdbParam({"query": s[1], "year": str(intyear), "page": 1}))

    #             if len(results) > 0:
    #                 result = self.findYearMatch(results, intyear, strict=True)
    #                 if result:
    #                     self.saveTmdbMultiResult(result)
    #                     return self.tmdbid, self.title, self.year
    #                 else:
    #                     result = self.findYearMatch(results, intyear, strict=False)
    #                     if result:
    #                         self.saveTmdbMultiResult(result)
    #                         return self.tmdbid, self.title, self.year
    #             elif intyear > 0:
    #                 results = search.multi({"query": s[1], "page": 1})
    #                 if len(results) > 0:
    #                     result = self.findYearMatch(results, intyear, strict=True)
    #                     if result:
    #                         self.saveTmdbMultiResult(result)
    #                         return self.tmdbid, self.title, self.year
    #                     else:
    #                         result = self.findYearMatch(results, intyear, strict=False)
    #                         if result:
    #                             self.saveTmdbMultiResult(result)
    #                             return self.tmdbid, self.title, self.year

    #     logger.info('TMDb Not found: [%s] [%s] ' % (title, cntitle))
    #     return 0, title, intyear


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


#     def searchTMDbByIMDbId(self, imdbid):
#         f = Find(self.tmdb)
#         logger.info("Search : " + imdbid)
#         t = f.find_by_imdb_id(imdb_id=imdbid)
#         if t:
#             # print(t)
# # (Pdb) p t.movie_results
# # [{'adult': False, 'backdrop_path': '/rcmjVmKBKONXk2LCe7GOAIHaIAO.jpg', 'id': 1068249, 'title': 'Reborn Rich', 'original_language': 'ko', 'original_title': '재벌집 막내아들', 'overview': '...', 'poster_path': '/xVtekQdaJ00cQqK2oyVJg5P7a6H.jpg', 'media_type': 'movie', 'genre_ids': [18, 14], 'popularity': 1.4, 'release_date': '2022-11-18', 'video': False, 'vote_average': 0.0, 'vote_count': 0}]
# # (Pdb) t.tv_results
# # [{'adult': False, 'backdrop_path': '/jG8mKDxe0LIDFBPB8uCeYGSBWCH.jpg', 'id': 153496, 'name': 'Reborn Rich', 'original_language': 'ko', 'original_name': '재벌집 막내아들', 'overview': '....', 'poster_path': '/ioywelRYOfNJ5w8aNQ5ttJo9dk1.jpg', 'media_type': 'tv', 'genre_ids': [18, 10765], 'popularity': 70.232, 'first_air_date': '2022-11-18', 'vote_average': 8.094, 'vote_count': 32, 'origin_country': ['KR']}]
#             if self.tmdbcat == "tv":
#                 if t.tv_results:
#                     self.tmdbcat = "tv"
#                     r = t['tv_results'][0]
#                     self.saveTmdbTVResultMatch(r)
#                 elif t.movie_results:
#                     self.tmdbcat = "movie"
#                     r = t['movie_results'][0]
#                     self.saveTmdbMovieResult(r)
#                 else:
#                     pass
#             else: 
#                 if t.movie_results:
#                     self.tmdbcat = "movie"
#                     r = t['movie_results'][0]
#                     self.saveTmdbMovieResult(r)
#                 elif t.tv_results:
#                     self.tmdbcat = "tv"
#                     r = t['tv_results'][0]
#                     self.saveTmdbTVResultMatch(r)
#                 else:
#                     pass

#         return self.tmdbid, self.title, self.year


#     def searchTMDbByTMDbIdTv(self, tmdbid):
#         tv = TV(self.tmdb)
#         logger.info("Search tmdbid in TV: " + tmdbid)
#         try:
#             t = tv.details(tmdbid)
#             if t:
#                 self.tmdbDetails = t
#                 self.saveTmdbTVResultMatch(t)
#         except:
#             pass
#         return self.tmdbid, self.title, self.year 

#     def searchTMDbByTMDbIdMovie(self, tmdbid):
#         movie = Movie(self.tmdb)
#         logger.info("Search tmdbid in Movie: " + tmdbid)
#         try:
#             m = movie.details(tmdbid)
#             if m:
#                 self.tmdbDetails = m
#                 self.saveTmdbMovieResult(m)
#         except:
#             pass
#         return self.tmdbid, self.title, self.year

#     def searchTMDbByTMDbId(self, cat, tmdbid):
#         if cat == 'tv':
#             return self.searchTMDbByTMDbIdTv(tmdbid)
#         elif cat == 'movie':
#             return self.searchTMDbByTMDbIdMovie(tmdbid)
#         else:
#             self.searchTMDbByTMDbIdTv(tmdbid)
#             if self.tmdbid <= 0:
#                 return self.searchTMDbByTMDbIdMovie(tmdbid)

#         return self.tmdbid, self.title, self.year
