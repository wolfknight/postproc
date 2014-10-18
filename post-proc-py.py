#!/usr/bin/python
import os, shutil, re, sys, time
import ConfigParser


SEASON_FORMATS = ["(S.)([0-9][0-9])", "(Season )([0-9])(.*)"]

VIDEO_EXT_LIST = [".mkv", ".mp4", ".avi", ".wmv", ".mpeg4"]
SUB_EXT_LIST = [".srt", ".idx", ".sub"]
REMOVE_EXT_LIST = [".txt", ".nzb", ".srr", ".sfv", ".url", ".md5", ".par2", ".jpg", ".tbn", ".smi", ".exe"]

EPISODE_IDENTIFIER_LIST = [".*S[0-9][0-9]E[0-9][0-9].*", ".*Season [0-9][0-9] Episode [0-9][0-9].*",
                           ".*S[0-9][0-9].*EP[0-9][0-9].*", ".*[0-9][xX][0-9][0-9].*"]
EPISODE_REGEXP_LIST = ["(.*[Ss])([0-9][0-9])([Ee])([0-9][0-9])(.*)", "(.*)([0-9])([Xx])([0-9][0-9])(.*)",
                       "(.*Season.*)([0-9][0-9])(.*Episode.*)([0-9][0-9])(.*)",
                       "(.*S)([0-9][0-9])(.*EP)([0-9][0-9])(.*)"]
MOVIE_IDENTIFIER_LIST = [".*1080p.*", ".*720p.*"]
IGNORE_IDENTIFIER_LIST = ["_.*"]

# Version 1.0
# #### MAIN #####
def main():
    # Verify all the given paths exist
    for d in DIRS_TO_VERIFY:
        if not os.path.isdir(d):
            log.info("The directory '%s' doesn't exist. Exiting..." % d)
            sys.exit(1)

    downloadedFilesList = os.listdir(DOWNLOAD_DIR)
    # If there are no files in the download dir, exit the script
    if not downloadedFilesList:
        sys.exit(0)

    headerPrinted = False
    for downloadedFile in downloadedFilesList:
        downloadedFileFullPath = os.path.join(DOWNLOAD_DIR, downloadedFile)
        if isContainsIdentefier(downloadedFile, IGNORE_IDENTIFIER_LIST):
            log.debug("Ignoring the entry: '%s'" % downloadedFile)
            continue

        if not headerPrinted:
            log.info("** Files found starting post processing **")
            headerPrinted = True
        if isContainsIdentefier(downloadedFile, EPISODE_IDENTIFIER_LIST):
            log.info("Handling the episode: '%s'" % downloadedFile)
            processEpisode(downloadedFileFullPath)
        else:
            episodeFoundInDir = isFullSeason(downloadedFileFullPath)
            if episodeFoundInDir:
                processFullSeason(downloadedFileFullPath, episodeFoundInDir)
            elif isContainsIdentefier(downloadedFile, MOVIE_IDENTIFIER_LIST):
                log.info("Handling the movie: '%s'" % downloadedFile)
                processMovie(downloadedFileFullPath)
            else:
                log.info("Not sure what to do with '%s'. Ignoring..." % downloadedFile)
                ignoreEntry(downloadedFileFullPath)

def ignoreEntry(pathToIgnore):
    newPath = os.path.join(os.path.dirname(pathToIgnore), "_%s" % os.path.basename(pathToIgnore))
    log.debug("ignoreEntry: Renaming %s to %s" % (pathToIgnore, newPath))
    os.rename(pathToIgnore, newPath)

