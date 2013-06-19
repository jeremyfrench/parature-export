from restkit import Resource  # pip install restkit
from restkit.errors import ResourceError, RequestFailed, RequestError
from urlparse import urlsplit
from BeautifulSoup import BeautifulSoup
import logging
import base64
import xml.etree.ElementTree as etree
import urllib2
import math
import os
import datetime
import time
import re

def get_config(config_path):
	config_vars = dict()

	with open(config_path) as f:
		for line in f:
			eq_index = line.find('=')
			var_name = line[:eq_index].strip()
			value = line[eq_index + 1:].strip()
			config_vars[var_name] = value

	return config_vars	

def set_proc_name(newname):
	from ctypes import cdll, byref, create_string_buffer
	libc = cdll.LoadLibrary('libc.so.6')
	buff = create_string_buffer(len(newname)+1)
	buff.value = newname
	libc.prctl(15, byref(buff), 0, 0, 0)

def throttle(min_period):
	"""Enforces throttling policy, will not call a method two times unless min_period has elapsed"""
	def _throttle(fn):
		calltime = [datetime.datetime.now() - datetime.timedelta(seconds=min_period)]
		def __throttle(*params, **kwargs):
			td = datetime.datetime.now() - calltime[0]
			elapsed = (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10 ** 6) / 10 ** 2
			if elapsed < min_period:
				wait_time = min_period - elapsed
				time.sleep(wait_time / 1000)
			rv = fn(*params, **kwargs)
			calltime[0] = datetime.datetime.now()
			return rv
		return __throttle
	return _throttle

def pretty(etree_root):
	return etree.tostring(etree_root)

def url2name(url):
	return os.path.basename(urlsplit(url)[2])

def save(file_data, filename, path = None, log_type = "I/O"):
	if path:
		if not os.path.exists(path):
			os.makedirs(path)
			
	filename = str(path) + filename
	
	logging.info(log_type + ": Saving " + filename)

	try:
		f = open(filename, 'wb')
		f.write(file_data)
		f.close()
	except IOError as e:
		logging.error(log_type + ": Error number {0}: {1}".format(e.errno, e.strerror))

def download(url, filename_override = None, path = None):
	filename = url2name(url)
	req = urllib2.Request(url)
	req.add_header('Referer', c['DOWNLOAD_REFERER'])
	r = urllib2.urlopen(req)
	if r.info().has_key('Content-Disposition'):
		cd = dict(map(
			lambda x: x.strip().split('=') if '=' in x else (x.strip(),''),
			r.info()['Content-Disposition'].split(';')))
		if 'filename' in cd:
			filename = cd['filename'].strip("\"'")
	elif r.url != url: 
		# if we were redirected, the real file name we take from the final URL
		filename = url2name(r.url)
	if filename_override: 
		# we can force to save the file as specified name
		filename = filename_override

	save(r.read(), filename, path, "Binary")

