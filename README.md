# torcp2
* since 2024.11.24 启动 torcp2 以将查询 TMDb/IMDb 等操作分离出，以对 TORDB 作 api 查询方式实现
* 与 torcp 差别在于，查询是通过 torcpdb 完成，在命令行中需要给 `--torcpdb-url` 和 `--torcpdb-apikey` 信息
---------

## Last Update
* 2025.8.9 新增 `--title-regex` 指定文件名或目录名，与此正则匹配上的部分进行识别
* 2025.8.7 支持 `.strm` 
* 2024.11.21 查 IMDb 由 episode 获取 series 的 IMDb，再查 TMDb
* 2024.10.23 `--add-year-dir` 在媒体名称目录之上，加一层年份目录
* 2023.5.24 对于包括 tmdbid=12345/tmdb-12345 的文件夹，都以目录中所包含的标识，对目录下的各文件/目录进行刮削
> 即对于 siteid 和刮削完成后的包含Emby/Plex括号的文件夹，都会进入对所有文件进行处理
* 2023.4.9  `--make-nfo` 在媒体目录内生成 .nfo 文件
* 2023.3.22 在资源目录之上，如果有一个目录名中带有 `tmdb=tv-123456` 或 `tmdb=m-123456` 信息，则会进入目录以此信息对文件进行刮削
* 2023.3.20 改为 logger 输出；参考 `tp.py` 设置输出目标和格式
* 2023.2.7 `--sep-area` 所有地区分目录，不可与语言 `--lang` 同时使用
* 2023.2.3 `--genre` 支持按类型分目录，以逗号分隔，使用`--tmdb-lang`所设的语言相关的类型词汇；如果媒体包含列出的类型，则在Movie/TV目录下单独成分目录，未在列的在 other 目录；如果同时进行了语言或地区分目录，类型目录与语言和地区同级目录，即类型中未在列的才分语言和地区；
* 2023.1.27 torcp代码组织为类(class)形式，以便通过代码形式进行调用，调用入口为 `main(argv, exportObject)`，参见11节说明
* 2022.12.23 `--tmdbid`，用`m-12345`或`movie-12345` 及 `t-54321`或`tv-54321`这样的形式，指定资源的TMDb信息
* 2022.11.30 `--tmdb-origin-name`, 对于电影，生成 `刮削名 (年份) - 原文件名`  这样的文件名，对于Emby可以实现以原文件名作为版本名。
* 2022.11.11 支持**Site-Id-IMDb**文件夹，即在资源目录之上，有一个目录名中带有 `[imdb=tt123456]` 或以 `tt123456` 结尾的目录
* 2022.10.26 `--make-plex-match`  Create a .plexmatch file at the top level of a series
* 2022.9.5 `--imdbid` 在 `-s` 模式下指定媒体的 IMDb id
* 2022.9.4  `--after-copy-script` 执行外部脚本时，会传入3个参数：生成的媒体路径，原媒体文件(夹)名，tmdbid
* 2022.8.18 如果资源文件夹命名里面带`[imdbid=xxx]`或`[tmdbid=xxx]`，则直接使用这样的id去TMDb中搜索资源信息
* 2022.7.21 `--after-copy-script` 在完成硬链后，执行一外部脚本，以便实现Plex刮削
* 2022.6.20 `-e, --keep-ext`, 可使用参数 `all` 
* 2022.4.3: `--make-log` 在目标目录中建立一个log文件，以便追溯原文件名
* 2022.3.23: `--symbolink` support symbol link
* 2022.3.13: `--lang` dispatch to different folders base on TMDb language
* 2022.2.26: `--tmdb-api-key` Support TMDb search 

