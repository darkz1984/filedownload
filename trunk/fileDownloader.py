"""Downloads files from http or ftp locations"""
import os
import urllib2
import sys
import re
import ftplib
import urlparse
import urllib

class DownloadFile(object):
	"""This class is used for downloading files from the internet via http or ftp.
	If supports basic http authentication and ftp accounts, and supports resuming downloads. 
	It does not support https or sftp.
	
	The main advantage of this class is it's ease of use, and pure pythoness, no C to compile.
	
	If a non-standard port is needed just include it in the url (http://example.com:7632).
	
	Basic usage:
		Simple
			downloader = fileDownloader.DownloadFile('http://example.com/file.zip')
			downloader.download()
	 	Use full path to download
	 		downloader = fileDownloader.DownloadFile('http://example.com/file.zip', "C:\\Users\\bantonj\\Downloads\\newfilename.zip")
	 		downloader.download()
	 	Password protected download
	 		downloader = fileDownloader.DownloadFile('http://example.com/file.zip', "C:\\Users\\bantonj\\Downloads\\newfilename.zip", ('jimmy','JHuyi5'))
	 		downloader.download()
	 	Resume
	 		downloader = fileDownloader.DownloadFile('http://example.com/file.zip')
			downloader.resume()
	"""        
	
	def __init__(self, url, localFileName=None, auth=None):
		"""Note that auth argument expects a tuple, ('username','password')"""
		self.url = url
		self.urlFileName = None
		self.progress = None
		self.localFileName = localFileName
		self.type = self.getType()
		self.auth = auth
		#if no filename given pulls filename from the url
		if not self.localFileName:
			self.localFileName = self.getUrlFilename(self.url)
		
	def __downloadFile__(self, urlObj, fileObj):
		"""starts the download loop"""
		chunk = 1024
		while 1:
			data = urlObj.read(chunk)
			if not data:
	            #print "done."
				fileObj.close()
				break
			fileObj.write(data)
			print "Read %s bytes"%len(data)
        
	def __authHttp__(self):
		"""handles http basic authentication"""
		passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
		# this creates a password manager
		passman.add_password(None, self.url, self.auth[0], self.auth[1])
		# because we have put None at the start it will always
		# use this username/password combination for  urls
		# for which `theurl` is a super-url
		
		authhandler = urllib2.HTTPBasicAuthHandler(passman)
		# create the AuthHandler
		
		opener = urllib2.build_opener(authhandler)
		
		urllib2.install_opener(opener)
		# All calls to urllib2.urlopen will now use our handler
		# Make sure not to include the protocol in with the URL, or
		# HTTPPasswordMgrWithDefaultRealm will be very confused.
		# You must (of course) use it when fetching the page though.
		
		pagehandle = urllib2.urlopen(self.url)
		# authentication is now handled automatically for us
		#print pagehandle.read()
		return pagehandle
		
	def __authFtp__(self):
		"""handles ftp authentication"""
		ftped = urllib2.FTPHandler()
		ftpUrl = self.url.replace('ftp://', '')
		req = urllib2.Request("ftp://%s:%s@%s"%(self.auth[0], self.auth[1], ftpUrl))
		print "ftp://%s:%s@%s"%(self.auth[0], self.auth[1], self.url)
		req.timeout = 120
		ftpObj = ftped.ftp_open(req)
		return ftpObj
        
	def __startHttpResume__(self, restart=None):
		"""starts to resume HTTP"""
		if restart:
			f = open(self.localFileName , "wb")
		else:
			f = open(self.localFileName , "ab")
		if self.auth:
			self.__authHttp__()
		#to resume ftp probably have to subClass ftpHandler or just user ftplib
		req = urllib2.Request(self.url)
		req.headers['Range'] = 'bytes=%s-%s' % (self.getLocalFileSize(), self.getUrlFileSize())
		urllib2Obj = urllib2.urlopen(req)
		self.__downloadFile__(urllib2Obj, f)

	def __startFtpResume__(self, restart=None):
		"""starts to resume FTP"""
		ftper = ftplib.FTP()
		parseObj = urlparse.urlparse(self.url)
		baseUrl= parseObj.hostname
		urlPort = parseObj.port
		bPath = os.path.basename(parseObj.path)
		gPath = parseObj.path.replace(bPath, "")
		unEncgPath = urllib.unquote(gPath)
		fileName = urllib.unquote(os.path.basename(self.url))
		ftper.connect(baseUrl, urlPort)
		ftper.login(self.auth[0], self.auth[1])
		print gPath
		if len(gPath) > 1:
			ftper.cwd(unEncgPath)
		ftper.sendcmd("TYPE I")
		ftper.sendcmd("REST " + str(self.getLocalFileSize()))
		downCmd = "RETR "+ fileName
		print downCmd
		ftper.retrbinary(downCmd, open(fileName, 'ab').write)
        
	def getUrlFilename(self, url):
		"""returns filename from url"""
		return urllib.unquote(os.path.basename(url))
		
	def getUrlFileSize(self):
		"""gets filesize of remote file from ftp or http server"""
		if self.type == 'http':
			urllib2Obj = urllib2.urlopen(self.url)
			return urllib2Obj.headers.get('content-length')
		
	def getLocalFileSize(self):
		"""gets filesize of local file"""
		size = os.stat(self.localFileName).st_size
		return size
		
	def getType(self):
		"""returns protocol of url (ftp or http)"""
		type = urlparse.urlparse(self.url).scheme
		return type	

	def download(self):
		"""starts the file download"""
		f = open(self.localFileName , "wb")
		if self.auth:
			if self.type == 'http':
				authObj = self.__authHttp__()
				self.__downloadFile__(authObj, f)
			elif self.type == 'ftp':
				self.url = self.url.replace('ftp://', '')
				authObj = self.__authFtp__()
				self.__downloadFile__(authObj, f)
		else:
			urllib2Obj = urllib2.urlopen(self.url)
			self.__downloadFile__(urllib2Obj, f)

	def resume(self):
		"""attempts to resume file download"""
		type = self.getType()
		if type == 'http':
			self.__startHttpResume__()
		elif type == 'ftp':
			self.__startFtpResume__()
