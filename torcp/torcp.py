# -*- coding: utf-8 -*-
"""A script hardlink media files and directories in Emby-happy naming and structs."""
import re
import os
import time
import datetime
import argparse
import shutil
import glob
import platform
import codecs
import logging
import xml.etree.ElementTree as ET

from .tmdbparser import TMDbNameParser
from .torcategory import TorCategory
from tortitle import TorTitle

VIDEO_EXTS = ['.mkv', '.mp4', '.ts', '.m2ts', '.mov', '.strm']
from loguru import logger


def area5dir(area_code):
    AREA5_DICT = {
        '欧美' : ['GB', 'FR', 'DE', 'IT', 'RU', 'DK', 'NO', 'IS', 'SE', 'FI', 'IE', 'ES', 'PT', 'NL', 'BE', 'AT', 
            'CH', 'UA', 'BY', 'PL', 'CZ', 'GR', 'TR', 'BG', 'RO', 'LT', 'HU', 'LU', 'MC', 'LI', 'EE', 'LV', 
            'HR', 'RS', 'SK', 'MD', 'SI', 'AL', 'MK', 'AZ', 'GE', 'ME', 'BA', 'CA', 'US', 'MX', 'GT', 'BZ', 
            'SV', 'HN', 'NI', 'CR', 'PA', 'BS', 'CU', 'JM', 'HT', 'DO', 'KN', 'AG', 'DM', 'LC', 'VC', 'BB', 
            'GD', 'TT', 'CO', 'EC', 'VE', 'GF', 'SR', 'PE', 'BO', 'PY', 'BR', 'CL', 'AR', 'UY'],
        '日本' : ['JP', 'JA'],
        '韩国' : ['KR', 'KO'],
        '大陆' : ['CN', 'ZH', '大陆', '中国'],
        '港台': ['HK', 'TW', '香港', '台湾']
        }
    return next((x for x, k in AREA5_DICT.items() if area_code in AREA5_DICT[x]), 'other')

def area7dir(area_code):
    AREA7_DICT = {
        '美国' : ['US'],
        '西方' : ['GB', 'FR', 'DE', 'IT', 'RU', 'DK', 'NO', 'IS', 'SE', 'FI', 'IE', 'ES', 'PT', 'NL', 'BE', 'AT', 
            'CH', 'UA', 'BY', 'PL', 'CZ', 'GR', 'TR', 'BG', 'RO', 'LT', 'HU', 'LU', 'MC', 'LI', 'EE', 'LV', 
            'HR', 'RS', 'SK', 'MD', 'SI', 'AL', 'MK', 'AZ', 'GE', 'ME', 'BA', 'CA', 'MX', 'GT', 'BZ', 
            'SV', 'HN', 'NI', 'CR', 'PA', 'BS', 'CU', 'JM', 'HT', 'DO', 'KN', 'AG', 'DM', 'LC', 'VC', 'BB', 
            'GD', 'TT', 'CO', 'EC', 'VE', 'GF', 'SR', 'PE', 'BO', 'PY', 'BR', 'CL', 'AR', 'UY'],
        '日本' : ['JP', 'JA'],
        '韩国' : ['KR', 'KO'],
        '大陆' : ['CN', 'ZH', '大陆', '中国'],
        '香港' : ['HK', '香港'],
        '台湾' : ['TW', '台湾']
        }
    return next((x for x, k in AREA7_DICT.items() if area_code in AREA7_DICT[x]), 'other')

def chinese_to_number(chinese_str):
    chinese_numbers = {
        '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
        '六': 6, '七': 7, '八': 8, '九': 9
    }
    return ''.join([str(chinese_numbers[char]) for char in chinese_str if char in chinese_numbers])


def is_0day_name(item_string):
    # CoComelon.S03.1080p.NF.WEB-DL.DDP2.0.H.264-NPMS
    m = re.match(r'^\w+.*\b(BluRay|Blu-?ray|720p|1080[pi]|[xh].?26\d|2160p|576i|WEB-DL|DVD|WEBRip|HDTV)\b.*', item_string, flags=re.A | re.I)
    return m

