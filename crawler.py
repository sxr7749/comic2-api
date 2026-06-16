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

def get_cover_url(manga_id, cover_data):
    if cover_data and 'data' in cover_data and cover_data['data']:
        cover_id = cover_data['data']['id']
        return f'https://uploads.mangadex.org/covers/{manga_id}/{cover_id}.jpg'
    return ''

def crawl_comics(limit=50):
    print(f'开始采集漫画数据，数量: {limit}')
    
    url = f'{BASE_URL}/manga?limit={limit}&order[followedCount]=desc'
    headers = {'Accept': 'application/json'}
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f'请求失败: {e}')
        return []
    
    comics = []
    for item in data['data']:
        attributes = item['attributes']
        title = attributes['title']
        
        comic = {
            'id': item['id'],
            'title': title.get('en') or title.get('ja') or title.get('zh') or 'Unknown',
            'title_cn': title.get('zh') or title.get('en') or '',
            'cover': get_cover_url(item['id'], attributes.get('coverArt')),
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
                tag['attributes']['name'].get('en') or tag['attributes']['name'].get('ja') or ''
                for tag in attributes['tags']
                if tag.get('attributes', {}).get('name')
            ]
        
        if attributes.get('authors') and attributes['authors']:
            comic['author'] = attributes['authors'][0]['attributes']['name'].get('en') or 'Unknown'
        
        comics.append(comic)
    
    print(f'成功采集 {len(comics)} 部漫画')
    return comics

def crawl_chapters(comic_id, limit=30):
    print(f'采集漫画 {comic_id} 的章节数据')
    
    url = f'{BASE_URL}/manga/{comic_id}/feed?limit={limit}&order[chapter]=desc'
    headers = {'Accept': 'application/json'}
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f'请求失败: {e}')
        return []
    
    chapters = []
    for item in data['data']:
        attributes = item['attributes']
        
        chapter = {
            'id': item['id'],
            'comic_id': comic_id,
            'title': attributes.get('title') or f"Chapter {attributes.get('chapter', '')}",
            'chapter_number': attributes.get('chapter') or '',
            'page_count': attributes.get('pageCount', 0),
            'update_time': attributes.get('updatedAt', ''),
            'images': []
        }
        
        chapters.append(chapter)
    
    print(f'成功采集 {len(chapters)} 章节')
    return chapters

def crawl_chapter_images(chapter_id):
    print(f'采集章节 {chapter_id} 的图片数据')
    
    url = f'{BASE_URL}/at-home/server/{chapter_id}'
    headers = {'Accept': 'application/json'}
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f'请求失败: {e}')
        return []
    
    base_url = data.get('baseUrl', '')
    chapter_data = data.get('chapter', {})
    hash_val = chapter_data.get('hash', '')
    data_saver = chapter_data.get('dataSaver', [])
    
    images = []
    if base_url and hash_val and data_saver:
        images = [f'{base_url}/data-saver/{hash_val}/{img}' for img in data_saver]
    
    print(f'成功采集 {len(images)} 张图片')
    return images

def crawl_categories():
    print('采集分类数据')
    
    url = f'{BASE_URL}/manga/tag'
    headers = {'Accept': 'application/json'}
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f'请求失败: {e}')
        return []
    
    categories = []
    for item in data['data']:
        attributes = item['attributes']
        name = attributes['name']
        
        category = {
            'id': item['id'],
            'name': name.get('en') or name.get('ja') or name.get('zh') or 'Unknown',
            'icon': '📖'
        }
        categories.append(category)
    
    print(f'成功采集 {len(categories)} 个分类')
    return categories

def save_json(data, filename):
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f'已保存: {filepath}')

def main():
    ensure_dirs()
    
    print('=' * 50)
    print('开始漫画数据采集')
    print('=' * 50)
    
    categories = crawl_categories()
    save_json(categories, 'categories.json')
    
    comics = crawl_comics(50)
    save_json(comics, 'comics.json')
    
    for comic in comics[:5]:
        chapters = crawl_chapters(comic['id'], 20)
        save_json(chapters, f'chapters/{comic["id"]}.json')
        time.sleep(1)
    
    print('=' * 50)
    print('采集完成！')
    print('=' * 50)

if __name__ == '__main__':
    main()