# celery config
broker_url = 'amqp://guest:guest@localhost:5672//'

## Using the database to store task state and results.
result_backend = 'redis://'

accept_content = ['pickle']
task_serializer = 'pickle'
result_serializer = 'pickle'

imports = ['solar_loader.celery']
