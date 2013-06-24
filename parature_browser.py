import requests
import cgi
import os

class parature_browser(object):
    def __init__(self,config):
        self.config = config
        
        self.session = requests.Session()
        #Login to server on init
        payload = {}
        payload['email'] = self.config['PARATURE_EMAIL']
        payload['password'] = self.config['PARATURE_PASSWORD']
        #TODO: config for this 
        x = self.session.post('https://s5.parature.com/ics/service/loginSQL.asp', data = payload) 
        
    def getPage(self, path):
        path = 'https://s5.parature.com' + path
        response = self.session.get(path)
        #TODO: some error checking and thowing. 
        return response.text
    
    def saveFile(self, url_path, file_path):
        path = 'https://s5.parature.com' + url_path
            
        response = self.session.get(path, allow_redirects=True, stream=True)
        _, params = cgi.parse_header(response.headers.get('Content-Disposition', ''))
        filename = params['filename*'].replace("UTF-8''",'')
        if not os.path.exists(file_path):
            os.makedirs(file_path)
        handle = open(file_path + filename, "wb")
        for block in response.iter_content(1024):
            if not block:
                break
            handle.write(block)
            
        
    
#Just for debug / Testing   
if __name__ == "__main__":
    config_vars = dict()

    with open('./config') as f:
        for line in f:
            eq_index = line.find('=')
            var_name = line[:eq_index].strip()
            value = line[eq_index + 1:].strip()
            config_vars[var_name] = value

    pb = parature_browser(config_vars)   
    
    
    print pb.getPage('/ics/km/kmFileList.asp?questionID=60') 
    
    pb.saveFile('/ics/dm/DLRedirect.asp?fileID=37842', '')