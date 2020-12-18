import json, os, requests, time, copy
from dateutil.parser import parse

class Storage(object):
    def __init__(self, fingerprint):
        self.filename = 'data.json'

        self.ip_address = str(requests.get('https://checkip.amazonaws.com').text.strip())

        self.fingerprint = fingerprint

        self.maxperday = 1211
        self.maxperhour = 192

        self.schema = {}
        self.schema['_ip'] = {}
        self.schema['_ip']['sum'] = 0
        self.schema['_ip']['fingerprints'] = {}
        self.schema['_fingerprint'] = {}
        self.schema['_fingerprint']['first'] = time.ctime()
        self.schema['_fingerprint']['pixels'] = 0
        self.schema['_fingerprint']['last'] = time.ctime()

        if not os.path.exists(self.filename):
            self.data = {}
            self.data['ip_addresses'] = {}
            self.prep()
            self.write()
        else:
            with open(self.filename) as json_file:
                self.data = json.load(json_file)
                self.prep()
                print(json.dumps(self.data['ip_addresses'][self.ip_address]['fingerprints'][self.fingerprint]))

    def prep(self):
        if not 'ip_addresses' in self.data:
            self.data['ip_addresses'] = {}
        if not self.ip_address in self.data['ip_addresses']:
            print('adding ip')
            self.data['ip_addresses'][self.ip_address] = copy.deepcopy(self.schema['_ip'])
        if not self.fingerprint in self.data['ip_addresses'][self.ip_address]['fingerprints']:
            print('adding fingerprint')
            self.data['ip_addresses'][self.ip_address]['fingerprints'][self.fingerprint] = copy.deepcopy(self.schema['_fingerprint'])

    def add(self):
        self.prep()
        self.data['ip_addresses'][self.ip_address]['sum'] = self.data['ip_addresses'][self.ip_address]['sum'] + 1
        self.data['ip_addresses'][self.ip_address]['fingerprints'][self.fingerprint]['pixels'] = self.data['ip_addresses'][self.ip_address]['fingerprints'][self.fingerprint]['pixels'] + 1
        self.data['ip_addresses'][self.ip_address]['fingerprints'][self.fingerprint]['last'] = time.ctime()
        self.write()

    def rate_limit(self):
        current = self.data['ip_addresses'][self.ip_address]['fingerprints'][self.fingerprint]
        if current['pixels'] < 10:
            return
        maxperday = self.maxperday
        maxperhour = self.maxperhour
        if self.get_daily(current) > maxperday:
            raise Exception(str(self.get_daily(current))+' since '+self.data['ip_addresses'][self.ip_address]['fingerprints'][self.fingerprint]['first'])
        if self.get_hourly(current) > maxperhour:
            print('We have reached our hourly limit of ' + str(maxperhour))
            return True

    def get_daily(self, current):
        first = parse(current['first'])
        last = parse(current['last'])
        length = (last - first).total_seconds()/60/60/24
        if length > 60*60*24:
            return current['pixels']/length
        else:
            return current['pixels']

    def get_hourly(self, current):
        first = parse(current['first'])
        last = parse(current['last'])
        seconds = (last - first).total_seconds()
        rate = current['pixels']/seconds*60*60
        print "Pixels per hour: " + str(round(rate)) + " (avg " + str(round(3600/rate)) + " seconds wait)"
        return rate

    def write(self):
        with open(self.filename, 'w') as json_file:
            json.dump(self.data, json_file)