def removeNonEssential(directory):
    files = os.listdir(directory)
    for f in files:
        # Remove any video file that contains the word "sample"
        if re.match(".*sample.*", f, flags=re.IGNORECASE) and isVideo(f):
            try:
                log.debug("Removing the video file '%s' because it's a sample" % f)
                os.remove(os.path.join(directory, f))
            except Exception, e:
                log.error("Failed to remove '%s'. Err: %s" % (f, str(e)))
            continue

        fileName, fileExtension = os.path.splitext(f)
        if fileExtension in REMOVE_EXT_LIST:
            try:
                log.debug("Removing the file '%s' because of its extension" % f)
                os.remove(os.path.join(directory, f))
            except Exception, e:
                log.error("Failed to remove '%s'. Err: %s" % (f, str(e)))


def stripSubdirStructure(directory):
    log.debug("Stripping sub-directories structure for '%s'" % directory)
    for root, dirs, files in os.walk(directory, topdown=False):
        if root != directory:
            for regFile in files:
                fileFullPath = os.path.join(root, regFile)
                if os.path.exists(os.path.join(directory, regFile)):
                    newPath = os.path.splitext(fileFullPath)
                    newPath = "%s.%s%s" % (newPath[0], logger.getTime(humanReadable=False), newPath[1])
                    os.rename(fileFullPath, newPath)
                    fileFullPath = newPath
                try:
                    log.debug("Moving '%s' to '%s'" % (fileFullPath, directory))
                    shutil.move(fileFullPath, directory)
                except Exception, e:
                    log.error("Failed to move '%s' to '%s'. Err: %s" % (fileFullPath, directory, str(e)))
            try:
                log.debug("Removing the emtpy dir '%s'" % root)
                os.rmdir(root)
            except Exception, e:
                log.error("Failed to remove '%s'. Err: %s" % (root, str(e)))


def isContainsIdentefier(fileName, identifierList):
    for ident in identifierList:
        if re.match(ident, fileName, flags=re.IGNORECASE):
            log.debug("Matched the file name '%s' to the pattern '%s'" % (fileName, ident))
            return True
    log.debugMore("The file name '%s' didn't match any of the patterns %s" % (fileName, str(identifierList)))
    return False


def isFullSeason(directory):
    log.debug("Testing if '%s' is a full season" % directory)
    if os.path.isdir(directory):
        for f in os.listdir(directory):
            if isContainsIdentefier(f, EPISODE_IDENTIFIER_LIST):
                log.info("Found an episode in '%s', regarding it as full season." % directory)
                return os.path.join(directory, f)
    log.debug("No episode found in '%s', not a full season." % directory)
    return False


def isVideo(fileName):
    log.debugMore("Checking if '%s' is a video." % fileName)
    f, fileExtension = os.path.splitext(fileName)
    if fileExtension in VIDEO_EXT_LIST:
        log.debugMore("Identified as a video '%s'." % fileName)
        return True
    log.debugMore("Not a video '%s'." % fileName)
    return False


def isSubtitle(fileName):
    log.debugMore("Checking if '%s' is a subtitle." % fileName)
    f, fileExtension = os.path.splitext(fileName)
    if fileExtension in SUB_EXT_LIST:
        log.debugMore("Identified as a subtitle file '%s'." % fileName)
        return True
    log.debugMore("Not a subtitle file '%s'." % fileName)
    return False


def _moveMovieToDir(movieFolder, newDir):
    log.info("Moving the movie: '%s' to '%s'." % (movieFolder, newDir))
    try:
        shutil.move(movieFolder, newDir)
    except Exception, e:
        log.error("Failed to move '%s' to '%s'. Err: %s" % (movieFolder, newDir, str(e)))


def _createFolderForVidFile(movie):
    log.info("Creating folder for '%s'." % movie)
    movieFolder = os.path.splitext(movie)[0]
    try:
        os.makedirs(movieFolder)
        shutil.move(movie, movieFolder)
    except Exception, e:
        log.error("Failed to create folder and/or move the movie into the folder '%s'." % movie)
        return None
    return movieFolder


