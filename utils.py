import os, time, piexif, re
import re
from PIL import Image
from moviepy.editor import VideoFileClip
import subprocess
import json
# ------------------------------------------------------------------
## general functions
# ------------------------------------------------------------------
def check_format(photo_path, valid_formats):
    '''
    检查文件类型，返回：[文件格式, (前缀, 后缀)]
    '''
    file_extension = str.upper(os.path.splitext(photo_path)[1][1:])
    if file_extension in valid_formats:
        return file_extension, valid_formats[file_extension]
    else:
        return 'INVALID FORMAT', None

def check_exif(photo_path):
    '''
    检查文件是否有Exif，Exif中是否有拍摄时间
    '''
    try:
        exif_dict = piexif.load(photo_path)  # 读取Exif信息
        return piexif.ExifIFD.DateTimeOriginal in exif_dict['Exif']
    except:
        return False
    
def png2jpg(photo_path):
    '''
    将 PNG 格式图片转换为 JPG 格式
    '''
    print('Executing png2jpg')
    new_photo_path = os.path.splitext(photo_path)[0] + '.jpg'
    try:
        Image.open(photo_path).convert('RGB').save(new_photo_path, quality=95)
        os.remove(photo_path)
        return new_photo_path
    except Exception as e:
        print(f"Error converting PNG to JPG: {e}")
        return None

# ------------------------------------------------------------------
## change photo name by time
# ------------------------------------------------------------------
def get_new_name(photo_path, photo_time, folder, valid_formats):
    '''
    获取新文件名，如果两个文件时分秒也相同，在文件名后累加数字1 2 3...区分
    '''
    count = 1
    file_extension, (prefix, suffix) = check_format(photo_path, valid_formats)
    temp_photo_name = f'bcwyatt.{suffix}'  # 使用临时文件名，避免重复在后面加_1_1
    temp_photo_path = os.path.join(folder, temp_photo_name)
    os.rename(photo_path, temp_photo_path)

    photo_time = photo_time.replace(':', '').replace(' ', '_')
    photo_name = f'{prefix}_{photo_time}.{suffix}'
    while photo_name in os.listdir(folder): # 区分时间相同的文件名
        photo_name = f'{prefix}_{photo_time}_{count}.{suffix}'
        count += 1
    return photo_name, temp_photo_path

def get_time_from_exif(photo_path):
    '''
    从Exif中提取照片时间，返回格式为2021:04:22 07:07:07
    '''
    exif_dict = piexif.load(photo_path)
    photo_time = exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal]
    photo_time = bytes.decode(photo_time)
    return photo_time

def get_time_from_create_date(photo_path):
    '''
    从照片修改日期提取时间，返回格式为2021:04:22 07:07:07
    '''
    photo_time = time.ctime(os.path.getmtime(photo_path)) # 如果使用修改日期，则改为os.path.getmtime()
    struct_time = time.strptime(photo_time, '%a %b %d %H:%M:%S %Y')
    photo_time = time.strftime('%Y:%m:%d %H:%M:%S', struct_time)
    return photo_time

# ------------------------------------------------------------------
## change photo time by name
# ------------------------------------------------------------------
def set_photo_time(photo_name, photo_path):
    '''
    给照片设置拍摄时间，导入exif信息
    '''
    exif_load_error = False
    photo_time = get_time_from_name(photo_name)  # 格式为'2024:04:22 07:58:10'
    if photo_time != False:
        try:
            exif_dict = piexif.load(photo_path)  # 读取现有Exif信息
            # 设置Exif信息，注意DateTime在ImageIFD里面
            exif_dict['0th'][piexif.ImageIFD.DateTime] = photo_time  
            exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = photo_time
            exif_dict['Exif'][piexif.ExifIFD.DateTimeDigitized] = photo_time
            try:
                exif_bytes = piexif.dump(exif_dict)
                piexif.insert(exif_bytes, photo_path)  # 插入Exif信息
                print(f'  Done, photo time has been changed to {photo_time}')
            except:
                exif_load_error = True
                print(f'  Exif dump error')
                return exif_load_error
        except:
            exif_load_error = True
            print('  Exif load error')
            return exif_load_error
    else:
        print('  No time in name')
    
    # # 修改文件的修改日期和访问日期
    # try:
    #     mod_time = time.mktime(time.strptime(photo_time, '%Y:%m:%d %H:%M:%S'))
    #     os.utime(photo_path, (mod_time, mod_time))  # 想修改创建日期可能需要win32库
    #     print(f'  Done, photo_mod_time has been changed to {photo_time}\n')
    # except:
    #     print(f'  No time in name, cannot change photo_mod_time\n')


def get_time_from_name(photo_name):
    '''
    利用正则表达式从文件名中提取时间，再转换为Exif时间格式
    from 'IMG_20220102_030405.jpg' to '2022:01:01 03:04:05'
    '''
    pn = photo_name
    # 文件名包含年月日时分秒，无分隔符或分隔符为（-._/）四种之一，如'2022.08.08_07/58/10.jpg'
    pattern_1 = re.compile(r'\d{4}([-|.|/|_]?\d{2}){5}')
    pattern_2 = re.compile(r'\d{10}')  # 文件名包含时间戳，如'mmexport1569824283462.jpg'

    if pattern_1.search(pn):  # 满足pattern_1，文件名包含年月日时分秒
        pn = pattern_1.search(pn).group()
        pn = pn.replace('_', '').replace('-', '').replace('.', '').replace('/', '')
        photo_time = f'{pn[0:4]}:{pn[4:6]}:{pn[6:8]} {pn[8:10]}:{pn[10:12]}:{pn[12:14]}'
    elif pattern_2.search(pn):  # 满足pattern_2，文件名包含时间戳
        pn = pattern_2.search(pn).group()
        photo_time = time.strftime('%Y:%m:%d %H:%M:%S', time.localtime(int(pn)))
        print('  Got photo_time from pattern_2, '+ photo_time)
    # elif check_exif(os.path.join(folder, photo_name)):  # 文件名中没有时间，但Exif中有时间
    #     photo_time = get_time_from_exif(os.path.join(folder, photo_name))
    #     no_time_in_name.append(photo_name)
    #     print('  No time in name, photo_time has been extracted from Exif')
    else: # 文件名中没有时间信息，则跳过该张图片
        photo_time = False
    # else:  # 文件名和Exif中都没有时间信息，则设置照片时间为照片修改日期
    #     photo_time = time.strftime('%Y:%m:%d %H:%M:%S', time.localtime())
    #     photo_time = get_time_from_create_date(os.path.join(folder, photo_name))
    #     no_time_in_name.append(photo_name)
    #     print('  No time in name and Exif, photo_time has been changed to create date')
    return photo_time
