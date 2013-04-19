from restkit import Resource  # pip install restkit
from restkit.errors import ResourceError, RequestFailed, RequestError 
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

def save_attachments(resource, subdirectory):

	file_path = "./" + c['JOB_ID'] + "/" + subdirectory + "/" 

	attachment_list = resource.findall(".//Attachment")

	if attachment_list and not os.path.exists(os.path.dirname(file_path)):
		os.makedirs(os.path.dirname(file_path))

	for attachment in attachment_list:

		url = attachment.attrib['href']
		filename = file_path + attachment.find('Name').text

		data_file = open(filename, 'w')
		response = urllib2.urlopen(url)
		data_file.write(response.read())
		data_file.close()

def save_XML(data, subdirectory, filename):
	file_path = "./" + c['JOB_ID'] + "/" + subdirectory + "/" + filename + ".xml"
	print filename
	if not os.path.exists(os.path.dirname(file_path)):
	    os.makedirs(os.path.dirname(file_path))

	data_file = open(file_path, 'w')
	data_file.write(data)
	data_file.close()

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
		return self.get(_token_=c['API_TOKEN'], _total_=count, _pageSize_=c['LIST_PAGE_SIZE'], _startPage_=page, _order_="Date_Created_asc_")

	@throttle(600)
	def api_list_count(self):
		doc = self.api_list(True)
		return doc.attrib['total']

	def export(self, start_page=0):
		resource_type = type(self).__name__

		count = self.api_list_count()
		total_pages = int(math.ceil(int(count) / int(c['LIST_PAGE_SIZE'])))
		
		print str(count) + " " + resource_type + "(s) with " + str(total_pages) + " total page(s)"
		page_start = 1
		skip = 0
		# Check for exsisting items
		dir_path = "./" + c['JOB_ID'] + "/" + resource_type + "/"
		if os.path.exists(dir_path):
			files = [f for f in os.listdir(dir_path) if re.match(r'.*\.xml', f)]
			done_file_count = len(files)
			if (done_file_count == count) :
				print "All of this type done, skipping"
				return
			else:
				print "looks like an export ran before, picking up where we left off"
				done_page = math.floor(done_file_count / int(c['LIST_PAGE_SIZE'])) + 1
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
		for i in range(page_start,total_pages):
			print "Processing page " + str(i)
			list_doc = self.api_list(page=i)
			print len(list_doc)
			resource_list = list_doc.findall(resource_type)
			
			if resource_list != None:
				#Skip items if set
				resource_list = resource_list[skip:]
				#reset skip for subsequent pages
				skip = 0
				for resource in resource_list:
					resource_id = resource.attrib['id']
					try:
						resource_full = self.api_get(resource_id)
						save_XML(data=pretty(resource_full), subdirectory=resource_type, filename=resource_id)
						save_attachments(resource_full, resource_type + "/" + resource_id)
					except ResourceError:
						print 'Error getting resource ' + resource_id
class Account(Parature):
	def __init__(self, **kwargs):
		self.api_resource_path = "Account/"
		super(Account, self).__init__()

class Ticket(Parature):
	def __init__(self, **kwargs):
		self.api_resource_path = "Ticket/"
		super(Ticket, self).__init__()

class Customer(Parature):
	def __init__(self, **kwargs):
		self.api_resource_path = "Customer/"
		super(Customer, self).__init__()

class Csr(Parature):
	def __init__(self, **kwargs):
		self.api_resource_path = "Csr/"
		super(Csr, self).__init__()

class Article(Parature):
	def __init__(self, **kwargs):
		self.api_resource_path = "Article/"
		super(Article, self).__init__()

class Download(Parature):
	def __init__(self, **kwargs):
		self.api_resource_path = "Download/"
		super(Download, self).__init__()

if __name__ == "__main__":
	c = get_config('./config')
	a = Account()
	a.export()

	t = Ticket()
	t.export()

	a = Account()
	a.export()

	csr = Csr()
	csr.export()

	d = Download()
	d.export()

	ar = Article()
	ar.export()

	cust = Customer()
	cust.export()
