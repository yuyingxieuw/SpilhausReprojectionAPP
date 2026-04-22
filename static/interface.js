// script for building basemap
let metersProjection = null;
let CRS_Spilhaus = null;
let mapSpilhaus = null;
let uploadedGeojsonLayer = null;

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
  let tile = L.tileLayer("/static/tiles/{z}/{x}/{y}.png", {
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

function setSubmitStatus(message, type = "neutral") {
  const status = document.getElementById("submitStatus");
  if (!status) return;

  status.textContent = message;
  status.dataset.type = type;
}

function assertGeoJSONShape(geojson) {
  const validTypes = new Set([
    "FeatureCollection",
    "Feature",
    "GeometryCollection",
    "Point",
    "MultiPoint",
    "LineString",
    "MultiLineString",
    "Polygon",
    "MultiPolygon",
  ]);

  if (!geojson || typeof geojson !== "object") {
    throw new Error("Please upload valid GeoJSON file.");
  }

  if (!validTypes.has(geojson.type)) {
    throw new Error("GeoJSON lacks valid type.");
  }

  if (
    geojson.type === "FeatureCollection" &&
    !Array.isArray(geojson.features)
  ) {
    throw new Error("FeatureCollection needs features.");
  }

  if (geojson.type === "Feature" && !geojson.geometry) {
    throw new Error("Feature needs geometry.");
  }
}

function countGeoJSONFeatures(geojson) {
  if (geojson.type === "FeatureCollection") return geojson.features.length;
  if (geojson.type === "Feature") return 1;
  return 1;
}

function addUploadedGeoJSON(geojson) {
  if (uploadedGeojsonLayer) {
    mapSpilhaus.removeLayer(uploadedGeojsonLayer);
  }

  uploadedGeojsonLayer = L.geoJSON(geojson, {
    coordsToLatLng: (c) => L.latLng(c[1], c[0]),
    pointToLayer: (_feature, latlng) =>
      L.circleMarker(latlng, {
        radius: 5,
        fillColor: "#ffd166",
        color: "#1b1b18",
        weight: 1,
        opacity: 1,
        fillOpacity: 0.9,
      }),
    style: {
      color: "#0f5132",
      weight: 2,
      fillColor: "#2a9d8f",
      fillOpacity: 0.32,
    },
    interactive: true,
  }).addTo(mapSpilhaus);

  const bounds = uploadedGeojsonLayer.getBounds();
  if (bounds.isValid()) {
    mapSpilhaus.fitBounds(bounds.pad(0.12), {
      animate: true,
      maxZoom: 3,
    });
  }
}

async function readGeoJSONFile(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => reject(new Error("Fail to read the file."));
    reader.readAsText(file);
  });
}

function setupSubmitForm() {
  const form = document.getElementById("submitForm");
  const fileInput = document.getElementById("geojsonFile");
  const textInput = document.getElementById("geojsonInput");
  const submitButton = document.getElementById("submitButton");

  if (!form || !fileInput || !textInput || !submitButton) return;

  fileInput.addEventListener("change", async () => {
    const [file] = fileInput.files;
    if (!file) return;

    try {
      const text = await readGeoJSONFile(file);
      textInput.value = text;
      setSubmitStatus(`Read file ${file.name}.`);
    } catch (err) {
      setSubmitStatus(`Error in read geojsonfile: ${err}`);
    }
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    submitButton.disabled = true;
    setSubmitStatus("Submiting...");

    try {
      const rawGeoJSON = textInput.value.trim();

      if (!rawGeoJSON) {
        throw new Error("Please upload or paste GeoJSON。");
      }

      const geojson = JSON.parse(rawGeoJSON);
      assertGeoJSONShape(geojson);
      const responseData = await sendToServer(geojson);
      processed_result = responseData.result;
      loadGeoJSONToLeaflet(processed_result);
      const featureCount = countGeoJSONFeatures(processed_result);
      setSubmitStatus(
        `Upload finished, added ${featureCount} feature to the map。`,
        "success",
      );
    } catch (err) {
      setSubmitStatus(`Error in process geojson: ${err}`);
    } finally {
      submitButton.disabled = false;
    }
  });
}

async function sendToServer(geojson) {
  const response = await fetch("/api/process", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(geojson),
  });
  const responseJson = await response.json();
  return responseJson;
}

function loadGeoJSONToLeaflet(data, options = {}) {
  const {
    pointToLayer,
    style,
    onEachFeature,
    coordsToLatLng,
    markersInheritOptions = false,
  } = options;

  if (!data) {
    throw new Error("No geojson data provided");
  }

  // 把各种 GeoJSON 顶层类型统一整理成 Leaflet 更稳妥可吃的格式
  function normalizeGeoJSON(input) {
    if (typeof input === "string") {
      input = JSON.parse(input);
    }
    if (!input || typeof input !== "object") {
      throw new Error("Invalid GeoJSON: input must be an object");
    }

    const allowedTypes = new Set([
      "FeatureCollection",
      "Feature",
      "GeometryCollection",
      "Point",
      "MultiPoint",
      "LineString",
      "MultiLineString",
      "Polygon",
      "MultiPolygon",
    ]);

    if (!allowedTypes.has(input.type)) {
      throw new Error(`Unsupported GeoJSON type: ${input.type}`);
    }

    // 1) 已经是 FeatureCollection，直接返回
    if (input.type === "FeatureCollection") {
      return input;
    }

    // 2) 已经是 Feature，直接返回
    if (input.type === "Feature") {
      return input;
    }

    // 3) GeometryCollection 需要包成 Feature
    if (input.type === "GeometryCollection") {
      return {
        type: "Feature",
        properties: {},
        geometry: input,
      };
    }

    // 4) 其他纯 geometry 类型（Point / Polygon / ...）也包成 Feature
    return {
      type: "Feature",
      properties: {},
      geometry: input,
    };
  }

  const normalized = normalizeGeoJSON(data);

  const defaultPointToLayer = (feature, latlng) => {
    return L.circleMarker(latlng, {
      radius: 6,
      weight: 1,
      fillOpacity: 0.8,
    });
  };

  const defaultStyle = (feature) => {
    const geomType = feature?.geometry?.type;
    // Line
    if (geomType === "LineString" || geomType === "MultiLineString") {
      return {
        color: "#3388ff",
        weight: 3,
        opacity: 1,
      };
    }
    // Polygon
    if (geomType === "Polygon" || geomType === "MultiPolygon") {
      return {
        color: "#3388ff", // 边线颜色
        weight: 1,
        fillColor: "#3388ff", // 填充颜色
        fillOpacity: 0.3,
      };
    }
    return {};
  };

  const defaultOnEachFeature = (feature, layer) => {
    if (feature.properties && Object.keys(feature.properties).length > 0) {
      layer.bindPopup(
        `<pre>${JSON.stringify(feature.properties, null, 2)}</pre>`,
      );
    }
  };

  const geojsonLayer = L.geoJSON(normalized, {
    pointToLayer: pointToLayer || defaultPointToLayer,
    style: style || defaultStyle,
    onEachFeature: onEachFeature || defaultOnEachFeature,
    coordsToLatLng,
    markersInheritOptions,
  });

  geojsonLayer.addTo(mapSpilhaus);

  return geojsonLayer;
}

buildCRS();
createSpilhaus();
addSpilhausTiles();
// loadJSONdataPoly();
setupSubmitForm();

//loadCenterPoint();
