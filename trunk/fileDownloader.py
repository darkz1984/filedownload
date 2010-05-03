import os
import sys
import urllib2

class DownloadFile(object):
	"""Downloads files from http or ftp locations"""
	def __init__(self, url, localFileName=None):
		self.url = url
		self.urlFileName = None
		self.progress = None
		self.localFileName = localFileName
		self.type = self.getType()
		
	def downloadFile(self, resume=None):
		chunk = 1024
		if not self.localFileName:
			self.localFileName = self.getUrlFilename(self.url)
		if resume:
		    if resume != 'restart':
		    	f = open(self.localFileName , "ab")
		    	urllib2Obj = urllib2.urlopen(resume)
		    else:
		    	f = open(self.localFileName , "wb")
		    	urllib2Obj = urllib2.urlopen(self.url)
		else:
			f = open(self.localFileName , "wb")
			urllib2Obj = urllib2.urlopen(self.url)
		while 1:
			data = urllib2Obj.read(chunk)
			if not data:
	            #print "done."
				f.close()
				break
			f.write(data)
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
		
	def startResume(self):
		"""starts to resume by getting the local filesize and calling downloadFile"""
		if not self.localFileName:
			self.localFileName = self.getUrlFilename(self.url)
		req = urllib2.Request(self.url)
		req.headers['Range'] = 'bytes=%s-%s' % (self.getLocalFileSize()+1, self.getUrlFileSize())
		self.downloadFile(req)


downloader = DownloadFile('http://download.thinkbroadband.com/5MB.zip')
downloader.downloadFile()
#downloader.startResume()
#urlretrieve("ftp://ftp.gimp.org/pub/gimp/v2.6/patch-2.6.5.bz2")