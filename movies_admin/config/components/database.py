import os

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('PG_DB'),
        'USER': os.getenv('PG_USER'),
        'PASSWORD': os.getenv('PG_PASSWORD'),
        'HOST': os.getenv('SQL_HOST', '127.0.0.1'),
        'PORT': os.getenv('SQL_PORT', 5432),
        'OPTIONS': {
            'options': os.getenv('SQL_OPTIONS'),
        },
    }
}