class Parature(Resource):
	def __init__(self, **kwargs):
		self.api_url = c['PARATURE_URL'] + "/" + c['API_ACCOUNT_ID'] + "/" + c['API_DEPARTMENT_ID'] + "/" + self.api_resource_path
		super(Parature, self).__init__(self.api_url, follow_redirect=True, max_follow_redirect=10, **kwargs)

	def request(self, *args, **kwargs):
		response = super(Parature, self).request(*args, **kwargs)
		root = etree.fromstring(response.body_string())
		return root

	@throttle(600)
	def api_get(self, id):
		return self.get(str(id), _token_=c['API_TOKEN'], _history_=True)

	@throttle(600)
	def api_list(self, count=False, page=0):
		return self.get(_token_=c['API_TOKEN'], _total_=count, _pageSize_=c['LIST_PAGE_SIZE'], _startPage_=page, _order_="Date_Created_asc_", Date_Updated_min_=c['DATE_UPDATED_MIN'])

	@throttle(600)
	def api_list_count(self):
		doc = self.api_list(True)
		return doc.attrib['total']

	def extract_binaries(self, resource, subdirectory):

		path = "./" + c['JOB_ID'] + "/" + subdirectory + "/" 

		try:
			item_list = []
			item_list = self.get_download_items(resource, item_list, path)
		except AttributeError:
			#Using the EAFP method to create get_download_items hook
			pass

		for item in item_list:
			
			try:
				download(item['url'], item['filename'], path)	
			except urllib2.HTTPError, e:
				logging.error("HTTP: \"" + str(e) + "\" reported on downloading " + str(item['url']) + " from object ID " + str(resource.attrib['id']))
			except:
				logging.error("HTTP: Unknown error downloading " + str(item['url']) + " from object ID " + str(resource.attrib['id']))

	def extract_XML(self, data, subdirectory, filename):
		filename = filename + ".xml"
		path = "./" + c['JOB_ID'] + "/" + subdirectory + "/"
		save(data, filename, path, "Data resource")

	def get_resource_data_and_binaries(self, id, type):
		try:
			self.pre_retrieve(id)
		except AttributeError:
			#Using the EAFP method to create pre_retrieve hook
			pass

		resource = self.api_get(id)						
		self.extract_XML(data=pretty(resource), subdirectory=type, filename=id)
		self.extract_binaries(resource, type + "/" + id)

		try:
			self.post_retrieve(id, resource)
		except AttributeError:
			#Using the EAFP method to create post_retrieve hook
			pass

	def export(self, start_page=1):

		if start_page == 0:
			start_page = 1

		resource_type = type(self).__name__

		count = self.api_list_count()
		total_pages = int(math.ceil(int(count) / float(c['LIST_PAGE_SIZE'])))
		
		logging.info("Processing: " + str(count) + " " + resource_type + "(s) with " + str(total_pages) + " total page(s)")
		page_start = start_page
		skip = 0
		# Check for exsisting items
		dir_path = "./" + c['JOB_ID'] + "/" + resource_type + "/"
		if os.path.exists(dir_path):
			files = [f for f in os.listdir(dir_path) if re.match(r'.*\.xml', f)]
			done_file_count = len(files)
			if (done_file_count == count) :
				logging.info("Processing: All of this type done, skipping")
				return
			else:
				logging.info("Processing: Previous export identified, restarting from last position")
				done_page = int(math.floor(done_file_count / float(c['LIST_PAGE_SIZE']))) + 1
				list_doc = self.api_list(page=done_page)
				resource_list = list_doc.findall(resource_type)
				offset = done_file_count % int(c['LIST_PAGE_SIZE'])
				last_resource = resource_list[offset-1]
				#check that the last resource is as expected.
				if os.path.exists(dir_path + last_resource.attrib['id'] + '.xml'): 
					next_resource = resource_list[offset]
					if not os.path.exists(dir_path + next_resource.attrib['id'] + '.xml'): 
						#set the start page and offset so they can pick up where we left off
						page_start = int(done_page)
						skip = offset
						
		# Cut the range down by the start page var
		for i in range(page_start,total_pages+1):

			logging.info("Processing: " + resource_type + " page " + str(i))
			list_doc = self.api_list(page=i)
			resource_list = list_doc.findall(resource_type)
			
			if resource_list != None:
				#Skip items if set
				resource_list = resource_list[skip:]
				#reset skip for subsequent pages
				skip = 0
				for resource in resource_list:
					resource_id = resource.attrib['id']
					
					logging.info("API: Getting " + resource_type + " ID " + str(resource_id))

					try:
						self.get_resource_data_and_binaries(resource_id, resource_type)
					except Exception as e:
						logging.error("API: Unknown error getting {0} {1}, message provided: {2}".format(resource_id, resource_type, e))						

class Account(Parature):
	def __init__(self, **kwargs):
		self.api_resource_path = "Account/"
		super(Account, self).__init__()

class Ticket(Parature):
	def __init__(self, **kwargs):
		self.api_resource_path = "Ticket/"
		super(Ticket, self).__init__()

	def get_download_items(self, resource, item_list, path):
		#Ticket style attachments
		attachment_list = resource.findall(".//Attachment")
		for attachment in attachment_list:
			item_list.append({'filename': attachment.find('Name').text, 'url': attachment.attrib['href']})

		return item_list			