class Config:
    """Handles argument parsing and configuration for the script."""
    def __init__(self, argv=None):
        self.argv = argv
        self.args = None
        self.keep_exts = list(VIDEO_EXTS)
        self.keep_ext_all = False
        self.load_args()

    def load_args(self):
        parser = argparse.ArgumentParser(
            description='torcp: a script hardlink media files and directories in Emby-happy naming and structs.'
        )
        parser.add_argument(
            'MEDIA_DIR',
            help='The directory contains TVs and Movies to be copied.')
        parser.add_argument('-d', '--hd_path', required=True, help='the dest path to create Hard Link.')
        parser.add_argument('-e', '--keep-ext', help="keep files with these extention('srt,ass').")
        parser.add_argument('-l', '--lang', help="seperate dir by language('cn,en').")
        parser.add_argument('--genre', help="seperate dir by genre('anime,document').")
        parser.add_argument('--other-dir', help='for any dir Other than Movie/TV.')
        parser.add_argument('--sep-area', action='store_true', help='seperate dir by all production area.')
        parser.add_argument('--sep-area5', action='store_true', help='seperate 5 dirs(cn,hktw,jp,kr,useu,other) by production area.')
        parser.add_argument('--sep-area7', action='store_true', help='seperate 7 dirs(us,cn,hk,tw,jp,kr,occident,other) by production area.')
        parser.add_argument(
            '--torcpdb-url',
            help='Search torcpdb API for the tmdb id'
        )
        parser.add_argument('--torcpdb-apikey', help='apikey for torcpdb API')
        parser.add_argument('--tv-folder-name', default='TV', help='specify the name of TV directory, default TV.')
        parser.add_argument('--movie-folder-name', default='Movie', help='specify the name of Movie directory, default Movie.')
        parser.add_argument('--tv', action='store_true', help='specify the src directory is TV.')
        parser.add_argument('--movie', action='store_true', help='specify the src directory is Movie.')
        parser.add_argument('--dryrun', action='store_true', help='print message instead of real copy.')
        parser.add_argument('--single', '-s', action='store_true', help='parse and copy one single folder.')
        parser.add_argument('--extract-bdmv', action='store_true', help='extract largest file in BDMV dir.')
        parser.add_argument('--full-bdmv', action='store_true', help='copy full BDMV dir and iso files.')
        parser.add_argument('--origin-name', action='store_true', help='keep origin file name.')
        parser.add_argument('--tmdb-origin-name', action='store_true', help='filename emby bracket - origin file name.')
        parser.add_argument('--sleep', type=int, help='sleep x seconds after operation.')
        parser.add_argument('--move-run', action='store_true', help='WARN: REAL MOVE...with NO REGRET.')
        parser.add_argument('--make-log', action='store_true', help='Make a log file.')
        parser.add_argument('--symbolink', action='store_true', help='symbolink instead of hard link')
        parser.add_argument('--cache', action='store_true', help='cache searched dir entries')
        parser.add_argument('--emby-bracket', action='store_true', help='ex: Alone (2020) [tmdbid=509635]')
        parser.add_argument('--plex-bracket', action='store_true', help='ex: Alone (2020) {tmdb-509635}')
        parser.add_argument('--make-plex-match', action='store_true', help='Create a .plexmatch file at the top level of a series')
        parser.add_argument('--make-nfo', action='store_true', help='Create a .nfo file in the media dir')
        parser.add_argument('--after-copy-script', default='', help='call this script with destination folder path after link/move')
        parser.add_argument('--imdbid', default='', help='specify the IMDb id, -s single mode only')
        parser.add_argument('--tmdbid', default='', help='specify the TMDb id, -s single mode only')
        parser.add_argument('--extitle', default='', help='specify the extra title to search')
        parser.add_argument('--site-str', help="site-id(ex. hds-12345) folder name, set site strs like ('chd,hds,ade,ttg').")
        parser.add_argument('--add-year-dir', action='store_true', help='Add a year dir above the media folder')
        parser.add_argument('--genre-with-area', default='', help='specify genres with area subdir, seperated with comma')
        parser.add_argument('-pr', '--title-regex', default='', help='the regex to match the title from path')

        self.args = parser.parse_args(self.argv)
        self._make_keep_exts()
        self._ensure_imdb()
        self.args.MEDIA_DIR = os.path.expanduser(self.args.MEDIA_DIR)
        self.args.hd_path = os.path.expanduser(self.args.hd_path)
        if self.args.other_dir:
            self.args.other_dir = os.path.expanduser(self.args.other_dir)

    def _make_keep_exts(self):
        if self.args.keep_ext == 'all':
            self.keep_ext_all = True
            return
        if self.args.keep_ext:
            arg_exts = self.args.keep_ext.split(',')
            for ext in arg_exts:
                ext = ext.strip()
                if ext:
                    self.keep_exts.append(f".{ext.lstrip('.')}")

    def _ensure_imdb(self):
        if self.args.imdbid:
            m1 = re.search(r'(tt\d+)', self.args.imdbid, re.A)
            self.args.imdbid = m1[1] if m1 else ''

class FileSystemManager:
    """Handles all file system operations."""
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)

    def ensure_dir(self, file_path):
        if os.path.isfile(file_path):
            file_path = os.path.dirname(file_path)
        if not self.config.args.dryrun and not os.path.exists(file_path):
            os.makedirs(file_path)

    def make_logfile(self, from_loc, dest_dir, log_dir=None):
        if not self.config.args.make_log:
            return
        if not log_dir:
            from_loc_dir = from_loc
            if os.path.isfile(from_loc):
                from_loc_dir = os.path.dirname(from_loc)
                if re.search(r'\bS\d+$', from_loc_dir):
                    from_loc_dir = os.path.dirname(from_loc_dir)
            origin_name, _ = os.path.splitext(os.path.basename(from_loc_dir))
        else:
            origin_name = os.path.basename(log_dir)
        if not origin_name:
            origin_name = '_'
        log_filename = os.path.join(dest_dir, origin_name + '.log')
        
        if not self.config.args.dryrun:
            self.ensure_dir(dest_dir)
            try:
                with codecs.open(log_filename, "a+", "utf-8") as logfile:
                    logfile.write(from_loc + '\n')
            except Exception:
                self.logger.warning("Error occurred when writing log file")

    def get_dest_dir(self, to_loc_path, cat_tv, cat_movie):
        if self.config.args.other_dir and not to_loc_path.startswith(cat_tv) and not to_loc_path.startswith(cat_movie):
            return os.path.join(self.config.args.other_dir, to_loc_path)
        return os.path.join(self.config.args.hd_path, to_loc_path)

    def _execute_op(self, func, from_loc, to_loc, is_dir=False):
        if os.path.islink(from_loc):
            self.logger.info(f'SKIP symbolic link: [{from_loc}]')
            return

        if not os.path.exists(to_loc):
            if self.config.args.dryrun:
                self.logger.info(f'{func.__name__}: {from_loc} ==> {to_loc}')
            else:
                self.logger.info(f'{func.__name__}: {from_loc} ==> {to_loc}')
                if is_dir and func == shutil.copytree:
                     func(from_loc, to_loc, copy_function=os.link)
                else:
                    func(from_loc, to_loc)
        else:
            self.logger.info(f'Target Exists: [{to_loc}]')

    def target_copy(self, from_loc, to_loc_path, to_loc_file=''):
        dest_dir = self.get_dest_dir(to_loc_path, 'TV', 'Movie')
        self.ensure_dir(dest_dir)
        self.make_logfile(from_loc, dest_dir)

        op = os.link
        if self.config.args.move_run:
            op = shutil.move
        elif self.config.args.symbolink:
            op = os.symlink

        if os.path.isfile(from_loc):
            dest_file = os.path.join(dest_dir, to_loc_file or os.path.basename(from_loc))
            self._execute_op(op, from_loc, dest_file)
        elif os.path.isdir(from_loc):
            dest_dir_full = os.path.join(dest_dir, os.path.basename(from_loc))
            if self.config.args.move_run:
                 self._execute_op(op, from_loc, dest_dir_full)
            else:
                self._execute_op(shutil.copytree if op != os.symlink else os.symlink, from_loc, dest_dir_full, is_dir=True)
        else:
            self.logger.warning(f'File/Dir {from_loc} not found')

