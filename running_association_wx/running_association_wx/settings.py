"""
Django settings for running_association_wx project.

Generated by 'django-admin startproject' using Django 2.0.3.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""

import os

from . import secret_settings

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = secret_settings.DJANGO_SECRET_KEY

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
if DEBUG:
    ALLOWED_HOSTS = ['api.yourpowersuck.com']
else:
    ALLOWED_HOSTS = ['127.0.0.1', 'localhost ', 'api.yourpowersuck.com', 'static.yourpowersuck.com']
# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # GeoDjango
    'django.contrib.gis',

    'rest_framework',

    'appointment.apps.AppointmentConfig',
    'running.apps.RunningConfig',
    'association.apps.AssociationConfig',
    'me.apps.MeConfig',
    'marathon_spider.apps.MarathonSpiderConfig',
    'pay.apps.PayConfig',
    'poll.apps.PollConfig',
     'ourRace.apps.MarathonConfig',
    'django_crontab',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'running_association_wx.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')]
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'running_association_wx.wsgi.application'

# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.spatialite',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'
                                       ''),
    }
}

# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/

# 修改语言为中文
# LANGUAGE_CODE = 'zh_Hans'
LANGUAGE_CODE = 'zh-hans'

# 修改时区为中国时区
TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

# 把这个设置成False,否则会使用默认的时区
USE_TZ = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/

STATIC_URL = 'https://static.yourpowersuck.com/static/'
MEDIA_URL = 'https://static.yourpowersuck.com/media/'
# 这个是不属于任何app的静态文件目录
#STATICFILES_DIRS = (
#    os.path.join(BASE_DIR, "static"),
#)
STATIC_ROOT = os.path.join(BASE_DIR, "static")

MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# If you’re using SpatiaLite 4.2+, you must put this in your settings.py:
SPATIALITE_LIBRARY_PATH = '/usr/lib/mod_spatialite.so'

REST_FRAMEWORK = {
    'DATETIME_FORMAT': '%Y-%m-%d %H:%M',  # 指的是输出格式，此参数为字符串
    'DATETIME_INPUT_FORMATS': ['%Y-%m-%d %H:%M'],  # 指的是输入格式，此参数为列表
    'DATE_FORMAT': '%Y-%m-%d',
    'DATE_INPUT_FORMATS': ['%Y-%m-%d'],
    'TIME_FORMAT': '%H:%M:%S',
    'TIME_INPUT_FORMATS': ['%H:%M:%S'],
    'EXCEPTION_HANDLER': 'utils.exception_handler.custom_exception_handler',
    'DEFAULT_THROTTLE_RATES': {
        'user': '60/min'
    }
}
if not DEBUG:
	REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = (
        'rest_framework.renderers.JSONRenderer',
    )

# 微信小程序参数
WX_APPID = secret_settings.WX_APPID
WX_SECRET = secret_settings.WX_SECRET

# 云片短信平台参数
YP_APIKEY = secret_settings.YP_APIKEY
YP_TPL_ID = secret_settings.YP_TPL_ID

# 定时器函数
CRONJOBS = [
    # 每天凌晨三点执行一次，把未手动改成‘已完成’状态的活动自动变成‘已完成’
    ('10 17 * * *', 'utils.cron.CompleteActivityAuto', '>>/home/webapp/wechat/running_association_wx/running_association_wx/cron.log'),
    # 每天早上九点执行一次，给所有有formid的人发投票提醒
    #('0 9 * * *', 'utils.cron.RemindPollingAuto'),
    # 每30分钟执行一次，计算该城市当前多少人报名成功
    #('*/30 * * * *', 'utils.cron.CountCityNumberAuto'),
    # 每天早上八点执行一次，给所有昨天报名成功的人发锦鲤结果通知
    # ('0 8 * * *', 'utils.cron.LuckyDrawAuto'),
    # 每天凌晨四点执行一次，重新计算分舵的人数活动数影响力，并删除没有舵主的分舵
    ('0 4 * * *', 'utils.cron.SaveBranchAuto'),
]

DOMAIN_NAME = "api.yourpowersuck.com"