class Customer(Parature):
	def __init__(self, **kwargs):
		self.api_resource_path = "Customer/"
		super(Customer, self).__init__()

class Csr(Parature):
	def __init__(self, **kwargs):
		self.api_resource_path = "Csr/"
		super(Csr, self).__init__()

	#CSR objects don't have the date updated field unlike every other object, so we'll override the list method to not try and use it
	@throttle(600)
	def api_list(self, count=False, page=0):
		return self.get(_token_=c['API_TOKEN'], _total_=count, _pageSize_=c['LIST_PAGE_SIZE'], _startPage_=page, _order_="Date_Created_asc_")

class Article(Parature):
	def __init__(self, **kwargs):
		self.api_resource_path = "Article/"
		super(Article, self).__init__()

	def get_download_items(self, resource, item_list, path):
		#Images in articles
		try:
			image_list = BeautifulSoup(resource.find("./Answer").text).findAll('img')
		except:
			image_list = []

		for image in image_list:
			url = image['src']

			if url.startswith('data:'):
				filetype = "." + url[url.find("/")+1:url.find(";")]
				base64_string = url.split("base64,")[1]
				filename = "embedded_" + base64_string[:30] + filetype

				save(base64.decodestring(base64_string), filename, path, "Binary")
			else:
				item_list.append({'filename': None, 'url': url})	

		return item_list

class Download(Parature):
	def __init__(self, **kwargs):
		self.visibility_toggled = []
		self.api_resource_path = "Download/"
		super(Download, self).__init__()

	@throttle(600)
	def pre_retrieve(self, id):
		#Ensure download object is made visible so an external link is presented in the resource
		resource = self.api_get(id)

		try:
			if not resource.find("./External_Link").text:
				resource.find("./Visible").text = 'true'
				resource.remove(resource.find("./Ext"))
				self.put(str(resource.attrib['id']), pretty(resource), _token_=c['API_TOKEN'])
				logging.info("Download object: ID {0} - External link visibility set to true".format(resource.attrib['id']))
				self.visibility_toggled.append({'id': resource.attrib['id'], 'resource': resource})
		except Exception as e:
			logging.error("Download object: ID {0} - No existing external link but couldn't enable the external link either. Message: {1}".format(resource.attrib['id'], e))

		return resource

	def get_download_items(self, resource, item_list, path):
		#Files on Download objects
		try:
			item_list.append({'filename': None, 'url': resource.find('External_Link').text})
		except:
			logging.info("Download: ID {0} has no external link".format(str(resource.attrib['id'])))
		
		return item_list

	def post_retrieve(self, id, resource):
		for item in self.visibility_toggled[:]:
			try:
				item['resource'].find("./Visible").text = 'false'
				self.put(str(item['id']), pretty(item['resource']), _token_=c['API_TOKEN'])
				logging.info("Download object: ID {0} - External link visibility switched back to false".format(resource.attrib['id']))
			except:
				logging.error("Download object: ID {0} - Couldn't restore visibility state - link left visible".format(resource.attrib['id']))
			self.visibility_toggled.remove(item)

if __name__ == "__main__":
	
	set_proc_name("parature-export")

	start_timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%S")

	c = get_config('./config')
	logging.basicConfig(filename= start_timestamp + "-" + c['LOG_FILE'], format= c['LOG_FORMAT'], datefmt= c['LOG_DATE_FORMAT'], level= int(c['LOG_LEVEL']))

	logging.info("START: Job starting, config loaded")

	logging.info("Processing: Extracting Downloads")
	d = Download()
	d.export()

	logging.info("Processing: Extracting CSRs")
	csr = Csr()
	csr.export()

	logging.info("Processing: Extracting Articles")
	ar = Article()
	ar.export()	

	logging.info("Processing: Extracting Customers")
	cust = Customer()
	cust.export()

	logging.info("Processing: Extracting Accounts")
	a = Account()
	a.export()

	logging.info("Processing: Extracting Tickets")
	t = Ticket()
	t.export()

	logging.info("FINISH: Job complete")

	#TODO: If article image download redirects to non-image, don't download, raise error
	#TODO: Add 3 retries for HTTP errors that aren't 404 or 400