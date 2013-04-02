from restkit import Resource #pip install restkit
from lxml import etree #apt-get install libxml2-dev libxslt-dev & pip install lxml
import urllib2
import math
import os

PARATURE_URL = "https://s5.parature.com/api/v1/"
API_TOKEN = ""
API_ACCOUNT_ID = "00000"
API_DEPARTMENT_ID = "00000"
LIST_PAGE_SIZE = 500
JOB_ID = "subdirectory-to-output-results-to"

def pretty(etree_root):
	return etree.tostring(etree_root, pretty_print=True)

def save_attachments(resource, subdirectory):

	attachment_list = resource.findall("Attachment")
	if attachment_list != None:
		for attachment in attachment_list:
			#This bit isn't doing anything - find ticketattachment then loop through attachments
			url = attachment.attrib['href']
			print url
	exit(-1)

	url = ""
	file_path = "./" + JOB_ID + "/" + subdirectory + "/" + filename
	
	if not os.path.exists(os.path.dirname(file_path)):
	    os.makedirs(os.path.dirname(file_path))

	data_file = open(file_path, 'w')
	response = urllib2.urlopen(url)
	data_file.write(response.read())
	data_file.close()

def save_XML(data, subdirectory, filename):
	file_path = "./" + JOB_ID + "/" + subdirectory + "/" + filename + ".xml"
	
	if not os.path.exists(os.path.dirname(file_path)):
	    os.makedirs(os.path.dirname(file_path))

	data_file = open(file_path, 'w')
	data_file.write(data)
	data_file.close()

class Parature(Resource):
	def __init__(self, **kwargs):
		self.api_url = PARATURE_URL + "/" + API_ACCOUNT_ID + "/" + API_DEPARTMENT_ID + "/" + self.api_resource_path
		super(Parature, self).__init__(self.api_url, follow_redirect=True, max_follow_redirect=10, **kwargs)

	def request(self, *args, **kwargs):
		response = super(Parature, self).request(*args, **kwargs)
		root = etree.fromstring(response.body_string())
		return root

	def api_get(self, id):
		return self.get(str(id), _token_ = API_TOKEN, _history_ = True)

	def api_list(self, count=False, page=0):
		return self.get(_token_ = API_TOKEN, _total_ = count, _pageSize_ = LIST_PAGE_SIZE, _startPage_ = page, _order_ = "Date_Created_asc_")

	def api_list_count(self):
		doc = self.api_list(True)
		return doc.attrib['total']

	def export(self, start_page = 0):
		resource_type = type(self).__name__

		count = self.api_list_count()
		total_pages = int(math.ceil(int(count) / LIST_PAGE_SIZE))
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

					save_XML(data=pretty(resource_full), subdirectory=resource_type, filename=object_id)

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
	
	a = Account()
	a.export()
	#t = Ticket()
	#t.export()