## 使用方法:
* 运行 `python tp.py -h `
```
usage: tp.py [-h] -d HD_PATH [-e KEEP_EXT] [-l LANG] [--genre GENRE] [--other-dir OTHER_DIR] [--sep-area] [--sep-area5] [--sep-area7] [--torcpdb-url TORCPDB_URL] [--torcpdb-apikey TORCPDB_APIKEY]
             [--tv-folder-name TV_FOLDER_NAME] [--movie-folder-name MOVIE_FOLDER_NAME] [--tv] [--movie] [--dryrun] [--single] [--extract-bdmv] [--full-bdmv] [--origin-name] [--tmdb-origin-name]
             [--sleep SLEEP] [--move-run] [--make-log] [--symbolink] [--cache] [--emby-bracket] [--plex-bracket] [--make-plex-match] [--make-nfo] [--after-copy-script AFTER_COPY_SCRIPT]
             [--imdbid IMDBID] [--tmdbid TMDBID] [--extitle EXTITLE] [--site-str SITE_STR] [--add-year-dir] [--genre-with-area GENRE_WITH_AREA] [-pr TITLE_REGEX]
             MEDIA_DIR

torcp: a script hardlink media files and directories in Emby-happy naming and structs.

positional arguments:
  MEDIA_DIR             The directory contains TVs and Movies to be copied.

options:
  -h, --help            show this help message and exit
  -d HD_PATH, --hd_path HD_PATH
                        the dest path to create Hard Link.
  -e KEEP_EXT, --keep-ext KEEP_EXT
                        keep files with these extention('srt,ass').
  -l LANG, --lang LANG  seperate dir by language('cn,en').
  --genre GENRE         seperate dir by genre('anime,document').
  --other-dir OTHER_DIR
                        for any dir Other than Movie/TV.
  --sep-area            seperate dir by all production area.
  --sep-area5           seperate 5 dirs(cn,hktw,jp,kr,useu,other) by production area.
  --sep-area7           seperate 7 dirs(us,cn,hk,tw,jp,kr,occident,other) by production area.
  --torcpdb-url TORCPDB_URL
                        Search torcpdb API for the tmdb id
  --torcpdb-apikey TORCPDB_APIKEY
                        apikey for torcpdb API
  --tv-folder-name TV_FOLDER_NAME
                        specify the name of TV directory, default TV.
  --movie-folder-name MOVIE_FOLDER_NAME
                        specify the name of Movie directory, default Movie.
  --tv                  specify the src directory is TV.
  --movie               specify the src directory is Movie.
  --dryrun              print message instead of real copy.
  --single, -s          parse and copy one single folder.
  --extract-bdmv        extract largest file in BDMV dir.
  --full-bdmv           copy full BDMV dir and iso files.
  --origin-name         keep origin file name.
  --tmdb-origin-name    filename emby bracket - origin file name.
  --sleep SLEEP         sleep x seconds after operation.
  --move-run            WARN: REAL MOVE...with NO REGRET.
  --make-log            Make a log file.
  --symbolink           symbolink instead of hard link
  --cache               cache searched dir entries
  --emby-bracket        ex: Alone (2020) [tmdbid=509635]
  --plex-bracket        ex: Alone (2020) {tmdb-509635}
  --make-plex-match     Create a .plexmatch file at the top level of a series
  --make-nfo            Create a .nfo file in the media dir
  --after-copy-script AFTER_COPY_SCRIPT
                        call this script with destination folder path after link/move
  --imdbid IMDBID       specify the IMDb id, -s single mode only
  --tmdbid TMDBID       specify the TMDb id, -s single mode only
  --extitle EXTITLE     specify the extra title to search
  --site-str SITE_STR   site-id(ex. hds-12345) folder name, set site strs like ('chd,hds,ade,ttg').
  --add-year-dir        Add a year dir above the media folder
  --genre-with-area GENRE_WITH_AREA
                        specify genres with area subdir, seperated with comma
  -pr TITLE_REGEX, --title-regex TITLE_REGEX
                        the regex to match the title from path
```

---

## 通过 torcpdb 进行 TMDb 查询
* 对一个目录进行遍历查询，完成硬链
```sh
python tp.py  /home/test/ -d /home/test/result3/ --torcpdb-url 'http://192.168.5.10:5009' --torcpdb-apikey  something 
```

