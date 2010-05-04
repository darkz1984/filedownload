import os
import urllib2
import sys
import re
import base64
from urlparse import urlparse

class DownloadFile(object):
	"""Downloads files from http or ftp locations"""
	def __init__(self, url, localFileName=None, auth=None):
		self.url = url
		self.urlFileName = None
		self.progress = None
		self.localFileName = localFileName
		self.type = self.getType()
		self.auth = auth
		if not self.localFileName:
			self.localFileName = self.getUrlFilename(self.url)
		
	def downloadFile(self, urlObj, fileObj):
		chunk = 1024
		while 1:
			data = urlObj.read(chunk)
			if not data:
	            #print "done."
				fileObj.close()
				break
			fileObj.write(data)
			print "Read %s bytes"%len(data)
        
	def getUrlFilename(self, url):
		"""finds out the filename from an url"""
		return os.path.basename(url)
		
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
		"""figures out if self.url is http or ftp"""
		type = self.url.split('://')
		print type[0]
		return type[0]
		
	def startResume(self, restart=None):
		"""starts to resume by getting the local filesize and calling downloadFile"""
		if restart:
			f = open(self.localFileName , "wb")
		else:
			f = open(self.localFileName , "ab")
		if self.auth:
			self.authHttp()
		#to resume ftp probably have to subClass ftpHandler or just user ftplib
		req = urllib2.Request(self.url)
		req.headers['Range'] = 'bytes=%s-%s' % (self.getLocalFileSize(), self.getUrlFileSize())
		urllib2Obj = urllib2.urlopen(req)
		self.downloadFile(urllib2Obj, f)

	def startNormal(self):
		"""starts the file download normally"""
		f = open(self.localFileName , "wb")
		if self.auth:
			if self.type == 'http':
				authObj = self.authHttp()
				self.downloadFile(authObj, f)
			elif self.type == 'ftp':
				authObj = self.authFtp()
				self.downloadFile(authObj, f)
		else:
			urllib2Obj = urllib2.urlopen(self.url)
			self.downloadFile(urllib2Obj, f)

	def authHttp(self):
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
		
	def authFtp(self):
		"""handles ftp authentication"""
		ftped = urllib2.FTPHandler()
		ftpUrl = self.url.replace('ftp://', '')
		req = urllib2.Request("ftp://%s:%s@%s"%(self.auth[0], self.auth[1], ftpUrl))
		print "ftp://%s:%s@%s"%(self.auth[0], self.auth[1], self.url)
		req.timeout = 120
		ftpObj = ftped.ftp_open(req)
		return ftpObj

downloader = DownloadFile('ftp://64.61.186.98:2695/trailers/Emerging_Pictures_Logo.wmv', auth=('catalogftp', 'hGwDo5i2'))
downloader.startNormal()
#downloader.startResume()
#urlretrieve("ftp://ftp.gimp.org/pub/gimp/v2.6/patch-2.6.5.bz2")