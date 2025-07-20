"""
Stage 3: 최단 경로 찾기

이 모듈은 분석된 지도 데이터를 사용하여 집(MyHome)에서 반달곰 커피(BandalgomCoffee) 위치까지의
최단 경로를 찾습니다. BFS 알고리즘을 사용하여 경로를 탐색하며, 공사장 위치는 지나갈 수 없습니다.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from collections import deque
import os
import sys


def load_map_data():
    """지도 데이터를 로드하고 전처리합니다."""
    try:
        print('지도 데이터를 로드하는 중...')
        
        area_map_df = pd.read_csv('data/area_map.csv')
        area_struct_df = pd.read_csv('data/area_struct.csv')
        area_category_df = pd.read_csv('data/area_category.csv')
        
        # 카테고리 데이터 정리
        area_category_df.columns = area_category_df.columns.str.strip()
        area_category_df['struct'] = area_category_df['struct'].str.strip()
        
        # 구조물 이름 매핑
        merged_df = pd.merge(area_struct_df, area_category_df, on='category', how='left')
        merged_df['struct'] = merged_df['struct'].fillna('Empty')
        
        # 전체 데이터 병합
        complete_df = pd.merge(area_map_df, merged_df, on=['x', 'y'], how='inner')
        
        print(f'✅ 지도 데이터 로드 완료: {len(complete_df)}개 위치')
        return complete_df
        
    except Exception as e:
        print(f'❌ 데이터 로드 중 오류 발생: {e}')
        sys.exit(1)


def find_key_locations(complete_df):
    """집과 반달곰 커피의 위치를 찾습니다."""
    # MyHome 위치 찾기
    home_locations = complete_df[complete_df['struct'] == 'MyHome']
    if home_locations.empty:
        print('❌ 오류: MyHome 위치를 찾을 수 없습니다.')
        sys.exit(1)
    
    home_pos = (home_locations.iloc[0]['x'], home_locations.iloc[0]['y'])
    print(f'🏠 집 위치: {home_pos}')
    
    # BandalgomCoffee 위치들 찾기
    cafe_locations = complete_df[complete_df['struct'] == 'BandalgomCoffee']
    if cafe_locations.empty:
        print('❌ 오류: BandalgomCoffee 위치를 찾을 수 없습니다.')
        sys.exit(1)
    
    cafe_positions = [(row['x'], row['y']) for _, row in cafe_locations.iterrows()]
    print(f'☕ 반달곰 커피 위치들: {cafe_positions}')
    
    # 공사장 위치들 찾기 (지나갈 수 없는 곳)
    construction_sites = set()
    for _, row in complete_df.iterrows():
        if row['ConstructionSite'] == 1:
            construction_sites.add((row['x'], row['y']))
    
    print(f'🚧 공사장 위치: {len(construction_sites)}개')
    
    return home_pos, cafe_positions, construction_sites


def create_grid_map(complete_df):
    """이동 가능한 격자 지도를 생성합니다."""
    # 좌표 범위 계산
    x_min, x_max = complete_df['x'].min(), complete_df['x'].max()
    y_min, y_max = complete_df['y'].min(), complete_df['y'].max()
    
    # 모든 유효한 좌표 집합 생성
    valid_positions = set(zip(complete_df['x'], complete_df['y']))
    
    print(f'📍 격자 범위: X({x_min}~{x_max}), Y({y_min}~{y_max})')
    print(f'📍 유효한 위치: {len(valid_positions)}개')
    
    return valid_positions, (x_min, x_max, y_min, y_max)


def bfs_shortest_path(start_pos, target_positions, valid_positions, construction_sites):
    """BFS 알고리즘을 사용하여 최단 경로를 찾습니다."""
    print(f'🔍 최단 경로 탐색 시작: {start_pos} → {target_positions}')
    
    # BFS를 위한 큐와 방문 기록
    queue = deque([(start_pos, [start_pos])])
    visited = {start_pos}
    
    # 이동 방향 (상, 하, 좌, 우)
    directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]
    
    while queue:
        current_pos, path = queue.popleft()
        
        # 목표 위치 중 하나에 도달했는지 확인
        if current_pos in target_positions:
            print(f'✅ 최단 경로 발견! 길이: {len(path)} 단계')
            return path, current_pos
        
        # 인접한 위치들 탐색
        x, y = current_pos
        for dx, dy in directions:
            next_x, next_y = x + dx, y + dy
            next_pos = (next_x, next_y)
            
            # 유효성 검사
            if (next_pos in valid_positions and 
                next_pos not in visited and 
                next_pos not in construction_sites):
                
                visited.add(next_pos)
                new_path = path + [next_pos]
                queue.append((next_pos, new_path))
    
    print('❌ 경로를 찾을 수 없습니다.')
    return None, None


def save_path_to_csv(path, target_cafe, filename='home_to_cafe.csv'):
    """경로를 CSV 파일로 저장합니다."""
    try:
        # 경로 데이터를 DataFrame으로 변환
        path_data = []
        for i, (x, y) in enumerate(path):
            step_type = 'Start' if i == 0 else 'End' if i == len(path) - 1 else 'Path'
            path_data.append({
                'step': i + 1,
                'x': x,
                'y': y,
                'type': step_type
            })
        
        path_df = pd.DataFrame(path_data)
        path_df.to_csv(filename, index=False, encoding='utf-8-sig')
        
        print(f'💾 경로가 {filename} 파일로 저장되었습니다.')
        print(f'📊 총 {len(path)}단계, 목표 카페: {target_cafe}')
        
        return path_df
        
    except Exception as e:
        print(f'❌ CSV 저장 중 오류 발생: {e}')
        sys.exit(1)


def visualize_path_on_map(complete_df, path, target_cafe, construction_sites, filename='map_final.png'):
    """경로를 지도에 빨간색 선으로 표시하고 저장합니다."""
    try:
        print('🎨 최종 지도 시각화 시작...')
        
        # 좌표 범위 계산
        x_min, x_max = complete_df['x'].min(), complete_df['x'].max()
        y_min, y_max = complete_df['y'].min(), complete_df['y'].max()
        
        # figure 설정
        fig_width = max(12, (x_max - x_min + 1) * 0.8)
        fig_height = max(10, (y_max - y_min + 1) * 0.8)
        
        fig, ax = plt.subplots(figsize=(fig_width, fig_height))
        
        # 좌표계 설정 (왼쪽 상단이 (1,1))
        ax.set_xlim(x_min - 0.5, x_max + 0.5)
        ax.set_ylim(y_max + 0.5, y_min - 0.5)
        
        # 격자선 그리기
        for x in range(x_min, x_max + 1):
            ax.axvline(x=x + 0.5, color='lightgray', linestyle='-', alpha=0.7)
            ax.axvline(x=x - 0.5, color='lightgray', linestyle='-', alpha=0.7)
        
        for y in range(y_min, y_max + 1):
            ax.axhline(y=y + 0.5, color='lightgray', linestyle='-', alpha=0.7)
            ax.axhline(y=y - 0.5, color='lightgray', linestyle='-', alpha=0.7)
        
        # 구조물 그리기
        structure_counts = {'Apartment': 0, 'Building': 0, 'BandalgomCoffee': 0, 'MyHome': 0, 'ConstructionSite': 0}
        
        for _, row in complete_df.iterrows():
            x, y = row['x'], row['y']
            struct_type = row['struct']
            is_construction = row['ConstructionSite'] == 1
            
            # 공사장 우선 처리
            if is_construction:
                # 회색 사각형 (공사장)
                rect = patches.Rectangle((x - 0.4, y - 0.4), 0.8, 0.8, 
                                       linewidth=1, edgecolor='black', 
                                       facecolor='gray', alpha=0.8)
                ax.add_patch(rect)
                structure_counts['ConstructionSite'] += 1
                continue
            
            # 다른 구조물들
            if struct_type == 'Apartment':
                circle = patches.Circle((x, y), 0.3, linewidth=1, 
                                      edgecolor='black', facecolor='brown', alpha=0.8)
                ax.add_patch(circle)
                structure_counts['Apartment'] += 1
                
            elif struct_type == 'Building':
                circle = patches.Circle((x, y), 0.3, linewidth=1, 
                                      edgecolor='black', facecolor='brown', alpha=0.8)
                ax.add_patch(circle)
                structure_counts['Building'] += 1
                
            elif struct_type == 'BandalgomCoffee':
                rect = patches.Rectangle((x - 0.3, y - 0.3), 0.6, 0.6, 
                                       linewidth=1, edgecolor='black', 
                                       facecolor='green', alpha=0.8)
                ax.add_patch(rect)
                structure_counts['BandalgomCoffee'] += 1
                
            elif struct_type == 'MyHome':
                # 삼각형 (집)
                triangle_points = [(x, y - 0.35), (x - 0.3, y + 0.2), (x + 0.3, y + 0.2)]
                triangle = patches.Polygon(triangle_points, linewidth=1, 
                                         edgecolor='black', facecolor='green', alpha=0.8)
                ax.add_patch(triangle)
                structure_counts['MyHome'] += 1
        
        # 경로를 빨간색 선으로 그리기
        if path and len(path) > 1:
            path_x = [pos[0] for pos in path]
            path_y = [pos[1] for pos in path]
            
            ax.plot(path_x, path_y, color='red', linewidth=3, alpha=0.8, 
                   marker='o', markersize=4, markerfacecolor='red', 
                   markeredgecolor='darkred', label=f'Shortest Path ({len(path)} steps)')
            
            # 시작점과 끝점 강조 표시
            start_x, start_y = path[0]
            end_x, end_y = path[-1]
            
            ax.plot(start_x, start_y, 'ro', markersize=8, markerfacecolor='blue', 
                   markeredgecolor='darkblue', label='Start (MyHome)')
            ax.plot(end_x, end_y, 'ro', markersize=8, markerfacecolor='orange', 
                   markeredgecolor='darkorange', label=f'Target Cafe {target_cafe}')
        
        # 범례 및 제목 설정
        ax.legend(loc='upper right', fontsize=10)
        ax.set_xlabel('X Coordinate', fontsize=12)
        ax.set_ylabel('Y Coordinate', fontsize=12)
        ax.set_title(f'Shortest Path from MyHome to BandalgomCoffee\nPath Length: {len(path) if path else 0} steps', 
                    fontsize=16, fontweight='bold')
        
        # 축 눈금 설정
        ax.set_xticks(range(x_min, x_max + 1))
        ax.set_yticks(range(y_min, y_max + 1))
        
        # 이미지 저장
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f'🎯 최종 지도가 {filename} 파일로 저장되었습니다.')
        
        # 구조물 개수 출력
        for struct_type, count in structure_counts.items():
            korean_names = {
                'Apartment': 'Apartment',
                'Building': 'Building', 
                'BandalgomCoffee': 'BandalgomCoffee',
                'MyHome': 'MyHome',
                'ConstructionSite': 'ConstructionSite'
            }
            print(f'{korean_names[struct_type]}: {count}개', end=', ')
        print()
        
    except Exception as e:
        print(f'❌ 지도 시각화 중 오류 발생: {e}')
        sys.exit(1)


def main():
    """메인 실행 함수"""
    print('=' * 60)
    print('🚀 Stage 3: 최단 경로 찾기 시작')
    print('=' * 60)
    
    # 1. 데이터 로드
    complete_df = load_map_data()
    
    # 2. 핵심 위치 찾기
    home_pos, cafe_positions, construction_sites = find_key_locations(complete_df)
    
    # 3. 격자 지도 생성
    valid_positions, grid_bounds = create_grid_map(complete_df)
    
    # 4. 최단 경로 탐색 (BFS 알고리즘)
    path, target_cafe = bfs_shortest_path(home_pos, cafe_positions, valid_positions, construction_sites)
    
    if path is None:
        print('❌ 집에서 반달곰 커피까지의 경로를 찾을 수 없습니다.')
        sys.exit(1)
    
    # 5. 경로를 CSV 파일로 저장
    path_df = save_path_to_csv(path, target_cafe)
    
    # 6. 경로가 표시된 지도 시각화 및 저장
    visualize_path_on_map(complete_df, path, target_cafe, construction_sites)
    
    print('=' * 60)
    print('✅ Stage 3 완료!')
    print(f'📁 생성된 파일들:')
    print(f'   - home_to_cafe.csv: 최단 경로 데이터')
    print(f'   - map_final.png: 경로가 표시된 최종 지도')
    print('=' * 60)


if __name__ == '__main__':
    main()
