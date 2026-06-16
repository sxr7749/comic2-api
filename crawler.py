import requests
import json
import os
import time

BASE_URL = 'https://api.mangadex.org'
OUTPUT_DIR = 'api'
IMAGE_DIR = 'images/covers'

def ensure_dirs():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(IMAGE_DIR, exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, 'chapters'), exist_ok=True)

def make_request(url, headers=None, timeout=30):
    try:
        headers = headers or {'Accept': 'application/json'}
        response = requests.get(url, headers=headers, timeout=timeout)
        if response.status_code == 200:
            return response.json()
        else:
            print(f'HTTP Error {response.status_code}: {url}')
            return None
    except requests.exceptions.RequestException as e:
        print(f'Request failed: {e}')
        return None

def get_cover_url(manga_id, cover_data):
    if cover_data and isinstance(cover_data, dict):
        data = cover_data.get('data')
        if data and isinstance(data, dict):
            cover_id = data.get('id')
            if cover_id:
                return f'https://uploads.mangadex.org/covers/{manga_id}/{cover_id}.jpg'
    return ''

def crawl_comics(limit=20):
    print(f'[INFO] 开始采集漫画数据，数量: {limit}')
    
    url = f'{BASE_URL}/manga?limit={limit}&order[followedCount]=desc'
    data = make_request(url)
    
    if not data or 'data' not in data:
        print('[ERROR] 获取漫画数据失败')
        return []
    
    comics = []
    for item in data['data']:
        try:
            attributes = item.get('attributes', {})
            title = attributes.get('title', {})
            
            comic = {
                'id': item.get('id', ''),
                'title': title.get('en') or title.get('ja') or title.get('zh') or 'Unknown',
                'title_cn': title.get('zh') or title.get('en') or '',
                'cover': get_cover_url(item.get('id', ''), attributes.get('coverArt')),
                'author': '',
                'status': attributes.get('status', 'unknown'),
                'description': '',
                'tags': [],
                'chapter_count': attributes.get('chapterCount', 0),
                'rating': attributes.get('rating', 0),
                'category': '',
                'update_time': attributes.get('updatedAt', ''),
                'source': 'mangadex'
            }
            
            if attributes.get('description'):
                desc = attributes['description']
                comic['description'] = desc.get('en') or desc.get('ja') or desc.get('zh') or ''
            
            if attributes.get('tags'):
                comic['tags'] = [
                    tag.get('attributes', {}).get('name', {}).get('en') or ''
                    for tag in attributes['tags']
                ]
            
            if attributes.get('authors') and attributes['authors']:
                author_data = attributes['authors'][0]
                comic['author'] = author_data.get('attributes', {}).get('name', {}).get('en') or 'Unknown'
            
            comics.append(comic)
        except Exception as e:
            print(f'[WARNING] 解析漫画数据失败: {e}')
            continue
    
    print(f'[INFO] 成功采集 {len(comics)} 部漫画')
    return comics

def crawl_chapters(comic_id, limit=10):
    print(f'[INFO] 采集漫画 {comic_id} 的章节数据')
    
    url = f'{BASE_URL}/manga/{comic_id}/feed?limit={limit}&order[chapter]=desc'
    data = make_request(url)
    
    if not data or 'data' not in data:
        print(f'[ERROR] 获取章节数据失败: {comic_id}')
        return []
    
    chapters = []
    for item in data['data']:
        try:
            attributes = item.get('attributes', {})
            chapter = {
                'id': item.get('id', ''),
                'comic_id': comic_id,
                'title': attributes.get('title') or f"Chapter {attributes.get('chapter', '')}",
                'chapter_number': attributes.get('chapter') or '',
                'page_count': attributes.get('pageCount', 0),
                'update_time': attributes.get('updatedAt', ''),
                'images': []
            }
            chapters.append(chapter)
        except Exception as e:
            print(f'[WARNING] 解析章节数据失败: {e}')
            continue
    
    print(f'[INFO] 成功采集 {len(chapters)} 章节')
    return chapters

def crawl_categories():
    print('[INFO] 采集分类数据')
    
    url = f'{BASE_URL}/manga/tag'
    data = make_request(url)
    
    if not data or 'data' not in data:
        print('[ERROR] 获取分类数据失败')
        return []
    
    categories = []
    for item in data['data']:
        try:
            attributes = item.get('attributes', {})
            name = attributes.get('name', {})
            category = {
                'id': item.get('id', ''),
                'name': name.get('en') or name.get('ja') or name.get('zh') or 'Unknown',
                'icon': '📖'
            }
            categories.append(category)
        except Exception as e:
            print(f'[WARNING] 解析分类数据失败: {e}')
            continue
    
    print(f'[INFO] 成功采集 {len(categories)} 个分类')
    return categories

def save_json(data, filename):
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f'[INFO] 已保存: {filepath}')
    return filepath

def main():
    print('=' * 60)
    print('🚀 漫画数据采集脚本启动')
    print('=' * 60)
    
    ensure_dirs()
    
    categories = crawl_categories()
    if categories:
        save_json(categories, 'categories.json')
    else:
        print('[ERROR] 分类采集失败，使用默认数据')
        save_json([], 'categories.json')
    
    comics = crawl_comics(20)
    if comics:
        save_json(comics, 'comics.json')
    else:
        print('[ERROR] 漫画采集失败，使用默认数据')
        save_json([], 'comics.json')
    
    if comics:
        for comic in comics[:3]:
            chapters = crawl_chapters(comic['id'], 10)
            if chapters:
                save_json(chapters, f'chapters/{comic["id"]}.json')
            time.sleep(0.5)
    
    print('=' * 60)
    print('✅ 采集完成')
    print('=' * 60)
    
    output_files = []
    for root, dirs, files in os.walk(OUTPUT_DIR):
        for file in files:
            output_files.append(os.path.join(root, file))
    
    print(f'生成的文件: {output_files}')
    
    if not output_files:
        print('[ERROR] 未生成任何文件')
        exit(1)

if __name__ == '__main__':
    main()
