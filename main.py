import os, time, piexif, re
import re
from PIL import Image
from utils import (
    check_format, check_exif, png2jpg,
    get_new_name, get_time_from_exif, get_time_from_create_date,
    set_photo_time, get_time_from_name
)
# ------------------------------------------------------------------
## general variables
# ------------------------------------------------------------------
valid_formats = {
    'JPG': ('IMG', 'jpg'),
    'JPEG': ('IMG', 'jpg'),
    'PNG': ('IMG', 'jpg'),
    'DNG': ('DJI', 'DNG'),
    'ARW': ('RAW', 'ARW'),
    'MP4': ('VID', 'mp4')
}
folder = r'G:\ALBUM\temp'


# ------------------------------------------------------------------
## change name by time
# ------------------------------------------------------------------
def change_photo_name(folder):
    '''
    修改照片的文件名为拍摄日期，如果Exif中不包含拍摄日期，则不修改该张照片的名字
    e.g., {prefix}_20210424_071829.{suffix}
    '''
    count = 0
    file_num = len(os.listdir(folder))
    for photo_name in os.listdir(folder):
        print(f'{file_num - count} Working on file: {photo_name}')
        count += 1
        photo_path = os.path.join(folder, photo_name)
        file_extension, _ = check_format(photo_path, valid_formats)
        if file_extension == 'PNG': photo_path = png2jpg(photo_path)
        if file_extension in ['JPG', 'JPEG', 'PNG', 'DNG', 'ARW']:
            if check_exif(photo_path):
                photo_time = get_time_from_exif(photo_path)
            else:  # Exif中不包含拍摄日期，则不修改该张照片的名字，no_exif包含未修改的照片序列
                photo_time = False
                no_exif.append(photo_name)
                print(f'  No Exif, photo name has not been changed')
                # photo_time = get_time_from_create_date(photo_path)
                # print(f'No Exif, photo name has been changed to create date')
            if photo_time != False:
                photo_name, temp_photo_path = get_new_name(photo_path, photo_time, folder, valid_formats)
                new_photo_path = os.path.join(folder, photo_name)
                os.rename(temp_photo_path, new_photo_path)
                print(f'  Done, photo name has been changed to {photo_name}')
            else:
                no_time_in_name.append(photo_name)
                print('  No time in name, photo_time has been set FALSE, skipping this photo')
        elif file_extension in ['MP4']:
            print(f'  video not realized currently')
        else:
            print(f'  Not image/video, end process')


# ------------------------------------------------------------------
## change time by name
# ------------------------------------------------------------------
def change_photo_time(folder):
    '''
    修改该路径下的所有照片的时间
    '''
    count = 0
    file_num = len(os.listdir(folder))
    for photo_name in os.listdir(folder):
        print(f'{file_num - count} Working on file: {photo_name}')
        count += 1
        photo_path = os.path.join(folder, photo_name)
        file_extension, _ = check_format(photo_path, valid_formats)
        if file_extension == 'PNG': photo_path = png2jpg(photo_path)
        if file_extension in ['JPG', 'JPEG', 'PNG']:
            exif_load_error_status = set_photo_time(photo_name, photo_path)
            if exif_load_error_status:
                exif_load_error.append(photo_name)
        elif file_extension in ['MP4']:
            print(f'  video not realized currently')
        elif file_extension in ['DNG', 'ARW']:
            print(f'  Exist timestamp, end process')
        else:
            print(f'  Not image/video, end process')


# ------------------------------------------------------------------
## main
# ------------------------------------------------------------------
if __name__ == '__main__':
    no_exif, exif_load_error, no_time_in_name = [[] for i in range(3)]

    motion = input('Change name or time: ')
    while motion not in ['name', 'time']:
        motion = input('Please just input name or time: ')
    if motion == 'name':
        change_photo_name(folder)
    else:  # motion == 'time'
        change_photo_time(folder)
    
    # 统计不能执行的照片文件
    if no_exif: 
        print('Photos_no_exif(not change name):\n', no_exif)
    if exif_load_error: 
        print('Photos_exif_load_error(write exif info fail):\n', exif_load_error)
    if no_time_in_name: 
        print('Photos_no_time_in_name(not change time):\n', no_time_in_name)