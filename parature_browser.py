import requests

class parature_browser(object):
    def __init__(self,config):
        self.config = config
        
        self.session = requests.Session()
        #Login to server on init
        payload = {}
        payload['email'] = self.config['PARATURE_EMAIL']
        payload['password'] = self.config['PARATURE_PASSWORD']
        #TODO: config for this 
        x = self.session.post('https://s5-sandbox.parature.com/ics/service/loginSQL.asp', data = payload) 
        
    def getPage(self, path):
        path = 'https://s5-sandbox.parature.com/' + path
        response = self.session.get(path)
        #TODO: some error checking and thowing. 
        return response.text
    
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
    
    print pb.getPage('ics/km/kmFileList.asp?questionID=1') 
    