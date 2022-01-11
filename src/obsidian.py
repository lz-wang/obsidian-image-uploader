import os
import re

from pkg.utils.file_tools import get_encoding


def find_ob_imgs(ob_file_path: str):
    if not os.path.exists(ob_file_path):
        return []

    with open(ob_file_path, 'r', encoding=get_encoding(ob_file_path)) as ob:
        lines = ob.readlines()

    ob_imgs = []
    ob_img_p = re.compile(r'!\[\[(.*)]]')
    for line in lines:
        ob_imgs.extend(re.findall(ob_img_p, line))
    return list(set(ob_imgs))


def update_ob_file(ob_file_path: str, img_url_map: dict, suffix: str):
    if not os.path.exists(ob_file_path):
        return False, f'Obsidian文件 {ob_file_path} 不存在'

    new_ob_file_path = ob_file_path.replace('.md', f'{suffix}.md')
    tmp_ob_file_path = ob_file_path.replace('.md', f'.md.tmp')
    with open(tmp_ob_file_path, 'w', encoding='utf-8') as new_ob:
        with open(ob_file_path, 'r', encoding=get_encoding(ob_file_path)) as ob:
            ob_lines = ob.readlines()

        new_ob_lines = []
        ob_img_p = re.compile(r'!\[\[(.*)]]')
        for line in ob_lines:
            line_imgs = re.findall(ob_img_p, line)
            if line_imgs:
                for img in line_imgs:
                    _img_url = img_url_map.get(img)
                    old = f'![[{img}]]'
                    new = f'![{img}]({_img_url})'
                    line = line.replace(old, new)
            new_ob_lines.append(line)
        new_ob.writelines(new_ob_lines)
    if suffix:
        os.rename(tmp_ob_file_path, new_ob_file_path)
    else:
        os.remove(ob_file_path)
        os.rename(tmp_ob_file_path, ob_file_path)
        new_ob_file_path = ob_file_path
    return True, new_ob_file_path
