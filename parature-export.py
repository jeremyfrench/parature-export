from restkit import Resource #pip install restkit
import xml.etree.ElementTree as etree
import urllib2
import math
import os
import datetime
import time

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
         elapsed = (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10 ** 6) / 10 ** 6
         if elapsed < min_period:
            wait_time = min_period - elapsed
            time.sleep(wait_time)
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

	@throttle(1)
	def api_get(self, id):
		return self.get(str(id), _token_ = c['API_TOKEN'], _history_ = True)

        @throttle(1)
	def api_list(self, count=False, page=0):
		return self.get(_token_ = c['API_TOKEN'], _total_ = count, _pageSize_ = c['LIST_PAGE_SIZE'], _startPage_ = page, _order_ = "Date_Created_asc_")

        @throttle(1)
	def api_list_count(self):
		doc = self.api_list(True)
		return doc.attrib['total']

	def export(self, start_page = 0):
		resource_type = type(self).__name__

		count = self.api_list_count()
		total_pages = int(math.ceil(int(count) / int(c['LIST_PAGE_SIZE'])))
		print str(count) + " " + resource_type + "(s) with " + str(total_pages) + " total page(s)"

		#Cut the range down by the start page var
		for i in range(total_pages):
			print "Processing page " + str(i)
			list_doc = self.api_list(page = i)

			resource_list = list_doc.findall(resource_type)
			if resource_list != None:
				for resource in resource_list:
					resource_id = resource.attrib['id']
					resource_full = self.api_get(resource_id)

					save_XML(data=pretty(resource_full), subdirectory=resource_type, filename=resource_id)
					save_attachments(resource_full, resource_type + "/" + resource_id)

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
		super(Ticket, self).__init__()

class Csr(Parature):
	def __init__(self, **kwargs):
		self.api_resource_path = "Csr/"
		super(Ticket, self).__init__()

class KnowledgeBase(Parature):
	def __init__(self, **kwargs):
		self.api_resource_path = "Article/"
		super(Ticket, self).__init__()

class Download(Parature):
	def __init__(self, **kwargs):
		self.api_resource_path = "Download/"
		super(Ticket, self).__init__()

if __name__ == "__main__":
	c = get_config('./config')
	#a = Account()
	#a.export()
	t = Ticket()
	t.export()
