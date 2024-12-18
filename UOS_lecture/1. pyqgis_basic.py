# 첫 번째 벡터 레이어 불러오기
layer_path_1 = "/seoul_sgg.shp"  # 첫 번째 벡터 파일 경로
layer_1 = QgsVectorLayer(layer_path_1, "seoul_sgg", "ogr")

if not layer_1.isValid():
    print("First layer failed to load!")
else:
    QgsProject.instance().addMapLayer(layer_1)


# 두 번째 벡터 레이어 불러오기
layer_path_2 = "/seoul_toilet.shp"  # 두 번째 벡터 파일 경로
layer_2 = QgsVectorLayer(layer_path_2, "seoul_toilet", "ogr")

if not layer_2.isValid():
    print("Second layer failed to load!")
else:
    QgsProject.instance().addMapLayer(layer_2)

# 버퍼 거리 설정
buffer_distance = 100  # 100미터

# 버퍼 레이어 출력 경로 설정
buffer_output_path = "/seoul_toilet_buffered.shp"  # 버퍼 출력 파일 경로

# 버퍼 생성
processing.run("native:buffer", {
    'INPUT': layer_2,
    'DISTANCE': buffer_distance,
    'SEGMENTS': 5,
    'END_CAP_STYLE': 0,  # Flat
    'JOIN_STYLE': 0,     # Round
    'MITER_LIMIT': 2,
    'DISSOLVE': False,
    'OUTPUT': buffer_output_path
})

# 생성된 버퍼 레이어를 불러와서 프로젝트에 추가
buffer_layer = QgsVectorLayer(buffer_output_path, "seoul_toilet_buffer", "ogr")
if not buffer_layer.isValid():
    print("Buffer layer failed to load!")
else:
    QgsProject.instance().addMapLayer(buffer_layer)

# 폴리곤 레이어 불러오기
polygon_layer = QgsProject.instance().mapLayersByName("seoul_sgg")

# 중심점 레이어 생성
centroid_layer = QgsVectorLayer("Point?crs=EPSG:5179", "seoul_sgg_centroids", "memory")
centroid_layer_data = centroid_layer.dataProvider()

# 기존 레이어의 속성 필드 추가
centroid_layer_data.addAttributes(polygon_layer.fields())
centroid_layer.updateFields()

# 중심점 생성
for feature in polygon_layer.getFeatures():
    centroid = feature.geometry().centroid()
    centroid_feature = QgsFeature()
    centroid_feature.setGeometry(centroid)
    centroid_feature.setAttributes(feature.attributes())
    centroid_layer_data.addFeature(centroid_feature)

# 결과 레이어 추가
QgsProject.instance().addMapLayer(centroid_layer)

# 레이어 설정
input_layer = QgsProject.instance().mapLayersByName("seoul_sgg")[0]

# Convex Hull 생성
convex_hull_result = processing.run("native:convexhull", {
    'INPUT': input_layer,
    'OUTPUT': 'memory:'
})

# 결과 레이어 추가
convex_hull_layer = convex_hull_result['OUTPUT']
QgsProject.instance().addMapLayer(convex_hull_layer)

# 레이어 불러오기
layer = QgsProject.instance().mapLayersByName("seoul_sgg")[0]

# 속성 테이블의 데이터 읽기
for feature in layer.getFeatures():
    print(feature['SIG_KOR_NM'])  # 실제 필드 이름을 사용하여 출력

# 특정 조건으로 필터링
expression = QgsExpression("SIG_KOR_NM = '동대문구'")  # 필드 이름과 값을 수정하여 조건 설정
request = QgsFeatureRequest(expression)

print('필터링 된 구만 선택')
# 필터링된 결과 출력
for feature in layer.getFeatures(request):
    print(feature['SIG_KOR_NM'])  # '동대문구'인 레코드만 출력됨

# 필요한 라이브러리 임포트
from qgis.PyQt.QtCore import QVariant

# 레이어 불러오기
sgg_layer = QgsProject.instance().mapLayersByName("seoul_sgg")[0]
toilet_layer = QgsProject.instance().mapLayersByName("seoul_toilet")[0]

# 'index'라는 새로운 필드를 sgg_layer에 추가
sgg_layer.dataProvider().addAttributes([QgsField("index", QVariant.Int)])
sgg_layer.updateFields()

# 'index' 필드의 인덱스 확인
index_field_idx = sgg_layer.fields().indexFromName("index")

# 각 seoul_sgg 폴리곤에 대해 seoul_toilet 포인트 개수를 계산하여 'index' 필드에 저장
for sgg_feature in sgg_layer.getFeatures():
    # 현재 폴리곤의 범위(bounding box)를 사용해 포함된 포인트 검색
    count = 0
    for toilet_feature in toilet_layer.getFeatures():
        if sgg_feature.geometry().contains(toilet_feature.geometry()):
            count += 1
    
    # 'index' 필드에 개수 저장
    sgg_layer.startEditing()
    sgg_feature[index_field_idx] = count
    sgg_layer.updateFeature(sgg_feature)
sgg_layer.commitChanges()
