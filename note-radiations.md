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