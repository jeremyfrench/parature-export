import requests
import cgi


class parature_browser(object):
    def __init__(self,config):
        self.config = config
        
        self.session = requests.Session()
        #Login to server on init
        payload = {}
        payload['email'] = self.config['PARATURE_EMAIL']
        payload['password'] = self.config['PARATURE_PASSWORD']
        self.session.post(self.config['PARATURE_WEB_URL'] + '/ics/service/loginSQL.asp', data = payload) 
        
    def getPage(self, path):
        path = 'https://s5.parature.com' + path
        response = self.session.get(path)
        #TODO: some error checking and thowing. 
        return response.text
    
    def getFile(self, url_path):
        path = self.config['PARATURE_WEB_URL'] + url_path
        response = self.session.get(path, allow_redirects=True)
        _, params = cgi.parse_header(response.headers.get('Content-Disposition', ''))
        filename = params['filename*'].replace("UTF-8''",'')
        return response.content, filename
            
        
    
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
    