def processMovie(movie):
    if os.path.isdir(movie):
        log.debugMore("Movie '%s' is a movie folder." % movie)
        stripSubdirStructure(movie)
        removeNonEssential(movie)
        isContainsVideo = False
        for f in os.listdir(movie):
            if isVideo(f):
                isContainsVideo = True
                break
        if not isContainsVideo:
            log.info("No video file under '%s'. Ignoring..." % movie)
            ignoreEntry(movie)
            return
        _moveMovieToDir(movie, MOVIE_DIR)
    elif isVideo(movie):
        log.debugMore("Movie '%s' is a video file." % movie)
        movieFolder = _createFolderForVidFile(movie)
        if movieFolder:
            _moveMovieToDir(movieFolder, MOVIE_DIR)


def getEpisodeNewLocation(episodeNameList):
    if isinstance(episodeNameList, str):
        episodeNameList = [episodeNameList]
    for episodeName in episodeNameList:
        log.debug("Searching for TV Show path using '%s'." % episodeName)
        tvShowPath = getTvShowPath(episodeName)
        if not tvShowPath:
            continue
        log.debug("Found TV Show path '%s'." % tvShowPath)
        pathForEpisode = getSeasonPath(tvShowPath, os.path.basename(episodeName))
        if pathForEpisode:
            log.debug("Using season path '%s'." % pathForEpisode)
            return pathForEpisode

    log.info("No TV Show found for %s. Using Org dir " % str(episodeNameList))
    return ORG_DIR


def _moveEpisode(episodeFilePath, pathForEpisode):
    if os.path.normpath(os.path.dirname(episodeFilePath)) == os.path.normpath(pathForEpisode):
        log.info("No need to move the episode. Org dir and the episode location are the same.")
        return
    try:
        log.info("Moving the episode file '%s' to '%s'." % (os.path.basename(episodeFilePath), pathForEpisode))
        shutil.move(episodeFilePath, pathForEpisode)
    except Exception, e:
        log.error("Failed to move '%s' to '%s'. Err: %s" % (episodeFilePath, pathForEpisode, str(e)))


def processEpisode(episode):  # TODO - handle RAR archives
    if os.path.isdir(episode):
        log.debugMore("Episode '%s' is a folder" % episode)
        stripSubdirStructure(episode)
        removeNonEssential(episode)
        movedFile = False
        for f in os.listdir(episode):
            if isVideo(f) or isSubtitle(f):
                movedFile = True
                pathForEpisode = getEpisodeNewLocation([episode, f])
                episodeFilePath = os.path.join(episode, f)
                _moveEpisode(episodeFilePath, pathForEpisode)
        if movedFile:
            log.debug("Removing the directory: '%s'" % episode)
            try:
                shutil.rmtree(episode)
            except Exception, e:
                log.error("Failed to remove the directory '%s'. Err: %s" % (episode, str(e)))
        else:
            log.info("The folder %s does NOT contain a video file. Ignoring..." % episode)
            ignoreEntry(episode)
    elif isVideo(episode) or isSubtitle(episode):
        log.debugMore("Episode '%s' is a video or subtitle file." % episode)
        pathForEpisode = getEpisodeNewLocation(episode)
        _moveEpisode(episode, pathForEpisode)
    else:
        log.info("Episode '%s' is not a video. Ignoring..." % episode)
        ignoreEntry(episode)


def getNewSeasonName(seasonNumber):
    if int(seasonNumber) < 10 and "season" not in WANTED_SEASON_FORMAT.lower():
        seasonNewName = "%s%02d" % (WANTED_SEASON_FORMAT, seasonNumber)
    else:
        seasonNewName = "%s%d" % (WANTED_SEASON_FORMAT, seasonNumber)
    log.debug("Season's new name set to be '%s'" % seasonNewName)
    return seasonNewName