class MediaReNameProcessor:
    """Processes media files and directories."""
    def __init__(self, config, fs_manager, export_obj=None):
        self.config = config
        self.args = config.args
        self.fs_manager = fs_manager
        self.export_obj = export_obj
        self.logger = logging.getLogger(__name__)
        self.CAT_NAME_TV = 'TV'
        self.CAT_NAME_MOVIE = 'Movie'
        self.cur_media_name = ''

    def main(self, export_object=None):
        self.export_obj = export_object
        self.process_media()

    def process_media(self):
        cp_location = os.path.abspath(self.args.MEDIA_DIR)
        self.logger.info("=========>>> " + datetime.datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S %z"))

        # search_cache = CacheManager(cp_location) if self.args.cache else None
        # if search_cache: search_cache.openCache()

        arg_imdb_id = self.args.imdbid if self.args.single else ''
        arg_tmdb_id = self.args.tmdbid if self.args.single else ''

        if os.path.isfile(cp_location):
            self.process_one_dir_item(os.path.dirname(cp_location), os.path.basename(cp_location), arg_imdb_id, arg_tmdb_id)
        else:
            if self.args.single and not self.is_collections(cp_location):
                parent_location, item_name, folder_imdb_id, folder_tmdb_id = self.parse_folder_imdb_id(os.path.dirname(cp_location), os.path.basename(cp_location))
                if arg_imdb_id or arg_tmdb_id:
                    self.process_one_dir_item(parent_location, item_name, imdbidstr=arg_imdb_id, tmdbidstr=arg_tmdb_id)
                elif folder_imdb_id or folder_tmdb_id:
                    self.process_with_same_imdb(parent_location, folder_imdb_id, folder_tmdb_id)
                else:
                    self.process_one_dir_item(parent_location, item_name, imdbidstr=folder_imdb_id, tmdbidstr=folder_tmdb_id)
            else:
                for item in os.listdir(cp_location):
                    if self.useless_file(item):
                        continue
                    
                    parent_location, item_name, folder_imdb_id, folder_tmdb_id = self.parse_folder_imdb_id(cp_location, item)

                    if self.is_collections(item_name) and os.path.isdir(os.path.join(parent_location, item_name)):
                        self.logger.info(f'Process collections: {item_name}')
                        pack_dir = os.path.join(parent_location, item_name)
                        for fn in os.listdir(pack_dir):
                            # if search_cache and search_cache.is_cached(fn):
                            #     self.logger.info(f'Skipping. File previously linked: {fn}')
                            #     continue
                            self.process_one_dir_item(pack_dir, fn, imdbidstr='')
                            # if search_cache: search_cache.append(fn)
                    else:
                        # if search_cache and search_cache.is_cached(item_name):
                        #     self.logger.info(f'Skipping. File previously linked: {item_name}')
                        #     continue
                        if (folder_imdb_id or folder_tmdb_id) and (parent_location != cp_location):
                            self.process_with_same_imdb(parent_location, folder_imdb_id, folder_tmdb_id)
                        else:
                            self.process_one_dir_item(parent_location, item_name, imdbidstr=folder_imdb_id, tmdbidstr=folder_tmdb_id)
                        # if search_cache: search_cache.append(item_name)

        # if search_cache: search_cache.close_cache()

    def process_one_dir_item(self, cp_location, item_name, imdbidstr='', tmdbidstr=''):
        self.cur_media_name = item_name
        media_src = os.path.join(cp_location, item_name)
        if os.path.islink(media_src):
            self.logger.info(f'SKIP symbolic link: [{media_src}]')
            return

        title_for_parsing = item_name
        if self.args.title_regex:
            match = re.search(self.args.title_regex, item_name)
            if match:
                if match.groups():
                    title_for_parsing = match.group(1)
                else:
                    title_for_parsing = match.group(0)
                self.logger.info(f"Extracted title '{title_for_parsing}' using regex: {self.args.title_regex}")

        cat = self.set_args_category()

        tmdbid_val = None
        tmdbcat_val = None
        if tmdbidstr:
            if '-' in tmdbidstr:
                parts = tmdbidstr.split('-', 1)
                tmdbcat_val = parts[0]
                tmdbid_val = parts[1]
                if tmdbcat_val == 'm':
                    tmdbcat_val = 'movie'
            else:
                tmdbid_val = tmdbidstr

        # self.logger.info(f">> title_for_parsing: {title_for_parsing}")
        p = TMDbNameParser(self.args.torcpdb_url, self.args.torcpdb_apikey)
        p.parse(title_for_parsing, by_tordb=(self.args.torcpdb_url is not None), imdbid=imdbidstr, tmdbid=tmdbid_val, tmdbcat=tmdbcat_val, extitle=self.args.extitle)
        p.title = self._fix_nt_name(p.title)
        cat = self.gen_cat_folder_name(p)

        dest_folder_name = self.gen_media_folder_name(p)
        dest_cat_folder_name = os.path.join(cat, dest_folder_name)

        if os.path.isfile(media_src):
            filename, file_ext = os.path.splitext(item_name)
            if self.is_media_file_type(file_ext):
                if cat == self.CAT_NAME_TV:
                    self.logger.info(f'Single Episode file?  {media_src}')
                    new_tv_file_name = self.gen_tv_season_epison_group(item_name, p.group, p.resolution) if not self.args.origin_name else item_name
                    season_folder = self.rename_s0d(p.season)
                    season_folder_full_path = os.path.join(self.args.tv_folder_name, dest_folder_name, season_folder)
                    self.fs_manager.target_copy(media_src, season_folder_full_path, new_tv_file_name)
                    self.mk_plex_match(os.path.join(self.args.tv_folder_name, dest_folder_name), p)
                    self.mk_media_nfo(os.path.join(self.args.tv_folder_name, dest_folder_name), "", p)
                    self.target_dir_hook(os.path.join(self.args.tv_folder_name, dest_folder_name), tmdbidstr=str(p.tmdbid), tmdbcat=p.tmdbcat, tmdbtitle=p.title, tmdbobj=p)
                elif cat == self.CAT_NAME_MOVIE:
                    year_str = str(p.year) if p.year > 0 else ''
                    if self.args.origin_name:
                        new_movie_name = self.gen_movie_origin_name(media_src, p.title, year_str, name_parser=p)
                    elif self.args.tmdb_origin_name:
                        new_movie_name = self.gen_movie_tmdb_origin_name(media_src, p.title, year_str, name_parser=p)
                    else:
                        new_movie_name = self.gen_movie_res_group(media_src, p.title, year_str, p.resolution, p.group, name_parser=p)
                    self.fs_manager.target_copy(media_src, dest_cat_folder_name, new_movie_name)
                    self.mk_media_nfo(dest_cat_folder_name, new_movie_name, p)
                    self.target_dir_hook(dest_cat_folder_name, tmdbidstr=str(p.tmdbid), tmdbcat=p.tmdbcat, tmdbtitle=p.title, tmdbobj=p)
                elif cat == 'TMDbNotFound':
                    self.fs_manager.target_copy(media_src, cat)
                    self.target_dir_hook(os.path.join(cat, item_name), tmdbidstr=str(p.tmdbid), tmdbcat=p.tmdbcat, tmdbtitle=p.title, tmdbobj=p)
                else:
                    self.logger.info(f'Single media file : [ {cat} ] {media_src}')
                    self.fs_manager.target_copy(media_src, dest_cat_folder_name)
                    self.target_dir_hook(dest_cat_folder_name, tmdbidstr=str(p.tmdbid), tmdbcat=p.tmdbcat, tmdbtitle=p.title, tmdbobj=p)
            elif file_ext.lower() in ['.iso']:
                if self.args.full_bdmv or self.args.extract_bdmv:
                    bdmv_folder = os.path.join('BDMVISO', dest_folder_name)
                    self.fs_manager.target_copy(media_src, bdmv_folder)
                    self.target_dir_hook(bdmv_folder, tmdbidstr='', tmdbcat='iso', tmdbtitle=item_name, tmdbobj=None)
                else:
                    self.logger.info(f'Skip .iso file:  {media_src}')
            else:
                self.logger.info(f'Skip file:  {media_src}')
        else:
            if cat == self.CAT_NAME_TV:
                self.copy_tv_folder_items(media_src, dest_folder_name, p.season, p.group, p.resolution, p)
            elif cat == self.CAT_NAME_MOVIE:
                self.process_movie_dir(media_src, p.tmdbcat, dest_folder_name, folder_tmdb_parser=p)
            elif cat in ['MV']:
                self.fs_manager.target_copy(media_src, cat)
                self.target_dir_hook(os.path.join(cat, item_name), tmdbidstr='', tmdbcat='mv', tmdbtitle=item_name, tmdbobj=None)
            elif cat in ['Music']:
                self.process_music(media_src, cat, dest_folder_name)
            elif cat in ['TMDbNotFound']:
                if p.tmdbcat == 'movie':
                    self.logger.info(f'Search media in dir: [ {cat} ], {media_src}')
                    self.process_movie_dir(media_src, cat, dest_folder_name, folder_tmdb_parser=p)
                else:
                    self.fs_manager.target_copy(media_src, cat)
                    self.target_dir_hook(os.path.join(cat, item_name), tmdbidstr='', tmdbcat='notfound', tmdbtitle=p.title, tmdbobj=None)
            elif cat in ['Audio']:
                self.fs_manager.target_copy(media_src, cat)
                self.target_dir_hook(os.path.join(cat, item_name), tmdbidstr='', tmdbcat='audio', tmdbtitle=item_name, tmdbobj=None)
            elif cat in ['eBook']:
                self.logger.info(f'Skip eBoook: [{cat}], {media_src}')
            else:
                self.logger.info(f'Dir treat as movie folder: [ {cat} ], {media_src}')
                self.process_movie_dir(media_src, cat, dest_folder_name, folder_tmdb_parser=p)

    def process_with_same_imdb(self, parent_folder, folder_imdb_id, folder_tmdb_id):
        for item in os.listdir(parent_folder):
            self.process_one_dir_item(parent_folder, item, imdbidstr=folder_imdb_id, tmdbidstr=folder_tmdb_id)

    def parse_folder_imdb_id(self, loc_in, item_in):
        site_id, inside_site_folder_name = self._under_site_id_folder(loc_in, item_in)
        folder_imdb_id, inside_imdb_folder_name = self._under_imdb_folder(loc_in, item_in)
        folder_tmdb_id, inside_tmdb_folder_name = self._under_tmdb_folder(loc_in, item_in)
        if folder_imdb_id:
            return os.path.join(loc_in, item_in), inside_imdb_folder_name, folder_imdb_id, folder_tmdb_id
        if folder_tmdb_id:
            return os.path.join(loc_in, item_in), inside_tmdb_folder_name, folder_imdb_id, folder_tmdb_id
        if site_id:
            return os.path.join(loc_in, item_in), inside_site_folder_name, folder_imdb_id, folder_tmdb_id
        return loc_in, item_in, folder_imdb_id, folder_tmdb_id

    def _under_site_id_folder(self, cp_location, folder_name):
        site_id = self._match_site_id(folder_name)
        if site_id:
            dir_list = os.listdir(os.path.join(cp_location, folder_name))
            if len(dir_list) >= 1:
                return site_id, dir_list[0]
        return '', ''

    def _under_imdb_folder(self, cp_location, folder_name):
        imdb_str = self._has_imdb_id(folder_name)
        if imdb_str:
            dir_list = os.listdir(os.path.join(cp_location, folder_name))
            if len(dir_list) >= 1:
                return imdb_str, dir_list[0]
        return '', ''

    def _under_tmdb_folder(self, cp_location, folder_name):
        tmdb_str = self._has_tmdb_id(folder_name)
        if tmdb_str:
            dir_list = os.listdir(os.path.join(cp_location, folder_name))
            if len(dir_list) >= 1:
                return tmdb_str, dir_list[0]
        return '', ''

    def _has_tmdb_id(self, str_):
        m1 = re.search(r'tmdb(id)?[=-]((m|tv)?-?(\d+))', str_.strip(), re.A | re.I)
        #TODO：  m1[2] or m1[4]
        return m1[2] if m1 else None

    def _has_imdb_id(self, str_):
        m1 = re.search(r'imdb(id)?\=(tt\d+)', str_.strip(), re.A | re.I)
        m2 = re.search(r'(tt\d+)\s*$', str_, re.A | re.I)
        if m1: return m1[2]
        if m2: return m2[1]
        return None

    def _match_site_id(self, str_):
        site_str = self.args.site_str.replace(',', '|') if self.args.site_str else 'chd|hds|ourbits|hdc|ttg|ade|cmct|frds|pter|u2|mteam|hdh|lemon'
        m1 = re.search(r'\(' + site_str + r'\)\-(\d+)$', str_.strip(), re.A | re.I)
        return m1[1] if m1 else None

    def is_collections(self, folder_name):
        return re.search(r'(\bPack$|合集|Anthology|Trilogy|Quadrilogy|Tetralogy|(?<!Criterion[ .])Collections?|国语配音4K动画电影$)', folder_name, flags=re.I)

    def useless_file(self, entry_name):
        return entry_name in ['@eaDir', '.DS_Store', '.@__thumb']

    def get_season_from_foldername(self, folderName, failDir=''):
        m1 = re.search(r'(\bS\d+(-S\d+)?|第(\d+)季)', folderName, flags=re.A | re.I)
        if m1:
            if m1.group(3):
                return 'S' + m1.group(3)
            else:
                return m1.group(1)
        elif m2 := re.search(r'第(\w+)季', folderName,  re.I):
            sstr = chinese_to_number(m2.group(1))
            return 'S'+sstr.zfill(2)
        else:
            return folderName


    def _fix_nt_name(self, file_path):
        if platform.system() == 'Windows':
            return re.sub(r'[:?<>*\/\"]', ' ', file_path)
        return re.sub(r'/', ' ', file_path)

    def gen_media_folder_name(self, name_parser):
        if name_parser.tmdbid > 0:
            if self.config.args.emby_bracket:
                tmdb_tail = '[tmdbid=' + str(name_parser.tmdbid) + ']'
            elif self.config.args.plex_bracket:
                tmdb_tail = '{tmdb-' + str(name_parser.tmdbid) + '}'
            else:
                tmdb_tail = ''

            media_folder_name = name_parser.title
            if self.config.args.add_year_dir:
                year_dir_name = str(name_parser.year) if name_parser.year > 0 else 'none'
                media_folder_name = os.path.join(year_dir_name, name_parser.title)

            subdir_title = media_folder_name
            area_dir = ''
            if self.config.args.lang:
                if self.config.args.lang.lower() == 'all':
                    area_dir = name_parser.original_language
                else:
                    ollist = [x.strip() for x in self.config.args.lang.lower().split(',')]
                    area_dir = name_parser.original_language if name_parser.original_language in ollist else 'other'
            elif self.config.args.sep_area:
                area_dir = name_parser.get_production_area()
            elif self.config.args.sep_area5:
                area_dir = area5dir(name_parser.get_production_area().upper())
            elif self.config.args.sep_area7:
                area_dir = area7dir(name_parser.get_production_area().upper())

            genre_dir = area_dir
            if self.config.args.genre:
                arg_genre_list = [x.strip() for x in self.config.args.genre.lower().split(',')]
                media_genre_list = [d.lower().strip() for d in name_parser.get_genres_list()]
                match_genre = next((g for g in arg_genre_list if g in media_genre_list), '')
                if match_genre:
                    genre_dir = match_genre
                match_genre_with_area = ''
                if self.config.args.genre_with_area:
                    arg_genre_with_area_list = [x.strip() for x in self.config.args.genre_with_area.lower().split(',')]
                    match_genre_with_area = next((g for g in arg_genre_with_area_list if g in media_genre_list), '')
                    if match_genre_with_area:
                        genre_dir = os.path.join(match_genre_with_area, area_dir)
                genre_dir = genre_dir if genre_dir else 'genres'
            subdir_title = os.path.join(genre_dir, media_folder_name)
                
            if name_parser.year > 0:
                media_folder_name = '%s (%d) %s' % (
                    subdir_title, name_parser.year, tmdb_tail)
            else:
                media_folder_name = '%s %s' % (subdir_title, tmdb_tail)

        else:
            if name_parser.tmdbcat == 'tv':
                if name_parser.year > 0 and name_parser.season == 'S01':
                    media_folder_name = '%s (%d)' % (name_parser.title, name_parser.year)
                else:
                    media_folder_name = name_parser.title
            else:
                if name_parser.year > 0:
                    media_folder_name = '%s (%d)' % (name_parser.title, name_parser.year)
                else:
                    media_folder_name = name_parser.title
                
        return media_folder_name.strip()

    def is_media_file_type(self, file_ext):
        return self.config.keep_ext_all or file_ext.lower() in self.config.keep_exts

    def rename_s0d(self, season_folder_name):
        match = re.match(r'^S(\d+)$', season_folder_name)
        if match:
            return f"Season {match.group(1)}"
        else:
            return season_folder_name

    def copy_tv_season_items(self, tv_source_full_path, tv_folder, season_folder, group_name, resolution, folder_tmdb_parser=None):
        if os.path.isdir(os.path.join(tv_source_full_path, 'BDMV')):
            bdmv_tv_folder = os.path.join(tv_folder, season_folder)
            self.process_bdmv(tv_source_full_path, bdmv_tv_folder, self.CAT_NAME_TV, tmdb_parser=folder_tmdb_parser)
            return

        for tv2_item in os.listdir(tv_source_full_path):
            tv2_item_path = os.path.join(tv_source_full_path, tv2_item)
            if os.path.isdir(tv2_item_path):
                logger.info('\033[31mSKIP dir in TV: [%s]\033[0m ' % tv2_item_path)
            else:
                filename, file_ext = os.path.splitext(tv2_item)
                season_folder_full_path = os.path.join(self.CAT_NAME_TV, tv_folder, season_folder)
                if self.is_media_file_type(file_ext):
                    if self.args.origin_name:
                        new_tv_file_name = os.path.basename(tv2_item)
                    else:
                        if not group_name:
                            tc = TorCategory(tv2_item)
                            cat, group_name = tc.ccfcat, tc.group
                            if not resolution:
                                resolution = tc.resolution
                        new_tv_file_name = self.gen_tv_season_epison_group(
                            tv2_item, group_name, resolution)
                    self.fs_manager.target_copy(tv2_item_path, season_folder_full_path, new_tv_file_name)
                elif file_ext.lower() in ['.iso']:
                    if self.args.full_bdmv or self.args.extract_bdmv:
                        self.fs_manager.target_copy(tv2_item_path, season_folder_full_path)

    def self_gen_category_dir(self, dir_name):
        return dir_name in [
            'MovieEncode', 'MovieRemux', 'MovieWebdl', 'MovieBDMV', 'BDMVISO',
            self.CAT_NAME_MOVIE, self.CAT_NAME_TV, 'TMDbNotFound'
        ]

    def gen_tv_season_epison_group(self, media_filename, group_name, resolution):
        tt = TorTitle(media_filename)
        tv_title, tv_year, tv_season, tv_episode, cn_title = tt.title, tt.year, tt.season, tt.episode, tt.cntitle
        cut_name = self.cut_origin_name(media_filename)

        tv_episode = re.sub(r'^Ep\s*', 'E', tv_episode, flags=re.I)
        tv_name = '%s %s %s%s %s - %s' % (tv_title,
                                        ('(' + tv_year + ')') if tv_year else '',
                                        tv_season.upper() if tv_season else '',
                                        tv_episode.upper() if tv_episode else '',
                                        (tt.sub_episode+' ') if tt.sub_episode else '',
                                        cut_name)

        return tv_name.strip()

    def count_media_file(self, file_path):
        types = tuple(f"*{ext}" for ext in VIDEO_EXTS if ext not in ['.strm'])
        cur_dir = os.getcwd()
        media_count = 0
        try:
            os.chdir(file_path)
            for files in types:
                media_count += len(glob.glob(files))
            os.chdir(cur_dir)
        except:
            pass
        return media_count
    
    def get_media_files(self, file_path, types=None):
        if types is None:
            types = tuple(f"*{ext}" for ext in VIDEO_EXTS)
        files_found = []
        cur_dir = os.getcwd()
        try:
            os.chdir(file_path)
            for files in types:
                files_found.extend(glob.glob(files))
            os.chdir(cur_dir)
        except:
            pass
        return files_found

    def get_first_media_file(self, file_path):
        media_files = self.get_media_files(file_path)
        return os.path.basename(media_files[0]) if media_files else None

    def get_music_file(self, file_path):
        types = ('*.flac', '*.ape', '*.wav')
        files_grabbed = []
        cur_dir = os.getcwd()
        try:
            os.chdir(file_path)
            for files in types:
                files_grabbed.extend(glob.glob(files))
            os.chdir(cur_dir)
        except:
            pass
        if files_grabbed:
            return os.path.basename(files_grabbed[0])
        else:
            return None

    def fix_season_group_with_filename(self, folder_path, folder_season, folder_group, folder_resolution, dest_folder_name):
        season = folder_season
        group = folder_group
        resolution = folder_resolution
        folder_name = dest_folder_name
        test_file = self.get_first_media_file(folder_path)
        if test_file:
            p = TMDbNameParser(self.config.args.torcpdb_url, self.config.args.torcpdb_apikey)
            p.parse(test_file, by_tordb=False)
            if not folder_group:
                group = p.group
            if not folder_season:
                season = p.season
            if not season:
                season = 'S01'
        return season, group, folder_name, resolution

    def copy_tv_folder_items(self, tv_source_folder, gen_folder, folder_season, group_name, resolution, folder_tmdb_parser):
        if os.path.islink(tv_source_folder):
            logger.info('SKIP symbolic link: [%s] ' % tv_source_folder)
            return
        if os.path.isdir(os.path.join(tv_source_folder, 'BDMV')):
            if self.config.args.full_bdmv or self.config.args.extract_bdmv:
                self.process_bdmv(tv_source_folder, gen_folder, 'MovieM2TS', tmdb_parser=folder_tmdb_parser)
                self.target_dir_hook(os.path.join('MovieM2TS', gen_folder), tmdbidstr=str(folder_tmdb_parser.tmdbid), tmdbcat=folder_tmdb_parser.tmdbcat, tmdbtitle=folder_tmdb_parser.title, tmdbobj=folder_tmdb_parser)
            else:
                logger.info('Skip BDMV/ISO  %s ' % gen_folder)
            return

        parse_season, parse_group, gen_folder, resolution = self.fix_season_group_with_filename(
            tv_source_folder, folder_season, group_name, resolution, gen_folder)
        parse_season = self.rename_s0d(parse_season)                       

        if not os.path.isdir(tv_source_folder):
            return

        for tv_item in sorted(os.listdir(tv_source_folder)):
            if self.useless_file(tv_item):
                logger.info('SKIP useless file: [%s] ' % tv_item)
                continue
            if self.self_gen_category_dir(tv_item):
                logger.info('SKIP self-generated dir: [%s] ' % tv_item)
                continue

            tv_item_path = os.path.join(tv_source_folder, tv_item)
            if os.path.isdir(tv_item_path):
                season_folder = self.get_season_from_foldername(tv_item, failDir=parse_season)
                season_folder = self.rename_s0d(season_folder)                       
                self.copy_tv_season_items(tv_item_path, gen_folder, season_folder, parse_group,
                                resolution, folder_tmdb_parser=folder_tmdb_parser)
            else:
                filename, file_ext = os.path.splitext(tv_item_path)
                if self.is_media_file_type(file_ext):
                    if self.config.args.origin_name:
                        new_tv_file_name = os.path.basename(tv_item_path)
                    else:
                        new_tv_file_name = self.gen_tv_season_epison_group(
                            tv_item, parse_group, resolution)
                    season_folder_full_path = os.path.join(self.CAT_NAME_TV, gen_folder,
                                                        parse_season)
                    self.fs_manager.target_copy(tv_item_path, season_folder_full_path, new_tv_file_name)

        self.mk_plex_match(os.path.join(self.CAT_NAME_TV, gen_folder), folder_tmdb_parser)
        self.mk_media_nfo(os.path.join(self.CAT_NAME_TV, gen_folder), "", folder_tmdb_parser)
        self.target_dir_hook(os.path.join(self.CAT_NAME_TV, gen_folder), tmdbidstr=str(folder_tmdb_parser.tmdbid), tmdbcat=folder_tmdb_parser.tmdbcat, tmdbtitle=folder_tmdb_parser.title, tmdbobj=folder_tmdb_parser)


    def cut_origin_name(self, src_origin_name):
        m1 = re.search( r'^.*\b(720p|1080[pi]|2160p|576i)[\. ]*', src_origin_name, flags=re.I)
        sstr = src_origin_name
        if m1:
            sstr = src_origin_name[m1.span(1)[0]:]
        else:
            m2 = re.search( r'([(\[]?((19\d{2}\b|20\d{2})(-19\d{2}|-20\d{2})?)[)\]]?)(?!.*\b\d{4}\b.*)', src_origin_name, flags=re.A | re.I)
            if m2:
                sstr = sstr[m2.span(1)[1]:].strip()
        sstr = re.sub(r'^[. ]*', '', sstr)
        sstr = re.sub(r'-', '_', sstr)
        return sstr

    def gen_tmdb_tail(self, name_parser):
        tmdb_tail = ''
        if (name_parser and name_parser.tmdbid > 0 and self.config.args.emby_bracket):
            tmdb_tail = ' [tmdbid=' + str(name_parser.tmdbid) + ']'
        return tmdb_tail
    
    def gen_movie_origin_name(self, media_src, movie_name, year, name_parser=None):
        # When --origin-name is used, return only the original filename (basename)
        # Do not prepend the scraped title/year or tmdb tail.
        origin_name = os.path.basename(media_src)
        return origin_name.strip()

    def gen_movie_tmdb_origin_name(self, media_src, movie_name, year, name_parser=None):
        origin_name = os.path.basename(media_src)
        ch1 = ' - '
        tmdb_tail = self.gen_tmdb_tail(name_parser)
        media_name = movie_name + ((' (' + year + ')' ) if year else '') + tmdb_tail + ch1 + origin_name
        return media_name.strip()

    def gen_movie_res_group(self, media_src, movie_name, year, resolution, group, name_parser=None):
        filename, file_ext = os.path.splitext(media_src)
        ch1 = ' - ' if (resolution or group) else ''
        ch2 = '_' if (resolution and group) else ''
        tmdb_tail = self.gen_tmdb_tail(name_parser)
        media_name = movie_name + ((' (' + year + ')' ) if year else '') + tmdb_tail + ch1 + (
            resolution if resolution else '') + ch2 + (
                                                    group
                                                    if group else '') + file_ext
        return media_name.strip()

    def set_args_category(self):
        cat = ''
        if self.config.args.tv:
            cat = self.CAT_NAME_TV
        elif self.config.args.movie:
            cat = self.CAT_NAME_MOVIE
        return cat

    def gen_cat_folder_name(self, parser):
        if self.config.args.torcpdb_url and parser.tmdbid <= 0 and parser.tmdbcat in ['tv', 'movie']:
            return 'TMDbNotFound'
        else:
            if parser.tmdbcat == 'movie':
                self.CAT_NAME_MOVIE = self.config.args.movie_folder_name
                return self.config.args.movie_folder_name
            elif parser.tmdbcat == 'tv':
                self.CAT_NAME_TV = self.config.args.tv_folder_name
                return self.config.args.tv_folder_name
            else:
                return parser.tmdbcat

    def process_bdmv(self, media_src, folder_gen_name, cat_folder, tmdb_parser=None):
        dest_cat_folder_name = os.path.join(cat_folder, folder_gen_name)
        if self.config.args.full_bdmv:
            for bdmv_item in os.listdir(media_src):
                full_bdmv_item = os.path.join(media_src, bdmv_item)
                self.fs_manager.target_copy(full_bdmv_item, dest_cat_folder_name)
            return

        if self.config.args.extract_bdmv:
            bdmv_dir = os.path.join(media_src, 'BDMV', 'STREAM')
            if not os.path.isdir(bdmv_dir):
                logger.info('BDMV/STREAM/ dir not found in   %s ' % media_src)
                return

            largest_streams = sorted(self.getLargestFiles(bdmv_dir))
            folder_gen_list = re.split(r'\/|\\', folder_gen_name)
            folder_name = folder_gen_list[0]
            disk_name = "" if len(folder_gen_list) <= 1 else folder_gen_list[1]

            if tmdb_parser and tmdb_parser.tmdbcat == 'tv':
                m = re.search(r"(S|Season)(\d+)", disk_name, re.I)
                if m:
                    ss_name = "S%02d" % int(m[2])
                else:
                    ss_name = "S01"
                dest_cat_folder_name = os.path.join(cat_folder, folder_name, ss_name)
                time.sleep(1)
                ep_count = self.count_media_file(os.path.join(self.config.args.hd_path, dest_cat_folder_name))
                for epidx, stream in enumerate(largest_streams):
                    ts_name = "%s %sE%02d %s_%s" % (folder_name, ss_name, ep_count+epidx+1, disk_name, os.path.basename(stream))
                    self.fs_manager.target_copy(stream, dest_cat_folder_name, ts_name)
            else:
                for stream in largest_streams:
                    ts_name = folder_name + ' - ' + os.path.basename( stream)
                    self.fs_manager.target_copy(stream, dest_cat_folder_name, ts_name)

        else:
            logger.info('Skip BDMV/ISO  %s ' % media_src)

    def process_music(self, media_src, folder_cat, folder_gen_name):
        self.fs_manager.target_copy(media_src, folder_cat)
        self.target_dir_hook('Music', tmdbidstr='', tmdbcat='music', tmdbtitle=os.path.basename(media_src), tmdbobj=None)


    def process_movie_dir(self, media_src, folder_cat, folder_gen_name, folder_tmdb_parser):
        if os.path.isdir(os.path.join(media_src, 'BDMV')):
            if self.config.args.full_bdmv or self.config.args.extract_bdmv:
                self.process_bdmv(media_src, folder_gen_name, 'MovieM2TS', tmdb_parser=folder_tmdb_parser)
                self.target_dir_hook(os.path.join('MovieM2TS', folder_gen_name), tmdbidstr=str(folder_tmdb_parser.tmdbid), tmdbcat=folder_tmdb_parser.tmdbcat, tmdbtitle=folder_tmdb_parser.title, tmdbobj=folder_tmdb_parser)
            else:
                logger.info('Skip BDMV/ISO  %s ' % media_src)
            return

        if not os.path.isdir(media_src):
            return

        test_file = self.get_music_file(media_src)
        if test_file:
            self.process_music(media_src, 'Music', folder_gen_name)
            return

        count_media_files = self.count_media_file(media_src)
        for movie_item in os.listdir(media_src):
            if self.useless_file(movie_item):
                logger.info('SKIP useless file: [%s] ' % movie_item)
                continue
            if self.self_gen_category_dir(movie_item):
                logger.info('SKIP self-generated dir: [%s] ' % movie_item)
                continue

            if (os.path.isdir(os.path.join(media_src, movie_item))):
                if os.path.isdir(os.path.join(media_src, movie_item, 'BDMV')):
                    logger.info(" Alert: MovieBDMV in a Movie dir.....?")
                    self.process_bdmv(os.path.join(media_src, movie_item),
                                os.path.join(folder_gen_name, movie_item),
                                'MovieM2TS')
                else:
                    logger.info('SKip dir in movie folder: [%s] ' % movie_item)
                continue
            
            filename, file_ext = os.path.splitext(movie_item)
            if file_ext.lower() in ['.iso']:
                if self.config.args.full_bdmv or self.config.args.extract_bdmv:
                    dest_cat_folder_name = os.path.join('BDMVISO', folder_gen_name)
                    self.fs_manager.target_copy(os.path.join(media_src, movie_item), dest_cat_folder_name)
                    self.target_dir_hook(dest_cat_folder_name, tmdbidstr='', tmdbcat='iso', tmdbtitle=movie_item, tmdbobj=None) 
                else:
                    logger.info('SKip iso file: [%s] ' % movie_item)
                continue

            if not self.is_media_file_type(file_ext):
                logger.info('Skip : %s ' % movie_item)
                continue

            p = folder_tmdb_parser
            if not (self.config.args.tmdbid and self.config.args.single):
                if not folder_tmdb_parser.tmdbhard and (folder_tmdb_parser.tmdbid <= 0) or count_media_files > 1:
                    fn_ok = is_0day_name(movie_item)
                    if fn_ok:
                        pf = TMDbNameParser(self.config.args.torcpdb_url, self.config.args.torcpdb_apikey)
                        pf.parse(movie_item, by_tordb=(self.config.args.torcpdb_url is not None))
                        pf.title = self._fix_nt_name(pf.title)
                        if pf.tmdbid > 0 or fn_ok:
                            p = pf

            cat = self.gen_cat_folder_name(p)
            dest_folder_name = self.gen_media_folder_name(p)
            dest_cat_folder_name = os.path.join(cat, dest_folder_name)
            media_src_item = os.path.join(media_src, movie_item)

            if cat == self.CAT_NAME_TV:
                logger.info('Miss Categoried TV: [%s] ' % media_src)
                self.copy_tv_folder_items(media_src, dest_folder_name, p.season, p.group,
                                p.resolution, p)
                return
            elif cat in ['TMDbNotFound', 'HDTV', 'Audio', 'eBook']:
                self.fs_manager.target_copy(media_src_item, dest_cat_folder_name)
                self.target_dir_hook(dest_cat_folder_name, tmdbidstr=str(p.tmdbid), tmdbcat=p.tmdbcat, tmdbtitle=p.title, tmdbobj=p)
                continue
            else:
                if self.config.args.origin_name:
                    year_str = str(p.year) if p.year > 0 else ''
                    new_movie_name = self.gen_movie_origin_name(movie_item, p.title, year_str,
                                                    name_parser=p)
                elif self.config.args.tmdb_origin_name:
                    year_str = str(p.year) if p.year > 0 else ''
                    new_movie_name = self.gen_movie_tmdb_origin_name(movie_item, p.title, year_str,
                                                    name_parser=p)
                else:
                    year_str = str(p.year) if p.year > 0 else ''
                    new_movie_name = self.gen_movie_res_group(movie_item, p.title, year_str,
                                                    p.resolution, p.group, name_parser=p)
                self.fs_manager.target_copy(media_src_item, dest_cat_folder_name, new_movie_name)
                self.mk_media_nfo(dest_cat_folder_name, new_movie_name, p)
                self.target_dir_hook(dest_cat_folder_name, tmdbidstr=str(p.tmdbid), tmdbcat=p.tmdbcat, tmdbtitle=p.title, tmdbobj=p)


    def mk_plex_match(self, target_dir, tmdb_parser):
        if not self.config.args.make_plex_match:
            return

        if not tmdb_parser:
            return

        pm_filepath = os.path.join(self.config.args.hd_path, target_dir, '.plexmatch')
        with open(pm_filepath, "w", encoding='utf-8') as pm_file:
            pm_file.write("Title: %s\ntmdbid: %d\n" %
                        (tmdb_parser.title, tmdb_parser.tmdbid))
            if tmdb_parser.year > 1990:
                pm_file.write("Year: %d\n" % (tmdb_parser.year))

    def write_nfo_file(self, nfo_filename, et_root):
        with open(nfo_filename, "w", encoding='utf-8') as nfo_file:
            nfo_file.write(ET.tostring(et_root, encoding="unicode"))

    def mk_media_nfo(self, target_dir, media_filename, tmdb_parser):
        if not self.config.args.make_nfo:
            return
        if not tmdb_parser:
            return
        if tmdb_parser.tmdbid < 0:
            return
        
        if tmdb_parser.tmdbcat == 'tv':
            root = ET.Element("tvshow")
            nfo_filename = 'tvshow.nfo'
        elif tmdb_parser.tmdbcat == 'movie':
            root = ET.Element("movie")
            fn, ext = os.path.splitext(media_filename)
            nfo_filename = fn + ".nfo"
        else:
            return
        
        title = ET.SubElement(root, "title")
        title.text = tmdb_parser.title

        year = ET.SubElement(root, "year")
        year.text = str(tmdb_parser.year)

        tmdbid = ET.SubElement(root, "tmdbid")
        tmdbid.text = str(tmdb_parser.tmdbid)

        if tmdb_parser.original_title:
            original_title = ET.SubElement(root, "originaltitle")
            original_title.text = tmdb_parser.original_title

        if tmdb_parser.overview:
            plot = ET.SubElement(root, "plot")
            plot.text = tmdb_parser.overview

        if tmdb_parser.vote_average: 
            rating = ET.SubElement(root, "rating")
            rating.text = str(tmdb_parser.vote_average)

        if tmdb_parser.genre_ids:
            genre = ET.SubElement(root, "genre")
            genre_item = ET.SubElement(genre, "item")
            genre_item.text = tmdb_parser.get_genres_str()

        media_dir = self.fs_manager.get_dest_dir(target_dir, self.CAT_NAME_TV, self.CAT_NAME_MOVIE)
        if not os.path.exists(media_dir):
            logger.warning('media dir not created: ' + media_dir)
            return
        nfo_filepath = os.path.join(media_dir, nfo_filename)
        self.write_nfo_file(nfo_filepath, root)

    def target_dir_hook(self, target_dir, tmdbidstr='', tmdbcat='', tmdbtitle='', tmdbobj=None):
        export_target_dir = target_dir
        # logger.info('Target Dir: ' + export_target_dir)
        if self.export_obj:
            self.export_obj.onOneItemTorcped(export_target_dir, self.cur_media_name, tmdbidstr, tmdbcat, tmdbtitle, tmdbobj)
        if self.config.args.after_copy_script:
            import subprocess        
            cmd = [self.config.args.after_copy_script, export_target_dir, self.cur_media_name, tmdbidstr, tmdbcat, tmdbtitle]
            subprocess.Popen(cmd).wait()
        return

class Torcp:
    """Public interface for the torcp script."""
    def __init__(self):
        self.config = None
        self.processor = None

    def main(self, argv=None, exportObject=None):
        """The main function of the script."""
        self.config = Config(argv)
        fs_manager = FileSystemManager(self.config)
        self.processor = MediaReNameProcessor(self.config, fs_manager, exportObject)
        self.processor.main(exportObject)

def main():
    torcp_instance = Torcp()
    torcp_instance.main()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,  format='%(asctime)s %(levelname)s %(funcName)s %(message)s')
    main()