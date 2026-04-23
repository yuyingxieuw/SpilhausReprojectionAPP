import geopandas as gpd
import json
from geojson import FeatureCollection
from shapely import LineString
from scripts.workflow import run_program
data= {
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "name": "Large Polygon With Two Holes A",
        "category": "polygon_with_holes"
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [
            [-125, 25],
            [-85, 25],
            [-85, 55],
            [-125, 55],
            [-125, 25]
          ],
          [
            [-118, 30],
            [-108, 30],
            [-108, 38],
            [-118, 38],
            [-118, 30]
          ],
          [
            [-102, 42],
            [-92, 42],
            [-92, 50],
            [-102, 50],
            [-102, 42]
          ]
        ]
      }
    },
    {
      "type": "Feature",
      "properties": {
        "name": "Large Polygon With Three Holes B",
        "category": "polygon_with_holes"
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [
            [20, 10],
            [70, 10],
            [70, 45],
            [20, 45],
            [20, 10]
          ],
          [
            [28, 15],
            [38, 15],
            [38, 23],
            [28, 23],
            [28, 15]
          ],
          [
            [45, 18],
            [58, 18],
            [58, 28],
            [45, 28],
            [45, 18]
          ],
          [
            [50, 32],
            [63, 32],
            [63, 40],
            [50, 40],
            [50, 32]
          ]
        ]
      }
    },
    {
      "type": "Feature",
      "properties": {
        "name": "Large Simple Polygon",
        "category": "polygon"
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [
            [90, -20],
            [130, -20],
            [130, 15],
            [90, 15],
            [90, -20]
          ]
        ]
      }
    },
    {
      "type": "Feature",
      "properties": {
        "name": "MultiPolygon With Holes",
        "category": "multipolygon"
      },
      "geometry": {
        "type": "MultiPolygon",
        "coordinates": [
          [
            [
              [-70, -40],
              [-35, -40],
              [-35, -10],
              [-70, -10],
              [-70, -40]
            ],
            [
              [-62, -33],
              [-50, -33],
              [-50, -22],
              [-62, -22],
              [-62, -33]
            ]
          ],
          [
            [
              [-20, -35],
              [15, -35],
              [15, -5],
              [-20, -5],
              [-20, -35]
            ],
            [
              [-12, -28],
              [0, -28],
              [0, -18],
              [-12, -18],
              [-12, -28]
            ],
            [
              [4, -16],
              [10, -16],
              [10, -10],
              [4, -10],
              [4, -16]
            ]
          ]
        ]
      }
    },
    {
      "type": "Feature",
      "properties": {
        "name": "Long LineString",
        "category": "linestring"
      },
      "geometry": {
        "type": "LineString",
        "coordinates": [
          [-160, 0],
          [-120, 10],
          [-80, 5],
          [-30, 20],
          [10, 15]
        ]
      }
    },
    {
      "type": "Feature",
      "properties": {
        "name": "MultiLineString Example",
        "category": "multilinestring"
      },
      "geometry": {
        "type": "MultiLineString",
        "coordinates": [
          [
            [100, 40],
            [120, 50],
            [140, 45]
          ],
          [
            [105, 20],
            [125, 10],
            [145, 18]
          ]
        ]
      }
    },
    {
      "type": "Feature",
      "properties": {
        "name": "Point Example",
        "category": "point"
      },
      "geometry": {
        "type": "Point",
        "coordinates": [30, -10]
      }
    },
    {
      "type": "Feature",
      "properties": {
        "name": "MultiPoint Example",
        "category": "multipoint"
      },
      "geometry": {
        "type": "MultiPoint",
        "coordinates": [
          [40, 60],
          [55, 58],
          [70, 62],
          [85, 57]
        ]
      }
    }
  ]
}

gdf_processed = run_program(data)
print(gdf_processed )
