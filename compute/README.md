# Pre-computing Irradiance Values

Here is a short recipe to replicate computing of irradiance per roof values. The main steps are:

- gather data into a postgresql dump
- build application image
- run a compute node

## Data

Urbis3D (v1), cadaste and TMY. After gathering all the files below, one should end up with something like this (not listing already present files) in the `./data/files` folder.

```
Bruxelles_centre-hour.csv  cadastre.cpg  cadastre.dbf  cadastre.prj  cadastre.qix  cadastre.shp  cadastre.shx  UrbAdm3D_SHP.zip
```

plus the file `Bruxelles_centre-hour.csv` again in the `./app/` folder, because constraints of docker COPY command.

### Urbis3D

This dataset comes from [urbis-download](https://datastore.brussels/web/urbis-download), in its ESRI Shapefile format.

### Cadastre

This dataset is a one of dump of a `cadastre` table on `Paola` server. There's not much history about this dump, it should obviously be updated as well.
Note that we actually only use the `geom` and `capakey` fields, so any shapefile with these fields should be usable.

### TMY

This file has been provided by _Meteotest_ and is known on IBGE servers as `Bruxelles_centre-hour.csv` under `/opt/sdi`.

## Postgis

The first step consists of integrating these datasets into a PostgreSQL dump that will be mounted on a set of databases servers in order to support further computations. A [bash script](./docker/data/build.sh) is provided that does just that or might serve as documentation if docker is not desirable to you. This guiding script create a "solar" database and "solar" schema (the latter to help with dumps), see relevant scripts if it needs adjustment.

## App

The Django application will provide two commands. First to setup a `results` table that will record irradiance values (plus state of the computation), and second to actually run a compute node. The app is the actual `solar_loader` on top of cartostation. It does mean that one must first have a working, if minimal, cartostation setup.

The whole process then depends on Django and solar_loader settings. The main idea of these settings is that database connections are regular Django connections declared in the `DATABASES` setting, whereas actual structures and names of tables are described in the `SOLAR_TABLES` setting. This being the result of not representing the data by means of Django models at development time in order to accomodate various deployment schemes across teams.

```python

DATABASES = {
    'default': { ... },
    'results': { ... },
    'solar0':  { ... },
    'solar1':  { ... },
}

SOLAR_CONNECTION_RESULTS = "results"
SOLAR_CONNECTION = ['solar0', 'solar1']

SOLAR_TABLES = {
    "ground": {
        "table": "energy.sdi_solar_cadastre",
        "geometry": "geom",
        "capakey": "capakey",
    },
    "roof": {
        "table": "energy.sdi_solar_roof",
        "geometry": "geom",
        "centroid": "flat_pos",
    },
    "solid": {"table": "energy.sdi_solar_solid", "geometry": "geom"},
    "results": {
        "table": "energy.sdi_solar_results",
        "irradiance": "irradiance",
        "roof_id": "roof_id",
    },
}
```

### initradiations

```
usage: manage.py initradiations [-h] [--version] [-v {0,1,2,3}]
                                [--settings SETTINGS]
                                [--pythonpath PYTHONPATH] [--traceback]
                                [--no-color] [--force-color] [--skip-checks]

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  -v {0,1,2,3}, --verbosity {0,1,2,3}
                        Verbosity level; 0=minimal output, 1=normal output,
                        2=verbose output, 3=very verbose output
  --settings SETTINGS   The Python path to a settings module, e.g.
                        "myproject.settings.main". If this isn't provided, the
                        DJANGO_SETTINGS_MODULE environment variable will be
                        used.
  --pythonpath PYTHONPATH
                        A directory to add to the Python path, e.g.
                        "/home/djangoprojects/myproject".
  --traceback           Raise on CommandError exceptions
  --no-color            Don't colorize the command output.
  --force-color         Force colorization of the command output.
  --skip-checks         Skip system checks.

```

This command creates the table that will host all the results from computations processed by compute nodes. There must be only one such table on a server that's reachable to all nodes. It comes in the following form:

```
# \d solar.results;
                                         Table "solar.results"
     Column     |           Type           | Collation | Nullable |               Default
----------------+--------------------------+-----------+----------+-------------------------------------
 id             | integer                  |           | not null | nextval('results_id_seq'::regclass)
 roof_id        | character varying(50)    |           | not null |
 irradiance     | numeric                  |           |          | 0.0
 area           | numeric                  |           |          | 0.0
 compute_status | integer                  |           |          | 0
 compute_node   | character varying(32)    |           |          |
 compute_start  | timestamp with time zone |           |          |
 compute_end    | timestamp with time zone |           |          |

```

Besides irradiance per roof, we also store some informations to drive and monitor the compute work.

`compute_status` is important and can be interpreted as:

- 0 = TODO, initial value
- 1 = PENDING, a compute node is busy with this roof
- 2 = DONE, irradiance has been successfully computed and recorded
- 3 = FAILED, computing irradiance has failed
- 4 = ACK, this roof is part of batch reserved by a compute node

Considering that the computation is quite a long process, it should be regularly monitored. It's rather easy with queries such as

```sql
select compute_status, count(id)from solar.results group by compute_status;
```

`compute_node` is the name of the node that has processed this roof and is useful in spoting weird behaviour coming from a specific node with such query as

```sql
select compute_node, compute_status, count(id), max(compute_end - compute_start), min(compute_end - compute_start), avg(compute_end - compute_start) from solar.results group by compute_node, compute_status order by compute_node, compute_status;
```

Note: In order to create the `results` table, we also need the data from the roof table, thus the dump made in the first step needs to be mounted on the same DB as the resulting one. But on the other hand, this command does not use `SOLAR_CONNECTION`s which can remain an empty list for this run.

### computeradiations

```
usage: manage.py computeradiations [-h] [-bs BATCH_SIZE] [--version]
                                   [-v {0,1,2,3}] [--settings SETTINGS]
                                   [--pythonpath PYTHONPATH] [--traceback]
                                   [--no-color] [--force-color]
                                   [--skip-checks]
                                   node_name

positional arguments:
  node_name             Name of this process

optional arguments:
  -h, --help            show this help message and exit
  -bs BATCH_SIZE, --batch-size BATCH_SIZE
                        Size of a batch to process
  --version             show program's version number and exit
  -v {0,1,2,3}, --verbosity {0,1,2,3}
                        Verbosity level; 0=minimal output, 1=normal output,
                        2=verbose output, 3=very verbose output
  --settings SETTINGS   The Python path to a settings module, e.g.
                        "myproject.settings.main". If this isn't provided, the
                        DJANGO_SETTINGS_MODULE environment variable will be
                        used.
  --pythonpath PYTHONPATH
                        A directory to add to the Python path, e.g.
                        "/home/djangoprojects/myproject".
  --traceback           Raise on CommandError exceptions
  --no-color            Don't colorize the command output.
  --force-color         Force colorization of the command output.
  --skip-checks         Skip system checks.

```

A compute node is generally run alongside a powerful or several database(s) serving the data gathered in the first step (and for which the dump is intended) in order to optimize workloads. Because runs just "steal" work from the `results` table, they can be started and stopped in any order and time. If some node is believed to have misbehaved, clearing its work is just a matter of updating corresponding records with a `compute_status` at TODO, next runs will pick up these roofs. Compute nodes wil stop themselves when there's not anymore work to get.

Note that this command will try to run as much processes as available CPUs (up to 32), and basically run these CPUs at 100%. Also note that these processes will maintain a rather large amount of connections to the database servers, those should be set with an adjusted `max_connections` and relevant other settings.
