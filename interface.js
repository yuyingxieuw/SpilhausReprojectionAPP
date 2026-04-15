// script for building basemap
let metersProjection = null;
let CRS_Spilhaus = null;
let mapSpilhaus = null;

const minx = -16857702.71589949;
const miny = -17212325.962645144;
const maxx = 17289853.05215329;
const maxy = 16935229.805407636;

const resolutions = [
  213422.22355032988708, 106711.11177516494354, 53355.55588758247177,
  26677.77794379123588,
];

const mapBounds = L.latLngBounds([miny, minx], [maxy, maxx]);

function buildCRS() {
  metersProjection = {
    project: (latlng) => L.point(latlng.lng, latlng.lat),
    unproject: (point) => L.latLng(point.y, point.x),
    bounds: L.bounds(L.point(minx, miny), L.point(maxx, maxy)),
  };

  CRS_Spilhaus = L.extend({}, L.CRS.Simple, {
    projection: metersProjection,
    transformation: new L.Transformation(1, -minx, -1, maxy),
    scale: (z) => 1 / resolutions[z],
    zoom: (s) => {
      const scales = resolutions.map((r) => 1 / r);
      let best = 0,
        err = Infinity;
      for (let i = 0; i < scales.length; i++) {
        const d = Math.abs(scales[i] - s);
        if (d < err) {
          err = d;
          best = i;
        }
      }
      return best;
    },
    infinite: false,
  });
}

function createSpilhaus() {
  mapSpilhaus = L.map("mapSpilhaus", {
    crs: CRS_Spilhaus,
    center: [-1590000, -14000000],
    zoom: 2,
    maxBounds: mapBounds,
    minZoom: 2,
    maxZoom: 3,
    scrollWheelZoom: "center",
    touchZoom: "center",
    doubleClickZoom: "center",
    zoomSnap: 1,
    zoomDelta: 1,
    inertia: false,
  });
}

function addSpilhausTiles() {
  let tile = L.tileLayer("tiles/{z}/{x}/{y}.png", {
    tms: true,
    tileSize: 256,
    minZoom: 0,
    maxZoom: 3,
    minNativeZoom: 3,
    maxNativeZoom: 3,
    scrollWheelZoom: "center",
    touchZoom: "center",
    doubleClickZoom: "center",
    zoomSnap: 1,
    zoomDelta: 1,
    inertia: false,
    noWrap: true,
    bounds: mapBounds,
    keepBuffer: 2,
  }).addTo(mapSpilhaus);
}

async function loadJSONdata1() {
  ///add polygon here
  const style = {
    color: "#e4e5e7ff",
    weight: 1,
    fillColor: "#d3340cff",
    fillOpacity: 0.25,
  };

  try {
    const r = await fetch(
      // 永远只能是相对路径
      "tile_data/country_54099_China.geojson",
    );
    const geojson = await r.json();

    L.geoJSON(geojson, {
      coordsToLatLng: (c) => L.latLng(c[1], c[0]),
      style,
      interactive: true,
    }).addTo(mapSpilhaus);

    console.log("Data loaded");
  } catch (err) {
    console.error("Data Loaded Failed", err);
  }
}

async function loadJSONdata2() {
  ///add polygon here
  const style = {
    color: "#e4e5e7ff",
    weight: 1,
    fillColor: "#d3340cff",
    fillOpacity: 0.25,
  };

  try {
    const r = await fetch(
      // 永远只能是相对路径
      "Fixed.geojson",
    );
    const geojson = await r.json();

    L.geoJSON(geojson, {
      coordsToLatLng: (c) => L.latLng(c[1], c[0]),
      style,
      interactive: true,
    }).addTo(mapSpilhaus);

    console.log("Data loaded");
  } catch (err) {
    console.error("Data Loaded Failed", err);
  }
}

async function loadCenterPoint() {
  // for points
  const pointstyle = {
    radius: 6,
    fillColor: "#392926ff",
    color: "#ffffff",
    weight: 0.4,
    opacity: 1,
    fillOpacity: 1,
  };

  try {
    const r = await fetch("data/center.geojson");
    const geojson = await r.json();

    L.geoJSON(geojson, {
      pointToLayer: (feature, latlng) => {
        return L.circleMarker(latlng, pointstyle);
      },
    }).addTo(mapSpilhaus);
    console.log("center point data loaded");
  } catch (err) {
    console.error("Center Data loaded failed", err);
  }
}

buildCRS();
createSpilhaus();
addSpilhausTiles();
loadJSONdata1();
loadJSONdata2();
//loadCenterPoint();
