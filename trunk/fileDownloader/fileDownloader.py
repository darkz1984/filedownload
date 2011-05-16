"""Downloads files from http or ftp locations"""
import os
import urllib2
import sys
import re
import ftplib
import urlparse
import urllib
import socket
import sys

version = "0.3.0"

class DownloadFile(object):
	"""This class is used for downloading files from the internet via http or ftp.
	It supports basic http authentication and ftp accounts, and supports resuming downloads. 
	It does not support https or sftp at this time.
	
	The main advantage of this class is it's ease of use, and pure pythoness. It only uses the Python standard library, 
	so no dependencies to deal with, and no C to compile.
	
	#####
	If a non-standard port is needed just include it in the url (http://example.com:7632).
	
	Basic usage:
		Simple
			downloader = fileDownloader.DownloadFile('http://example.com/file.zip')
			downloader.download()
	 	Use full path to download
	 		downloader = fileDownloader.DownloadFile('http://example.com/file.zip', "C:\\Users\\username\\Downloads\\newfilename.zip")
	 		downloader.download()
	 	Password protected download
	 		downloader = fileDownloader.DownloadFile('http://example.com/file.zip', "C:\\Users\\username\\Downloads\\newfilename.zip", ('username','password'))
	 		downloader.download()
	 	Resume
	 		downloader = fileDownloader.DownloadFile('http://example.com/file.zip')
			downloader.resume()
	"""        
	
	def __init__(self, url, q=None, localFileName=None, auth=None, timeout=120.0, autoretry=False, retries=10):
		"""Note that auth argument expects a tuple, ('username','password')"""
		self.url = url
		self.queue = q
		self.urlFileName = None
		self.progress = 0
		self.fileSize = None
		print localFileName
		self.localFileName = localFileName
		self.type = self.getType()
		self.auth = auth
		self.timeout = timeout
		self.autoretry = autoretry
		self.retries = retries
		self.curretry = None
		self.cur = 0
		#if no filename given pulls filename from the url
		if not self.localFileName:
			self.localFileName = self.getUrlFilename(self.url)
		
	def __downloadFile__(self, urlObj, fileObj, callBack=None, args=None):
		"""starts the download loop"""
		self.fileSize = self.getUrlFileSize()
		chunk = 8192
		while 1:
			try:
				data = urlObj.read(chunk)
			except socket.timeout:
				if self.autoretry:
					self.__retry__()
			if not data:
				print "done."
				fileObj.close()
				if self.queue:
					self.queue.put('done')
				break
			fileObj.write(data)
			self.cur = self.cur + 8192
			self.progress = (self.cur*100)/int(self.fileSize)
			if self.queue:
				self.queue.put([self.progress, self.cur, self.fileSize, args])
			if callBack:
				callBack([self.progress, self.cur, self.fileSize], args)
			
		if self.autoretry:
			self.__retry__()
      
	def __retry__(self):
		"""auto-resumes up to self.retries"""
		if self.retries > self.curretry:
				self.curretry += 1
				if self.getLocalFileSize() != self.urlFilesize:
					self.resume()
					
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
		
		#pagehandle = urllib2.urlopen(self.url, timeout=self.timeout)
		# authentication is now handled automatically for us
		#print pagehandle.read()
		#return pagehandle
		
	def __authFtp__(self):
		"""handles ftp authentication"""
		ftped = urllib2.FTPHandler()
		ftpUrl = self.url.replace('ftp://', '')
		req = urllib2.Request("ftp://%s:%s@%s"%(self.auth[0], self.auth[1], ftpUrl))
		#print "ftp://%s:%s@%s"%(self.auth[0], self.auth[1], self.url)
		req.timeout = 120
		ftpObj = ftped.ftp_open(req)
		return ftpObj
        
	def __startHttpResume__(self, restart=None, callBack=None):
		"""starts to resume HTTP"""
		curSize = self.getLocalFileSize()
		self.cur = curSize
		if restart:
			f = open(self.localFileName , "wb")
		else:
			f = open(self.localFileName , "ab")
		if self.auth:
			self.__authHttp__()
		req = urllib2.Request(self.url)
		req.headers['Range'] = 'bytes=%s-%s' % (curSize, self.getUrlFileSize())
		urllib2Obj = urllib2.urlopen(req)
		self.__downloadFile__(urllib2Obj, f, callBack=callBack)

	def __startFtpResume__(self, restart=None):
		"""starts to resume FTP"""
		if restart:
			f = open(self.localFileName , "wb")
		else:
			f = open(self.localFileName , "ab")
		ftper = ftplib.FTP(timeout=60)
		parseObj = urlparse.urlparse(self.url)
		baseUrl= parseObj.hostname
		urlPort = parseObj.port
		bPath = os.path.basename(parseObj.path)
		gPath = parseObj.path.replace(bPath, "")
		unEncgPath = urllib.unquote(gPath)
		fileName = urllib.unquote(os.path.basename(self.url))
		ftper.connect(baseUrl, urlPort)
		ftper.login(self.auth[0], self.auth[1])
		#print gPath
		if len(gPath) > 1:
			ftper.cwd(unEncgPath)
		ftper.sendcmd("TYPE I")
		ftper.sendcmd("REST " + str(self.getLocalFileSize()))
		downCmd = "RETR "+ fileName
		#print downCmd
		try:
			ftper.retrbinary(downCmd, f.write)
		except socket.error:
			if self.autoretry:
				self.resume()
		
        
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
        
	def checkExists(self):
		if self.auth:
			if self.type == 'http':
				authObj = self.__authHttp__()
				try:
					urllib2.urlopen(self.url)
				except urllib2.HTTPError:
					return False
				return True
			elif self.type == 'ftp':
				return "not yet supported"
		else:
			urllib2Obj = urllib2.urlopen(self.url, timeout=self.timeout)
			try:
				urllib2.urlopen(self.url)
			except urllib2.HTTPError:
				return False
			return True

	def download(self, callBack=None, aRgs=None):
		"""starts the file download"""
		#set socket timeout
		# timeout in seconds
		socket.setdefaulttimeout(self.timeout)
		print self.localFileName
		f = open(self.localFileName , "wb")
		if self.auth:
			if self.type == 'http':
				self.__authHttp__()
				urllib2Obj = urllib2.urlopen(self.url, timeout=self.timeout)
				self.__downloadFile__(urllib2Obj, f, callBack=callBack, args=aRgs)
			elif self.type == 'ftp':
				self.url = self.url.replace('ftp://', '')
				authObj = self.__authFtp__()
				self.__downloadFile__(authObj, f, callBack=callBack, args=aRgs)
		else:
			urllib2Obj = urllib2.urlopen(self.url, timeout=self.timeout)
			self.__downloadFile__(urllib2Obj, f, callBack=callBack)

	def resume(self, callBack=None):
		"""attempts to resume file download"""
		type = self.getType()
		if type == 'http':
			self.__startHttpResume__(callBack=callBack)
		elif type == 'ftp':
			self.__startFtpResume__()
