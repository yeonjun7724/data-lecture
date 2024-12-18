import numpy as np
from sklearn.cluster import KMeans
from PyQt5.QtCore import QVariant
from PyQt5.QtGui import QColor
from qgis.core import QgsField, QgsProject, QgsSymbol, QgsRendererCategory, QgsCategorizedSymbolRenderer

# QGIS 레이어 불러오기
layer = QgsProject.instance().mapLayersByName("seoul_toilet")[0]  # 레이어 이름 설정

# 좌표 데이터 추출
data = []
for feature in layer.getFeatures():
    geom = feature.geometry()
    if geom.isNull():
        continue
    point = geom.asPoint()  # 포인트 형식의 좌표 추출
    data.append([point.x(), point.y()])

data = np.array(data)

# K-평균 클러스터링 수행
k = 3  # 원하는 클러스터 개수
kmeans = KMeans(n_clusters=k, random_state=0)
kmeans.fit(data)
labels = kmeans.labels_

# 클러스터 레이블을 새 필드로 추가
layer.startEditing()
layer.dataProvider().addAttributes([QgsField("Cluster", QVariant.Int)])
layer.updateFields()

for i, feature in enumerate(layer.getFeatures()):
    feature["Cluster"] = int(labels[i])
    layer.updateFeature(feature)

layer.commitChanges()

# 클러스터 시각화를 위한 범주형 렌더러 설정
categories = []
cluster_colors = {
    0: QColor("red"),
    1: QColor("blue"),
    2: QColor("green")
}

# 각 클러스터에 대해 색상과 범주 설정
for cluster_value, color in cluster_colors.items():
    symbol = QgsSymbol.defaultSymbol(layer.geometryType())
    symbol.setColor(color)
    category = QgsRendererCategory(cluster_value, symbol, f"Cluster {cluster_value}")
    categories.append(category)

# 범주형 렌더러를 레이어에 적용
renderer = QgsCategorizedSymbolRenderer("Cluster", categories)
layer.setRenderer(renderer)

# 변경 사항을 QGIS에 반영
layer.triggerRepaint()
QgsProject.instance().addMapLayer(layer)

print("클러스터링 시각화가 완료되었습니다.")