def processFullSeason(season, episodeFoundInSeasonDir):
    stripSubdirStructure(season)
    removeNonEssential(season)
    seasonName = os.path.basename(season)
    seasonNewName = ""
    foundTvPath = True
    seasonNewLocation = getTvShowPath(seasonName)
    if seasonNewLocation is None:
        seasonNewLocation = getTvShowPath(episodeFoundInSeasonDir)
    seasonNewLocation = getSeasonPath(seasonNewLocation, episodeFoundInSeasonDir)
    if seasonNewLocation is None:
        seasonNewLocation = ORG_DIR
        foundTvPath = False
    if os.path.dirname(season) == seasonNewLocation:
        log.info("No need to move the season, already in Org dir")
        return
    log.info("Moving the season: '%s' to '%s'" % (season, seasonNewLocation))
    try:
        if foundTvPath:
            epList = os.listdir(season)
            for episode in epList:
                shutil.move(os.path.join(season, episode), seasonNewLocation)
            os.rmdir(season)
        else:
            shutil.move(season, seasonNewLocation)
    except Exception, e:
        log.error("Failed to move '%s' to '%s'. Err: %s" % (season, seasonNewLocation, str(e)))


def normalize(string):
    """ Will remove non alpha numeric chars, and replace spaces with the dot sign.
        @return Lowercase normalized string
    """
    defaultDelimiter = "."
    delimiterList = [" ", "..", "-", "_"]
    tmpStr = string.lower()
    for d in delimiterList:
        if d in tmpStr:
            tmpStr = tmpStr.replace(d, defaultDelimiter)
    retStr = ''
    for c in tmpStr:
        if c.isalnum() or c == defaultDelimiter:
            retStr += c
    return retStr


def getTvShowPath(episodeName):
    """
    Will return the TV Show path for the episode or None if it doesn't exist

    @param episodeName The episode file name
    """
    for tvDir in TV_SHOW_DIRS:
        log.debug("Searching in TV dir '%s'." % tvDir)
        if not os.path.isdir(tvDir):
            log.debugMore("Not a folder: '%s'. Ignoring..." % tvDir)
            continue
        for tvShow in os.listdir(tvDir):
            log.debugMore("Checking if '%s' should be in '%s'." % (episodeName, tvShow))
            normTvShow = normalize(tvShow)
            normEpName = normalize(os.path.basename(episodeName))
            log.debugMore("Comparing %s in %s" % (normTvShow, normEpName))
            if normTvShow in normEpName:
                log.debug("Found show: %s for episode: %s" % (tvShow, episodeName))
                return os.path.join(tvDir, tvShow)
    log.debugMore("getTvShowPath: No Show found for '%s'." % episodeName)
    return None


def getSeasonAndEpisode(episodeName):
    """
    Will return a tuple with the season number and the episode number
    Raises exception if can't

    @param episodeName The episode file name
    """
    log.debugMore("Extracting season number and episode number from '%s'." % episodeName)
    m = None
    for regexp in EPISODE_REGEXP_LIST:
        m = re.match(regexp, episodeName, flags=re.IGNORECASE)
        if m:
            break
    if m:
        log.debugMore("The episode name '%s' contains the pattern S??E??." % episodeName)
        sNumber = m.group(2)
        eNumber = m.group(4)
        try:
            sNumber = int(sNumber)
            eNumber = int(eNumber)
        except ValueError:
            log.debugMore(
                "The extracted season '%s' and/or episode number '%s' are not numbers." % (str(sNumber), str(eNumber)))
        else:
            log.debug("Identified season %d in '%s'" % (sNumber, episodeName))
            return sNumber, eNumber

    log.debug("Couldn't identify season and episode number in '%s'" % episodeName)
    raise Exception("Can't find episode")


def getTvShowSeasonInt(tvShowSeason):
    format1 = "(S.)([0-9][0-9])"
    format2 = "(Season )([0-9])(.*)"
    m = re.match(format1, tvShowSeason, flags=re.IGNORECASE)
    if m:
        try:
            return int(m.group(2))
        except ValueError:
            pass
    m = re.match(format2, tvShowSeason, flags=re.IGNORECASE)
    if m:
        try:
            return int(m.group(2) + m.group(3))
        except ValueError:
            pass
    return None


