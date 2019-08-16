from running_association_wx.settings import DOMAIN_NAME

WEIXIN_APP_ID = 'wxadf7a9a3c65c3961'
WEIXIN_APP_SECRET = '75b3244a7b272d42861a325154eef8b2'
WEIXIN_MCH_ID = '1447956502'
WEIXIN_MCH_KEY = '123qweasdzxcwer234cvvbnfgh456rty'
WEIXIN_NOTIFY_URL_FOUND = 'https://{}/payment/branch-fund-result/'.format(DOMAIN_NAME)
WEIXIN_NOTIFY_URL_ORDER = 'https://{}/payment/order-result/'.format(DOMAIN_NAME)
WEIXIN_NOTIFY_URL_MARATHON_ORDER = 'https://{}/payment/marathon-order-result/'.format(DOMAIN_NAME)
WEIXIN_NOTIFY_URL_ACTIVITY = 'https://{}/payment/activity-result/'.format(DOMAIN_NAME)
WEIXIN_MCH_KEY_FILE = './1447956502_djangodrf_key.pem'
WEIXIN_MCH_CERT_FILE = './1447956502_djangodrf_cert.pem'
