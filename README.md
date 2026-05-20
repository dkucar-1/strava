## Bulk Upload to Strava

The gpx format is basically xml with tags for geographical information such as latitude and longitude.

Strava doesn't respect `<trkseg></trkseg>`. It just draws each one of those as part of a continuous line, with flight lines connecting separate segments. This makes it not ideal for migrated tracks from other gpx tracking software such as Gaia or CalTopo.

The goal is to split those up into separate files and upload them as individual tracks.

### Strava gpx format

A Strava header looks like, with the body of the content starting with `<gpx ..><trk>`
```
<?xml version="1.0" encoding="UTF-8"?>
<gpx creator="StravaGPX" version="1.1" xmlns="http://www.topografix.com/GPX/1/1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd">
 <metadata>
  <time>2022-05-12T14:53:44Z</time>
 </metadata>
 <trk>
  <name>Strava route name</name>
...
```
and ends with 
```
  </trkseg>
 </trk>
</gpx>
```
So it is a matter of splitting up multiple files for multiple tracks manually and uploading one by one to strava using the API's POST verb.

For our purposes, the `<type>..</type>` is always 'hiking'.

### Token Exchange
The process is slightly complex and is handled in the `strava_auth` file. It's roughly described in the developer docs here 
<br>
https://developers.strava.com/docs/authentication/#refresh-expired-access-tokens