def getSeasonPath(tvShowPath, episodeName):
    try:
        seasonNumber, episodeNumber = getSeasonAndEpisode(episodeName)
    except:
        return None
    log.debug("Search for season dir '%d' in TV Show path '%s'." % (seasonNumber, tvShowPath))
    for tvShowSeason in os.listdir(tvShowPath):
        seasonPath = os.path.join(tvShowPath, tvShowSeason)
        if not os.path.isdir(seasonPath):
            continue
        if not isContainsIdentefier(tvShowSeason, SEASON_FORMATS):
            continue
        if getTvShowSeasonInt(tvShowSeason) is seasonNumber:
            log.debug("Found the correct season '%s'." % seasonPath)
            return seasonPath

    log.debug("Failed to find a folder for season '%d' in '%s'." % (seasonNumber, tvShowPath))
    newSeasonName = getNewSeasonName(seasonNumber)
    log.info("Creating folder '%s' in '%s'." % (newSeasonName, tvShowPath))
    seasonPath = os.path.join(tvShowPath, newSeasonName)
    try:
        os.mkdir(seasonPath)
        return seasonPath
    except Exception, e:
        log.error("Failed to create the folder '%s'. Err: %s" % (seasonPath, str(e)))
        return None


class logger(object):
    def __init__(self, logFilePath, logLevel="INFO"):
        super(logger, self).__init__()
        try:
            self.log = open(logFilePath, "a")
        except Exception, e:
            raise e
        if logLevel.lower() == "debug" or logLevel.lower() == "debugmore":
            self.logLevel = logLevel.upper()
        else:
            self.logLevel = "INFO"

    @staticmethod
    def getTime(humanReadable=True):
        if humanReadable:
            return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        else:
            return time.strftime("%H%M%S", time.localtime())

    def _writeLogLine(self, tag, logLine):
        self.log.write("%s  |%s|\t%s\n" % (logger.getTime(), tag, logLine))
        self.log.flush()

    def info(self, logLine):
        self._writeLogLine("INFO", logLine)

    def debug(self, logLine):
        if "DEBUG" in self.logLevel:
            self._writeLogLine("DEBUG", logLine)

    def debugMore(self, logLine):
        if self.logLevel == "DEBUGMORE":
            self._writeLogLine("DEBUG", logLine)

    def error(self, logLine):
        self._writeLogLine("ERROR", logLine)


if __name__ == "__main__":
    config = ConfigParser.ConfigParser()

    confFileName = "post-proc.conf"
    config.read(os.path.join(os.path.dirname(__file__), confFileName))
    try:
        MOVIE_DIR = config.get('default', 'MOVIE_DIR').strip()
        ORG_DIR = config.get('default', 'ORG_DIR').strip()
        TV_SHOW_DIRS = config.get('default', 'TV_SHOW_DIRS').split(",")
        TV_SHOW_DIRS = [s.strip() for s in TV_SHOW_DIRS]
        DOWNLOAD_DIR = config.get('default', 'DOWNLOAD_DIR').strip()
        LOG = config.get('default', 'LOG').strip()
    except (ConfigParser.NoOptionError, ConfigParser.NoSectionError):
        print "Please fill your configuration file, and locate it next to the script with the name '%s'" % confFileName
        sys.exit(1)

    try:
        LOG_LEVEL = config.get('default', 'LOG_LEVEL').strip()
    except ConfigParser.NoOptionError:
        LOG_LEVEL = "INFO"

    if config.has_option('default', "USE_SEASON_FORMAT"):
        WANTED_SEASON_FORMAT = "Season "
    else:
        WANTED_SEASON_FORMAT = "S."

    DIRS_TO_VERIFY = [MOVIE_DIR, ORG_DIR, DOWNLOAD_DIR]
    # TODO - If the movie dir is unavailable use org  dir instead of existing?

    # Init logger
    log = logger(LOG, LOG_LEVEL)
    main()