* 对单个文件进行硬链的例子
```sh
python tp.py "~/test/Is.S01.2018.2019.1080p.NF.WEB-DL.DDP2.0.x264-quypham@TTG/"  -d '~/fuse/test2' --torcpdb-url 'http://192.168.5.10:5009' --torcpdb-apikey  something --emby-bracket --tmdb-origin-name --sep-area5  --tv -s --tmdbid 104486
```

----

## 媒体文件名生成方案

### `--origin-name` 与 `--tmdb-origin-name`
* 对于IMDb搜索到的媒体资源，目录结构将按Emby/Plex所约定的规范进行组织，目录内的文件名，有3种可能的方式：
1. 默认的：刮削名 (年份) - 分辨率_组名.mkv
2. `--origin-name`：TV直接使用 原文件名, Movie：刮削名 (年份) - 原文件名
3. `--tmdb-origin-name`：刮削名 (年份) - 原文件名


### `--emby-bracket`， --plex-bracket`
* 可以使用 `--emby-bracket` 选项在 「刮削名 (年份)」之后加上如「[tmdbid=509635]」这样的emby bracket，以便Emby在刮削时直接辨认使用；
* 对于plex，可以使用 `--plex-bracket` 生成如 「{tmdb-509635}」这样的后缀；
* 这两个选项在使用  `--tmdb-origin-name` 时也是生效的

* 比如：
```sh
python3 tp.py ../test -d ../test/result --torcpdb-url 'http://192.168.5.10:5009' --torcpdb-apikey something --emby-bracket --tmdb-origin-name  --emby-bracket
```
* 结果如下：
```
.
├── A.Good.Day.to.Die.Hard.2013.1080p.BluRay.x265.10bit.3Audio.MNHD-FRDS
│   ├── A.Good.Day.to.Die.Hard.Extended.Version.2013.1080p.BluRay.x265.10bit.3Audio.MNHD-FRDS.mkv
│   ├── A.Good.Day.to.Die.Hard.Theatrical.Version.2013.1080p.BluRay.x265.10bit.3Audio.MNHD-FRDS.mkv
│   └── Bonus
└── result
    └── Movie
        └── 虎胆龙威5 (2013) [tmdbid=47964]
            ├── 虎胆龙威5 (2013) [tmdbid=47964] - A.Good.Day.to.Die.Hard.Extended.Version.2013.1080p.BluRay.x265.10bit.3Audio.MNHD-FRDS.mkv
            └── 虎胆龙威5 (2013) [tmdbid=47964] - A.Good.Day.to.Die.Hard.Theatrical.Version.2013.1080p.BluRay.x265.10bit.3Audio.MNHD-FRDS.mkv

```
* 而如果不使用 `--tmdb-origin-name `
```sh
python3 tp.py ../test -d ../test/result  --torcpdb-url 'http://192.168.5.10:5009' --torcpdb-apikey something  --emby-bracket 
```
* 得到结果如下：
```
.
├── A.Good.Day.to.Die.Hard.2013.1080p.BluRay.x265.10bit.3Audio.MNHD-FRDS
│   ├── A.Good.Day.to.Die.Hard.Extended.Version.2013.1080p.BluRay.x265.10bit.3Audio.MNHD-FRDS.mkv
│   ├── A.Good.Day.to.Die.Hard.Theatrical.Version.2013.1080p.BluRay.x265.10bit.3Audio.MNHD-FRDS.mkv
│   └── Bonus
└── result
    └── Movie
        └── 虎胆龙威5 (2013) [tmdbid=47964]
            └── 虎胆龙威5 (2013) [tmdbid=47964] - 1080p_FRDS.mkv
```
> 其中后一个版本会因文件已存在而跳过


-----

## 传入IMDb信息
* 在大部分情况下，有IMDb信息，可以确定地查出TMDb信息，有两种类型的方法：

