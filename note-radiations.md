# methodology


All computations are done after decomposing roof polygons into triangles.

Irradiance is computed for each triangle based on tilt, azimuth and shadows.

A base irradiance is obtained from both a TMY and a function provided by meteotest.

This base irradiance is then adjusted with the amount of shadows falling onto the triangle.


## Shadows

We first compute a transformation matrix to align the vector sun position and center of a triangle on the z-axis in order to cancel z. This matrix is used to transform the triangle and polygons from the solar.solid table that intersect with an extrusion of the considered triangle towards the sun, as returned by PostGIS. We then operate an union of all the intersections of these solids on the triangle in the XY plane with the help of GEOS through Shapely. The ratio of exposed area on this transformed triangle is then applied on the area of the original triangle in order to obtained the area that receives direct radiation.

```python

```

Both queries to PostGIS and intersections computations in the module are very demanding in terms of computation. It led to the decision to give up on an _on-the-fly_ approach as it would have required a massive hardware setup to provide a decent user experience. As we'll see later, we can get down to a sub-second to compute _a_ roof polygon, but at the expense of 48 cores shared between the module and PostGIS.

Hence the final approach is to build at once the resulting table of all irradiances. It comes with a couple challenges to, first, make it a reproductible process that can be run again when datasets are updated, and second, keep the cost as low as possible while achieving the computation in a reasonnable time frame.

### sample rate

Running the process over the 8400 hours of the year for the more than a million roof polygons would incur near unbearable resource expenses. We've decided to operate at a statistical level by sampling the year into days.
We've had a hint from the flemish team that a sample of a day every 14 days could work at providing accurate enough data. Our experiments converged towards a similar conclusion.

TODO numbrers

### cli
On the reproductible front, as part of the Django application that is the heart of solar-loader, we've developed a command line interface to run some of the tasks needed by the loader.


## The run

The fact. The whole computation in sequence to obtain radiations of exposed parts of a roof with a sample rate of 14 days takes an average of 45 seconds, and we've got a bit more than a million roofs to process. As is, it would mean a 520 days time frame.

The chance we have is that each triangle can be process in isolation, bearing no dependency to other triangles. It calls for parallelism. If Python is well known to being slow at computing, which in this case is mitigated byt using bindings to high performance libraries, namely numpy and geos, it comes with ```concurrent.future``` that makes it easier to achieve the kind of parallelism that we need here.

```ProcessPoolExecutor``` to run local computations with Shapely on each CPU
```ThreadPoolExecutor``` to run batches of queries on PostGIS

The experiment has been ran on Digital Ocean, which offers affordable compute units with a simple interface.
DO instances come in 2 types, "standard" and "CPU optimized", we only used "standard" ones for this experiment, and even though not measurable beforehand, we can expect some improvements with "CPU optimized" instances.

 - 1   compute: 24 vCPU, 128GB, $0.952/hour
 - 2+1 postgis:  8 vCPU,  32GB, $0.238/hour

```sh
time solar-loader all_rad --limit 512 2> /dev/null
real    7m2.854s
user    78m59.936s
sys     5m37.568s
```

That is 423 seconds / 512 roofs, 0.82 seconds per roof polygon. Which is still a 330 hours (9 days and a half) run for the whole dataset, but it comes back in the scope of the current project's timeline. On the cost side of things, we're then looking at an estimate of

```python
(0.952 + 3 * 0.238) * 330
#>> 549.78
```

with the very same setup.

If we go with a more abstract cpu time per roof, we're back to our average of 40 seconds, but we can go with CPU optimized at 0.952/hours for a 32 vCPUs unit, which gives

```python
total_time = 40 * 1000000 / 3600
cpu_cost = 0.952 / 32
cpu_cost * total_time
#>> 330.55555555555554
```

Leaving potential performances improvement aside.


## automation

Part of the setup has already been automated in lot-1, that is the building of a complete source dataset. Automating the compute part is a bit more difficult in  that sense that it would be tied to a cloud provider. Instead, what follows is a step by step guide that ought to be "portable" across cloud providers.


### images

Both should be Debian 9

#### solar-loader

1. Install dependencies

  ```console
  $ apt install git python3-pip python3-dev libgeos-dev libxml2-dev libxslt-dev
  $ pip3 install virtenv
  ```

2. Clone the repository

  ```console
  $ git clone https://github.com/be-lb/solar-loader.git
  ```
3. Create a virtualenv with python 3 and activate it

  ```console
  $ virtualenv venv
  $ source venv/bin/activate
  ```

4. Install the requirements in the virtualenv

  ```console
  $ virtualenv venv
  $ source venv/bin/activate
  ```

5. Install the requirements

  ```console
  (venv) $ cd
  (venv) $ pip install -r requirements.txt
  ```

6. Install the module

```console
(venv) $ python setup.py install
```

- Créer le fichier settings-dev.py

- Configure the module

```console
(venv) $ export DJANGO_SETTINGS_MODULE=settings-dev
(venv) $ export PYTHONPATH=/var/solar/solar-loader/solar_loader
```

Et ce devrait marcher (mais non :())

snapshot

### Postgis

The install has been tested on PostgreSQL 9.6 / PostGIS 2.3.


1. Install PostgreSQL (min 9.6) / PostGIS (min 2.3)

  ```console
  $ apt install postgresql-9.6 postgis-2.3 postgresql-9.6-postgis-scripts postgresql-client
  ```

2. Follow instructions from lot-1/db to get all of the dataset

  ```console
  user:~$ sudo su - postgres
  postgres:~$ psql -f  lot-1-master/db/sql/create-database.sql
  postgres:~$ exit
  user:~$ psql  -h localhost -U solar -f path-to-lot-1/db/sql/configure-solar.sql solar
  user:/path-to-lot-1/db$ ./deploy.sh localhost solar solar plokplok /path-to-solar-data/
  ```

3. configure pg
  - listen to all
  - many tweaks

snapshot

### runs


### results
