# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# streamondemand.- XBMC Plugin
# Canal para asiansubita
# http://blog.tvalacarta.info/plugin-xbmc/streamondemand.
# ------------------------------------------------------------
import re
import urlparse

from core import logger
from core import scrapertools
from core.item import Item
from servers import adfly
from servers import servertools

__channel__ = "asiansubita"
__category__ = "F,A"
__type__ = "generic"
__title__ = "asiansubita"
__language__ = "IT"

host = "http://asiansubita.altervista.org"


def isGeneric():
    return True


def mainlist(item):
    logger.info("streamondemand.asiansubita mainlist")

    itemlist = [Item(channel=__channel__,
                     title="[COLOR azure]Home[/COLOR]",
                     action="peliculas",
                     url=host,
                     thumbnail="http://orig03.deviantart.net/6889/f/2014/079/7/b/movies_and_popcorn_folder_icon_by_matheusgrilo-d7ay4tw.png"),
                Item(channel=__channel__,
                     title="[COLOR azure]Genere - Nazione[/COLOR]",
                     action="categorias",
                     url=host,
                     thumbnail="http://xbmc-repo-ackbarr.googlecode.com/svn/trunk/dev/skin.cirrus%20extended%20v2/extras/moviegenres/All%20Movies%20by%20Genre.png"),
                Item(channel=__channel__,
                     title="[COLOR yellow]Cerca...[/COLOR]",
                     action="search",
                     thumbnail="http://dc467.4shared.com/img/fEbJqOum/s7/13feaf0c8c0/Search")]

    return itemlist


def search(item, texto):
    logger.info("[asiansubita.py] " + item.url + " search " + texto)

    item.url = host + "/?s=" + texto

    try:
        return peliculas(item)

    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def peliculas(item):
    logger.info("streamondemand.asiansubita peliculas")

    itemlist = []

    # Descarga la pagina
    data = scrapertools.cache_page(item.url)

    # Extrae las entradas (carpetas)
    patron = '<!-- Post Type 3 -->\s*'
    patron += '<a.*?href="(.*?)" title="(.*?)" rel="bookmark">.*?<img src="(.*?)".*?<div class="entry-summary">\s*'
    patron += '(.*?)<a class="more-link"'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle, scrapedthumbnail, scrapedplot in matches:
        scrapedplot = scrapertools.decodeHtmlentities(scrapedplot)
        title = scrapertools.decodeHtmlentities(scrapedtitle)

        tmdbtitle1 = scrapedtitle.split("[")[0]
        tmdbtitle = tmdbtitle1.split("(")[0]
        year = scrapertools.find_single_match(scrapedtitle, '\((\d+)\)')
        try:
            plot, fanart, poster, extrameta = info(tmdbtitle, year)

            itemlist.append(
                Item(channel=__channel__,
                     thumbnail=poster,
                     fanart=fanart if fanart != "" else poster,
                     extrameta=extrameta,
                     plot=str(plot),
                     action="findvideos",
                     title="[COLOR azure]" + title + "[/COLOR]",
                     url=scrapedurl,
                     fulltitle=title,
                     show=title,
                     folder=True))
        except:
            itemlist.append(
                Item(channel=__channel__,
                     action="findvideos",
                     title=title,
                     url=scrapedurl,
                     thumbnail=scrapedthumbnail,
                     fulltitle=title,
                     show=title,
                     plot=scrapedplot,
                     viewmode="movie_with_plot"))

    # Paginación
    patron = '<div class="nav-previous"><a href="(.*?)" ><span class="meta-nav">&larr;</span> Articoli precedenti</a></div>'
    next_page = scrapertools.find_single_match(data, patron)

    if next_page != "":
        itemlist.append(
            Item(channel=__channel__,
                 action="peliculas",
                 title="[COLOR orange]Post piu' vecchi >>[/COLOR]",
                 url=next_page,
                 thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png"))

    return itemlist


def categorias(item):
    logger.info("streamondemand.asiansubita categorias")

    itemlist = []

    data = scrapertools.cache_page(item.url)

    # The categories are the options for the combo
    patron = '<li id="menu-item-[^>"]+" class="menu-item menu-item-type-taxonomy menu-item-object-category menu-item-[^>"]+"><a href="(.*?)">(.*?)</a></li>'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        itemlist.append(
            Item(channel=__channel__,
                 action="peliculas",
                 title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                 url=urlparse.urljoin(host, scrapedurl)))

    return itemlist


def findvideos(item):
    logger.info("[asiansubita.py] findvideos")

    itemlist = []

    # Descarga la página
    data = scrapertools.cache_page(item.url)

    # Extrae las datos
    thumbnail = scrapertools.find_single_match(data, 'src="([^"]+)"[^<]+</p>')
    plot = scrapertools.find_single_match(data, '<p style="text-align: justify;">(.*?)</p>')
    plot = scrapertools.decodeHtmlentities(plot)

    patron = 'href="(http://adf.ly/[^"]+)" target="_blank">([^<]+)</a>'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
        title = "[" + scrapedtitle + "] " + item.fulltitle

        itemlist.append(
            Item(channel=__channel__,
                 action="play",
                 title=title,
                 url=scrapedurl,
                 thumbnail=thumbnail,
                 plot=plot,
                 fulltitle=item.fulltitle,
                 show=item.show))

    return itemlist


def play(item):
    logger.info("[asiansubita.py] play")

    data = adfly.get_long_url(item.url)

    itemlist = servertools.find_video_items(data=data)

    for videoitem in itemlist:
        videoitem.title = item.show
        videoitem.fulltitle = item.fulltitle
        videoitem.show = item.show
        videoitem.thumbnail = item.thumbnail
        videoitem.channel = __channel__

    return itemlist


def info(title, year):
    logger.info("streamondemand.asiansubita info")
    try:
        from core.tmdb import Tmdb
        oTmdb = Tmdb(texto_buscado=title, year=year, tipo="movie", include_adult="false", idioma_busqueda="it")
        if oTmdb.total_results > 0:
            extrameta = {"Year": oTmdb.result["release_date"][:4],
                         "Genre": ", ".join(oTmdb.result["genres"]),
                         "Rating": float(oTmdb.result["vote_average"])}
            fanart = oTmdb.get_backdrop()
            poster = oTmdb.get_poster()
            plot = oTmdb.get_sinopsis()
            return plot, fanart, poster, extrameta
    except:
        pass