### 建一个包含IMDb id的目录
* 下载资源时多建一层父目录，包含IMDb信息： 即用户可以在rss站时，添加种子时就建一个以 `站点-id-IMDb` 为名的目录，作为下载资源的父目录，则torcp将以此IMDb id作为信息，对下层目录作为资源进行刮削。（by boomPa), 如：
```
audies_movie-1234-tt123456\
  Some.Movie.2022.1080p.BluRay.x264.DTS-ADE\
      Some.Movie.2022.1080p.BluRay.x264.DTS-ADE.mkv
```

* `站点-id-IMDb` 目录可能没有IMDb，对于 `站点关键字-id` 结构的目录torcp也会视为资源的父目录，即多进一层进行解析，其中 `站点关键字` 可由 `--site-str` 指定，如指定了 `--site-str audies_movie` 则碰到 `audies_movie-1234` 目录，则会进入内层目录对其中的文件夹或文件进行刮削。

* 另外，如果资源文件夹的名字，本身带有 `[imdb=tt123456]` 或 `[tmdb=123456]` 结尾，也会被用于直接指定媒体



### 以`--imdbid`参数指定 IMDb id
* 在qb中添加种子时，加一个IMDb tag。这可以使用 [torcc](https://github.com/ccf-2012/torcc) 或 [torfilter](https://github.com/ccf-2012/torfilter) 实现
* 在下载完成时，将此 IMDb tag 以`--imdbid` 参数传给torcp。
* 详情参考[利用 qBittorrent 的完成后自动执行脚本功能实现入库](qb自动入库.md)

----

## 以代码调用torcp进行二次开发
* torcp 入口定义为：
```py  
torcp.main(argv=None, exportObject=None)
```
  * argv为输入参数列表，可将原本命令行中调用传入的参数，以字符串数组形式传入
  * exportObject意为：当一个媒体项目完成输出时，调用此对象的函数 `exportObject.onOneItemTorcped(targetDir, curMediaName, tmdbIdStr, tmdbCat)` 进行处理。一个目录可能会多次输出。
  * torcp原来以命令行方式运行时，仍然保持不变
  
* 示例
```py
from torcp import torcp

class TorcpExportObj:
	def onOneItemTorcped(self, targetDir, mediaName, tmdbIdStr, tmdbCat):
		print(targetDir, mediaName, tmdbIdStr, tmdbCat)


if __name__ == '__main__':
	argv = ["~/torccf/test", "-d", "~/torccf/result", "--torcpdb-url", "<torcpdb-url>", "--torcpdb-apikey", "<api-key>", "--emby-bracket", "--extract-bdmv", "--tmdb-origin-name"]
	eo = TorcpExportObj()
	o = Torcp()
	o.main(argv, eo)
```


## 类型，语言，地区分目录
* 地区 `--sep-area` 与 语言 `--lang` 只选其一，`--lang` 优先（有lang了就不看area）
* 如果地区没有取到，则会取语言代码；语言是小写，地区是大写；
* 类型 `--genre` 独立在 地区/语言之外，如果指定了类型，只有没指定的部分会分 地区/地区
* `--genre` 可设的类型值与 `--tmdb-lang` 所设语言相关，对于电影，中文有：
```
动作 冒险 动画 喜剧 犯罪 纪录 剧情 家庭 奇幻 历史 恐怖 音乐 
悬疑 爱情 科幻 电视电影 惊悚 战争 西部
```
英文有：
```
Action Adventure Animation Comedy Crime Documentary Drama Family Fantasy
History Horror Music Mystery Romance Science Fiction TV Movie Thriller
War Western
```

* 对于电视，中文有：
```
动作冒险 动画 喜剧 犯罪 纪录 剧情 家庭 儿童 悬疑 新闻 真人秀 Sci-Fi & Fantasy
肥皂剧 脱口秀 War & Politics 西部
```

英文有：
```
Action & Adventure Animation Comedy Crime Documentary Drama Family
Kids Mystery News Reality Sci-Fi & Fantasy Soap Talk War & Politics
```


---
## Acknowledgement 
 * [@leishi1313](https://github.com/leishi1313)
 * @Aruba  @ozz
 * @NishinoKana @Esc @Hangsijing @Inu 
