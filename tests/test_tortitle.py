import pytest
from torcp.tortitle import TorTitle

# Test cases based on tests/test_parseTorName.py and new requirements
TEST_CASES = [
    # Standard Movie
    ("Iron.Man.2008.BluRay.1080p.x264.DTS-WiKi", {"title": "Iron Man", "cntitle": '', "year": "2008", "type": "movie", "season": '', "episode": ''}),
    # Movie with Chinese Title
    ("[钢铁侠].Iron.Man.2008.BluRay.1080p.x264.DTS-WiKi", {"title": "Iron Man", "cntitle": "钢铁侠", "year": "2008", "type": "movie", "season": '', "episode": ''}),
    # Standard TV Show
    ("The.Mandalorian.S01E01.2019.1080p.WEB-DL.DDP5.1.H264-NTb", {"title": "The Mandalorian", "cntitle": '', "year": "2019", "type": "tv", "season": 'S01', "episode": 'E01'}),
    # TV Show with Chinese Title
    ("[曼达洛人].The.Mandalorian.S01E01.2019.1080p.WEB-DL.DDP5.1.H264-NTb", {"title": "The Mandalorian", "cntitle": "曼达洛人", "year": "2019", "type": "tv", "season": 'S01', "episode": 'E01'}),
    # TV Show with Season only
    ("The.Terminal.List.S01.2022.1080p.AMZN.WEB-DL.DDP5.1.H.264-BlackTV", {"title": "The Terminal List", "cntitle": '', "year": "2022", "type": "tv", "season": 'S01', "episode": ''}),
    # Movie with long name and dots
    ("The.Lord.of.the.Rings.The.Fellowship.of.the.Ring.2001.EXTENDED.1080p.BluRay.x264-FSiHD", {"title": "The Lord of the Rings The Fellowship of the Ring", "cntitle": '', "year": "2001", "type": "movie", "season": '', "episode": ''}),
    # Movie with year at the end
    ("1917.2019.1080p.BluRay.x264-SPARKS", {"title": "1917", "cntitle": '', "year": "2019", "type": "movie", "season": '', "episode": ''}),
    # Movie with no clear year (should not find one)
    ("Top.Gun.Maverick.1080p.BluRay.x264-SPARKS", {"title": "Top Gun Maverick", "cntitle": '', "year": '', "type": "movie", "season": '', "episode": ''}),
    # TV Show with Chinese title and season
    ("[终极名单].The.Terminal.List.S01.2022.1080p.AMZN.WEB-DL.DDP5.1.H.264-BlackTV", {"title": "The Terminal List", "cntitle": "终极名单", "year": "2022", "type": "tv", "season": 'S01', "episode": ''}),
    # Movie with brackets in title
    ("Zack.Snyders.Justice.League.2021.2160p.WEB-DL.DDP5.1.Atmos.DV.HEVC-CMRG", {"title": "Zack Snyders Justice League", "cntitle": '', "year": "2021", "type": "movie", "season": '', "episode": ''}),
    # Another TV show format
    ("Game.of.Thrones.Season.1.Complete.1080p.BluRay.x264-CiNEFiLE", {"title": "Game of Thrones", "cntitle": '', "year": '', "type": "tv", "season": 'S01', "episode": ''}),
    ('半暖时光.The.Memory.About.You.S01.2021.2160p.WEB-DL.AAC.H265-HDSWEB',
     {'title': 'The Memory About You', 'cntitle': '半暖时光', 'year': '2021', 'type': 'tv', "season": 'S01', "episode": ''}),
    ('不惑之旅.To.the.Oak.S01.2021.2160p.WEB-DL.AAC.H265-HDSWEB', {'title': 'To the Oak', 'cntitle': '不惑之旅', 'year': '2021', 'type': 'tv', "season": 'S01', "episode": ''}),
    ('Dinotrux S03E02 1080p Netflix WEB-DL DD 5.1 H.264-AJP69.mkv', {'title': 'Dinotrux', 'cntitle': '', 'year': '', 'type': 'tv', "season": 'S03', "episode": 'E02'}),
    ('排球女将.Moero.Attack.1979.Complete.WEB-DL.1080p.H264.DDP.MP3.Mandarin&Japanese-OPS', {'title': 'Moero Attack', 'cntitle': '排球女将', 'year': '1979', 'type': 'movie', "season": '', "episode": ''}),
    ("【红钻级收藏版】蜘蛛侠：英雄归来.全特效+内封三版字幕.Spider-Man.Homecoming.2017.2160P.BluRay.X265.10bit.HDR.DHD.MA.TrueHD.7.1.Atmos.English&Mandarin-GYT.strm", 
     {'title': 'Spider Man Homecoming', 'cntitle': '蜘蛛侠：英雄归来', 'year': '2017', 'type': 'movie', "season": '', "episode": ''}),
    ("21座桥-英语.21.Bridges.2019.BluRay.2160p.x265.10bit.HDR.mUHD-FRDS", 
     {'title': '21 Bridges', 'cntitle': '21座桥', 'year': '2019', 'type': 'movie', "season": '', "episode": ''}),
    ("13.Going.on.30.2004.Bluray.1080p.DTS.x264-CHD.strm", {'title': '13 Going on 30', 'cntitle': '', 'year': '2004', 'type': 'movie', "season": '', "episode": ''}),
    ('X档案.第一季.1993.中英字幕￡CMCT梦幻', {'title': 'X档案', 'cntitle': 'X档案', 'year': '1993', 'type': 'tv', "season": 'S01', "episode": ''}),
    ('Taxi.4.Director\'s.Cut.2007.Bluray.1080p.x264.DD5.1-wwhhyy@Pter.mkv', {'title': 'Taxi 4', 'cntitle': '', 'year': '2007', 'type': 'movie', "season": '', "episode": ''}),
    ('豹.1963.JPN.1080p.意大利语中字￡CMCT风潇潇', {'title': '豹', 'cntitle': '豹', 'year': '1963', 'type': 'movie', "season": '', "episode": ''}),
    ('金刚狼3殊死一战.Logan.2017.BluRay.1080p.x265.10bit.MNHD-FRDS', {'title': 'Logan', 'cntitle': '金刚狼3殊死一战', 'year': '2017', 'type': 'movie', "season": '', "episode": ''}),
    ('人工智能4K REMUX (2001)', {'title': '人工智能', 'cntitle': '人工智能', 'year': '2001', 'type': 'movie', "season": '', "episode": ''}),
    ('1988 骗徒臭事多 Dirty Rotten Scoundrels 豆瓣：8.2（美国）', {'title': 'Dirty Rotten Scoundrels', 'cntitle': '骗徒臭事多', 'year': '1988', 'type': 'movie', "season": '', "episode": ''}),

]

@pytest.mark.parametrize("name, expected", TEST_CASES)
def test_tor_title_parsing(name, expected):
    result = TorTitle(name).to_dict()
    assert result == expected