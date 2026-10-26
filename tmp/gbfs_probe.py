import json, urllib.request

def fetch_json(url):
    with urllib.request.urlopen(url, timeout=20) as r:
        return json.load(r)

root = fetch_json('https://gbfs.capitalbikeshare.com/gbfs/2.3/gbfs.json')
lang = next(iter(root.get('data', {})))
feeds = root['data'][lang]['feeds']
feed_map = {feed['name']: feed['url'] for feed in feeds}
station_info_url = feed_map['station_information']
status_url = feed_map['station_status']
info = fetch_json(station_info_url)
status = fetch_json(status_url)
print('STATION_INFO_KEYS', sorted(info.get('data', {}).keys()))
print('STATION_STATUS_KEYS', sorted(status.get('data', {}).keys()))
print('INFO_SAMPLE', json.dumps(info['data']['stations'][0], indent=2)[:4000])
print('STATUS_SAMPLE', json.dumps(status['data']['stations'][0], indent=2)[:4000])
