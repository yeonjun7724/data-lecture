pip install seaborn
pip install matplotlib
pip install Moran
pip install pysal
pip install esda libpysal
pip install scikit-learn

import geopandas as gpd
from esda.moran import Moran_Local
from libpysal.weights import Queen
from qgis.core import QgsVectorLayer, QgsProject, QgsGraduatedSymbolRenderer, QgsRendererRange, QgsSymbol, QgsStyle
from PyQt5.QtGui import QColor

# GeoPandas로 서울 행정구역 shp 파일 로드 및 분석
shp_path = "C:/Users/joe전략마케팅팀/Desktop/새 폴더/3주차_교육과정/seoul_sgg.shp"  # 파일 경로
output_shp_path = "C:/Users/joe전략마케팅팀/Desktop/moran_result.shp"  # 저장 경로

# GeoDataFrame 로드
gdf = gpd.read_file(shp_path)

# Queen 인접 행렬 생성
w = Queen.from_dataframe(gdf)
w.transform = "r"  # Row-standardization

# Local Moran's I 계산 (index 열 사용)
index_values = gdf["index"]  # index 칼럼이 수치형이어야 합니다
moran_local = Moran_Local(index_values, w)

# Moran's I 값 및 p-value 추가
gdf["moran_I"] = moran_local.Is
gdf["p_value"] = moran_local.p_sim
gdf["sig_category"] = "Not Significant"
gdf.loc[gdf["p_value"] < 0.05, "sig_category"] = "Significant"
gdf["quadrant"] = moran_local.q  # LISA 분면 정보 추가

# SHP 파일로 저장
gdf.to_file(output_shp_path, driver="ESRI Shapefile")
print(f"분석 결과가 저장되었습니다: {output_shp_path}")

# 2. QGIS 환경에서 레이어 추가
layer = QgsVectorLayer(output_shp_path, "Moran Result", "ogr")
if not layer.isValid():
    print("레이어를 불러오는 데 실패했습니다!")
else:
    QgsProject.instance().addMapLayer(layer)
    print("레이어가 추가되었습니다.")

# 3. QGIS 단계구분도 설정
def apply_graduated_symbology(layer, field_name):
    """
    PyQGIS를 이용해 단계구분도 스타일을 설정하는 함수.
    """
    ranges = []
    color_ramp = [
        ("#d73027", -1.0, -0.5),  # 낮은 Moran's I
        ("#fdae61", -0.5, 0),    # 중간값(음수)
        ("#fee08b", 0, 0.5),     # 중간값(양수)
        ("#1a9850", 0.5, 1.0)    # 높은 Moran's I
    ]
    
    for color, lower, upper in color_ramp:
        symbol = QgsSymbol.defaultSymbol(layer.geometryType())
        symbol.setColor(QColor(color))
        range_item = QgsRendererRange(lower, upper, symbol, f"{lower} ~ {upper}")
        ranges.append(range_item)
    
    renderer = QgsGraduatedSymbolRenderer(field_name, ranges)
    renderer.setMode(QgsGraduatedSymbolRenderer.GraduatedColor)
    
    # 레이어에 렌더러 적용
    layer.setRenderer(renderer)
    layer.triggerRepaint()

# 단계구분도를 'moran_I' 필드 기준으로 적용
apply_graduated_symbology(layer, "moran_I")

print("단계구분도가 적용되었습니다.")